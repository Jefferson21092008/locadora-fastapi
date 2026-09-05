from sqlalchemy import (
    case,
    func,
    or_,
    select,
)

from modulos.models.aluguel_model import (
    AluguelModel,
)
from modulos.models.manutencao_model import (
    ManutencaoModel,
)
from modulos.models.veiculo_model import (
    VeiculoModel,
)


class RelatorioRepository:
    """Consultas de relatórios executadas exclusivamente com SQLAlchemy."""

    def __init__(
        self,
        banco_sqlalchemy,
    ):
        if banco_sqlalchemy is None:
            raise ValueError(
                "BancoSQLAlchemy é obrigatório."
            )

        self.banco_sqlalchemy = (
            banco_sqlalchemy
        )

    @staticmethod
    def _para_lista_dict(
        resultado,
    ):
        return [
            dict(linha)
            for linha in resultado
        ]

    # ================================================================
    # VEÍCULOS MAIS ALUGADOS
    # ================================================================

    def veiculos_mais_alugados(
        self,
        limite=10,
    ):
        total_alugueis = func.count(
            AluguelModel.id
        )

        comando = (
            select(
                VeiculoModel.id.label("id"),
                VeiculoModel.tipo.label("tipo"),
                VeiculoModel.modelo.label("modelo"),
                total_alugueis.label(
                    "total_alugueis"
                ),
            )
            .outerjoin(
                AluguelModel,
                AluguelModel.veiculo_id
                == VeiculoModel.id,
            )
            .group_by(
                VeiculoModel.id,
                VeiculoModel.tipo,
                VeiculoModel.modelo,
            )
            .having(total_alugueis > 0)
            .order_by(
                total_alugueis.desc(),
                VeiculoModel.id.asc(),
            )
            .limit(limite)
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            resultado = (
                sessao.execute(comando)
                .mappings()
                .all()
            )

        return self._para_lista_dict(
            resultado
        )

    # ================================================================
    # FATURAMENTO POR TIPO
    # ================================================================

    def faturamento_por_tipo(self):
        faturamento = func.coalesce(
            func.sum(
                AluguelModel.valor
            ),
            0.0,
        )

        comando = (
            select(
                AluguelModel.veiculo_tipo.label(
                    "tipo"
                ),
                func.count(
                    AluguelModel.id
                ).label("total_alugueis"),
                faturamento.label(
                    "faturamento"
                ),
            )
            .where(
                AluguelModel.status
                == "finalizado"
            )
            .group_by(
                AluguelModel.veiculo_tipo
            )
            .order_by(
                faturamento.desc(),
                AluguelModel.veiculo_tipo.asc(),
            )
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            resultado = (
                sessao.execute(comando)
                .mappings()
                .all()
            )

        return self._para_lista_dict(
            resultado
        )

    # ================================================================
    # CUSTOS DE MANUTENÇÃO
    # ================================================================

    def custos_manutencao(self):
        custo_total = func.coalesce(
            func.sum(
                case(
                    (
                        ManutencaoModel.status
                        == "finalizada",
                        ManutencaoModel.custo,
                    ),
                    else_=0.0,
                )
            ),
            0.0,
        )

        total_manutencoes = func.count(
            ManutencaoModel.id
        )

        comando = (
            select(
                VeiculoModel.id.label("id"),
                VeiculoModel.tipo.label("tipo"),
                VeiculoModel.modelo.label("modelo"),
                total_manutencoes.label(
                    "total_manutencoes"
                ),
                custo_total.label(
                    "custo_total"
                ),
            )
            .join(
                ManutencaoModel,
                ManutencaoModel.veiculo_id
                == VeiculoModel.id,
            )
            .group_by(
                VeiculoModel.id,
                VeiculoModel.tipo,
                VeiculoModel.modelo,
            )
            .order_by(
                custo_total.desc(),
                total_manutencoes.desc(),
                VeiculoModel.id.asc(),
            )
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            resultado = (
                sessao.execute(comando)
                .mappings()
                .all()
            )

        return self._para_lista_dict(
            resultado
        )

    # ================================================================
    # CLIENTES QUE MAIS ALUGAM
    # ================================================================

    def clientes_mais_alugam(
        self,
        limite=10,
    ):
        total_alugueis = func.count(
            AluguelModel.id
        )

        total_gasto = func.coalesce(
            func.sum(
                case(
                    (
                        AluguelModel.status
                        == "finalizado",
                        AluguelModel.valor,
                    ),
                    else_=0.0,
                )
            ),
            0.0,
        )

        comando = (
            select(
                AluguelModel.cliente_id.label(
                    "cliente_id"
                ),
                AluguelModel.cliente_nome.label(
                    "cliente_nome"
                ),
                AluguelModel.cliente_usuario.label(
                    "cliente_usuario"
                ),
                total_alugueis.label(
                    "total_alugueis"
                ),
                total_gasto.label(
                    "total_gasto"
                ),
            )
            .group_by(
                AluguelModel.cliente_id,
                AluguelModel.cliente_nome,
                AluguelModel.cliente_usuario,
            )
            .order_by(
                total_alugueis.desc(),
                total_gasto.desc(),
                AluguelModel.cliente_id.asc(),
            )
            .limit(limite)
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            resultado = (
                sessao.execute(comando)
                .mappings()
                .all()
            )

        return self._para_lista_dict(
            resultado
        )

    # ================================================================
    # RESUMO FINANCEIRO
    # ================================================================

    def resumo_financeiro(self):
        receita_alugueis = (
            select(
                func.coalesce(
                    func.sum(
                        AluguelModel.valor
                    ),
                    0.0,
                )
            )
            .where(
                AluguelModel.status
                == "finalizado"
            )
            .scalar_subquery()
        )

        custos_manutencao = (
            select(
                func.coalesce(
                    func.sum(
                        ManutencaoModel.custo
                    ),
                    0.0,
                )
            )
            .where(
                ManutencaoModel.status
                == "finalizada"
            )
            .scalar_subquery()
        )

        comando = select(
            receita_alugueis.label(
                "receita_alugueis"
            ),
            custos_manutencao.label(
                "custos_manutencao"
            ),
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            linha = (
                sessao.execute(comando)
                .mappings()
                .one()
            )

        resultado = dict(linha)
        resultado["resultado_bruto"] = (
            resultado["receita_alugueis"]
            - resultado["custos_manutencao"]
        )

        return resultado

    # ================================================================
    # RESULTADO POR VEÍCULO
    # ================================================================

    def resultado_por_veiculo(self):
        receitas = (
            select(
                AluguelModel.veiculo_id.label(
                    "veiculo_id"
                ),
                func.count(
                    AluguelModel.id
                ).label("total_alugueis"),
                func.coalesce(
                    func.sum(
                        AluguelModel.valor
                    ),
                    0.0,
                ).label("receita"),
            )
            .where(
                AluguelModel.status
                == "finalizado"
            )
            .group_by(
                AluguelModel.veiculo_id
            )
            .subquery("receitas")
        )

        custos = (
            select(
                ManutencaoModel.veiculo_id.label(
                    "veiculo_id"
                ),
                func.count(
                    ManutencaoModel.id
                ).label("total_manutencoes"),
                func.coalesce(
                    func.sum(
                        ManutencaoModel.custo
                    ),
                    0.0,
                ).label("custo_manutencao"),
            )
            .where(
                ManutencaoModel.status
                == "finalizada"
            )
            .group_by(
                ManutencaoModel.veiculo_id
            )
            .subquery("custos")
        )

        total_alugueis = func.coalesce(
            receitas.c.total_alugueis,
            0,
        )
        receita = func.coalesce(
            receitas.c.receita,
            0.0,
        )
        total_manutencoes = func.coalesce(
            custos.c.total_manutencoes,
            0,
        )
        custo_manutencao = func.coalesce(
            custos.c.custo_manutencao,
            0.0,
        )
        resultado_bruto = (
            receita
            - custo_manutencao
        )

        comando = (
            select(
                VeiculoModel.id.label("id"),
                VeiculoModel.tipo.label("tipo"),
                VeiculoModel.modelo.label("modelo"),
                total_alugueis.label(
                    "total_alugueis"
                ),
                receita.label("receita"),
                total_manutencoes.label(
                    "total_manutencoes"
                ),
                custo_manutencao.label(
                    "custo_manutencao"
                ),
                resultado_bruto.label(
                    "resultado_bruto"
                ),
            )
            .outerjoin(
                receitas,
                receitas.c.veiculo_id
                == VeiculoModel.id,
            )
            .outerjoin(
                custos,
                custos.c.veiculo_id
                == VeiculoModel.id,
            )
            .where(
                or_(
                    total_alugueis > 0,
                    total_manutencoes > 0,
                )
            )
            .order_by(
                resultado_bruto.desc(),
                VeiculoModel.id.asc(),
            )
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            resultado = (
                sessao.execute(comando)
                .mappings()
                .all()
            )

        return self._para_lista_dict(
            resultado
        )
