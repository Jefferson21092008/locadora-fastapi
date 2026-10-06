from datetime import date, timedelta

from sqlalchemy import (
    String,
    case,
    cast,
    func,
    or_,
    select,
)

from modulos.concorrencia import (
    buscar_por_id_para_atualizacao,
)
from modulos.consultas import (
    ResultadoPaginado,
)
from modulos.outbox import persistir_eventos_outbox
from modulos.excecoes import ConflitoConcorrencia
from modulos.manutencoes import (
    Manutencao,
)
from modulos.models.manutencao_model import (
    ManutencaoModel,
)
from modulos.models.reserva_model import ReservaModel
from modulos.models.veiculo_model import (
    VeiculoModel,
)


class ManutencaoRepository:
    """Acesso às manutenções usando exclusivamente SQLAlchemy."""

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
    def _para_entidade(
        model,
    ):
        if model is None:
            return None

        return Manutencao.from_dict(
            {
                "id": model.id,
                "veiculo_id": model.veiculo_id,
                "motivo": model.motivo,
                "quilometragem": model.quilometragem,
                "custo": model.custo,
                "data_inicio": model.data_inicio,
                "data_fim": model.data_fim,
                "status": model.status,
                "tipo": model.tipo,
                "prioridade": model.prioridade,
                "fornecedor": model.fornecedor,
                "custo_estimado": model.custo_estimado,
                "data_prevista": model.data_prevista,
                "observacoes": model.observacoes,
            }
        )

    @classmethod
    def _para_entidades(
        cls,
        models,
    ):
        return [
            cls._para_entidade(
                model
            )
            for model in models
        ]

    @staticmethod
    def _buscar_reserva_conflitante(
        sessao,
        veiculo_id,
        data_prevista,
    ):
        hoje = date.today()

        primeira = sessao.scalar(
            select(ReservaModel)
            .where(
                ReservaModel.veiculo_id == veiculo_id,
                ReservaModel.status == "ativa",
                ReservaModel.data_fim > hoje.isoformat(),
            )
            .order_by(
                ReservaModel.data_inicio,
                ReservaModel.id,
            )
        )

        if primeira is None:
            return None

        if not data_prevista:
            return primeira

        fim_manutencao = (
            date.fromisoformat(data_prevista)
            + timedelta(days=1)
        ).isoformat()

        return sessao.scalar(
            select(ReservaModel)
            .where(
                ReservaModel.veiculo_id == veiculo_id,
                ReservaModel.status == "ativa",
                ReservaModel.data_inicio < fim_manutencao,
                ReservaModel.data_fim > hoje.isoformat(),
            )
            .order_by(
                ReservaModel.data_inicio,
                ReservaModel.id,
            )
        )

    def buscar_por_id(
        self,
        id_manutencao,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            model = sessao.get(
                ManutencaoModel,
                id_manutencao,
            )

            return self._para_entidade(
                model
            )

    def buscar_ativa_por_veiculo(
        self,
        id_veiculo,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    ManutencaoModel
                )
                .where(
                    ManutencaoModel.veiculo_id
                    == id_veiculo,
                    ManutencaoModel.status
                    == "ativa",
                )
                .order_by(
                    ManutencaoModel.id
                )
            )

            model = sessao.scalar(
                comando
            )

            return self._para_entidade(
                model
            )

    def listar_por_veiculo(
        self,
        id_veiculo,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    ManutencaoModel
                )
                .where(
                    ManutencaoModel.veiculo_id
                    == id_veiculo
                )
                .order_by(
                    ManutencaoModel.id
                )
            )

            models = (
                sessao.scalars(
                    comando
                )
                .all()
            )

            return self._para_entidades(
                models
            )

    def listar_ativas(self):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    ManutencaoModel
                )
                .where(
                    ManutencaoModel.status
                    == "ativa"
                )
                .order_by(
                    ManutencaoModel.id
                )
            )

            models = (
                sessao.scalars(
                    comando
                )
                .all()
            )

            return self._para_entidades(
                models
            )

    def listar_colecao(self):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    ManutencaoModel
                )
                .order_by(
                    ManutencaoModel.id
                )
            )

            models = (
                sessao.scalars(
                    comando
                )
                .all()
            )

            return self._para_entidades(
                models
            )

    def consultar(
        self,
        pagina=1,
        por_pagina=12,
        busca="",
        status="todos",
        tipo="todos",
        prioridade="todos",
        ordenar="id",
        direcao="desc",
    ):
        filtros = []
        termo = str(
            busca or ""
        ).strip().lower()

        if termo:
            filtros.append(
                or_(
                    func.lower(
                        ManutencaoModel.motivo
                    ).contains(
                        termo
                    ),
                    func.lower(
                        func.coalesce(
                            ManutencaoModel.fornecedor,
                            "",
                        )
                    ).contains(
                        termo
                    ),
                    func.lower(
                        func.coalesce(
                            ManutencaoModel.observacoes,
                            "",
                        )
                    ).contains(
                        termo
                    ),
                    func.lower(
                        VeiculoModel.modelo
                    ).contains(
                        termo
                    ),
                    func.lower(
                        VeiculoModel.tipo
                    ).contains(
                        termo
                    ),
                    cast(
                        ManutencaoModel.id,
                        String,
                    ).contains(
                        termo
                    ),
                    cast(
                        ManutencaoModel.veiculo_id,
                        String,
                    ).contains(
                        termo
                    ),
                    cast(
                        VeiculoModel.ano,
                        String,
                    ).contains(
                        termo
                    ),
                )
            )

        if status != "todos":
            filtros.append(
                ManutencaoModel.status
                == status
            )

        if tipo != "todos":
            filtros.append(
                ManutencaoModel.tipo
                == tipo
            )

        if prioridade != "todos":
            filtros.append(
                ManutencaoModel.prioridade
                == prioridade
            )

        colunas_ordenacao = {
            "id": ManutencaoModel.id,
            "data_inicio": (
                ManutencaoModel.data_inicio
            ),
            "data_prevista": (
                ManutencaoModel.data_prevista
            ),
            "custo": ManutencaoModel.custo,
            "custo_estimado": (
                ManutencaoModel.custo_estimado
            ),
            "quilometragem": (
                ManutencaoModel.quilometragem
            ),
        }
        coluna = colunas_ordenacao.get(
            ordenar,
            ManutencaoModel.id,
        )
        ordem = (
            coluna.desc()
            if direcao == "desc"
            else coluna.asc()
        )
        deslocamento = (
            pagina - 1
        ) * por_pagina
        hoje = date.today().isoformat()

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            base = (
                select(
                    ManutencaoModel
                )
                .join(
                    VeiculoModel,
                    VeiculoModel.id
                    == ManutencaoModel.veiculo_id,
                )
                .where(
                    *filtros
                )
            )

            total = sessao.scalar(
                select(
                    func.count(
                        ManutencaoModel.id
                    )
                )
                .join(
                    VeiculoModel,
                    VeiculoModel.id
                    == ManutencaoModel.veiculo_id,
                )
                .where(
                    *filtros
                )
            ) or 0

            comando = (
                base
                .order_by(
                    ordem,
                    ManutencaoModel.id.desc(),
                )
                .offset(
                    deslocamento
                )
                .limit(
                    por_pagina
                )
            )

            models = (
                sessao.scalars(
                    comando
                )
                .all()
            )

            resumo = (
                sessao.execute(
                    select(
                        func.count(
                            ManutencaoModel.id
                        ),
                        func.sum(
                            case(
                                (
                                    ManutencaoModel.status
                                    == "ativa",
                                    1,
                                ),
                                else_=0,
                            )
                        ),
                        func.sum(
                            case(
                                (
                                    ManutencaoModel.status
                                    == "finalizada",
                                    1,
                                ),
                                else_=0,
                            )
                        ),
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
                        func.sum(
                            case(
                                (
                                    (
                                        ManutencaoModel.status
                                        == "ativa"
                                    )
                                    & (
                                        ManutencaoModel.data_prevista
                                        .is_not(
                                            None
                                        )
                                    )
                                    & (
                                        ManutencaoModel.data_prevista
                                        < hoje
                                    ),
                                    1,
                                ),
                                else_=0,
                            )
                        ),
                        func.sum(
                            case(
                                (
                                    ManutencaoModel.status
                                    == "ativa",
                                    ManutencaoModel.custo_estimado,
                                ),
                                else_=0.0,
                            )
                        ),
                    )
                )
                .one()
            )

        return ResultadoPaginado(
            items=self._para_entidades(
                models
            ),
            total=int(
                total
            ),
            resumo={
                "total": int(
                    resumo[0] or 0
                ),
                "ativas": int(
                    resumo[1] or 0
                ),
                "finalizadas": int(
                    resumo[2] or 0
                ),
                "custo_finalizado": float(
                    resumo[3] or 0.0
                ),
                "atrasadas": int(
                    resumo[4] or 0
                ),
                "custo_estimado_ativo": float(
                    resumo[5] or 0.0
                ),
            },
        )

    def registrar(
        self,
        manutencao,
        veiculo,
    ):
        dados_manutencao = (
            manutencao.to_dict()
        )
        dados_veiculo = (
            veiculo.to_dict()
        )

        model_manutencao = (
            ManutencaoModel(
                veiculo_id=dados_manutencao[
                    "veiculo_id"
                ],
                motivo=dados_manutencao[
                    "motivo"
                ],
                quilometragem=dados_manutencao[
                    "quilometragem"
                ],
                custo=dados_manutencao[
                    "custo"
                ],
                data_inicio=dados_manutencao[
                    "data_inicio"
                ],
                data_fim=dados_manutencao.get(
                    "data_fim"
                ),
                status=dados_manutencao[
                    "status"
                ],
                tipo=dados_manutencao[
                    "tipo"
                ],
                prioridade=dados_manutencao[
                    "prioridade"
                ],
                fornecedor=dados_manutencao.get(
                    "fornecedor"
                ),
                custo_estimado=(
                    dados_manutencao[
                        "custo_estimado"
                    ]
                ),
                data_prevista=(
                    dados_manutencao.get(
                        "data_prevista"
                    )
                ),
                observacoes=(
                    dados_manutencao.get(
                        "observacoes"
                    )
                ),
            )
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                model_veiculo = buscar_por_id_para_atualizacao(
                    sessao,
                    VeiculoModel,
                    dados_veiculo["id"],
                )

                if model_veiculo is None:
                    raise RuntimeError(
                        "Veículo não encontrado durante a manutenção."
                    )

                if model_veiculo.status != "disponivel":
                    raise ConflitoConcorrencia(
                        "O estado do veículo mudou enquanto a manutenção "
                        "era aberta. Atualize a tela e tente novamente."
                    )

                conflito_reserva = self._buscar_reserva_conflitante(
                    sessao,
                    dados_veiculo["id"],
                    dados_manutencao.get("data_prevista"),
                )
                if conflito_reserva is not None:
                    if not dados_manutencao.get("data_prevista"):
                        raise ConflitoConcorrencia(
                            "Uma reserva futura foi criada. Informe uma "
                            "previsão de conclusão antes de abrir a manutenção."
                        )
                    raise ConflitoConcorrencia(
                        "Uma reserva futura passou a conflitar com a "
                        "manutenção enquanto a operação era processada."
                    )

                sessao.add(model_manutencao)
                model_veiculo.status = dados_veiculo["status"]
                model_veiculo.disponivel = dados_veiculo["disponivel"]
                model_veiculo.alugado_por = dados_veiculo.get("alugado_por")
                model_veiculo.ativo = dados_veiculo["ativo"]

                sessao.flush()
                novo_id = model_manutencao.id
                persistir_eventos_outbox(
                    sessao,
                    {"manutencao_id": novo_id},
                )
                sessao.commit()
                return novo_id
            except Exception:
                sessao.rollback()
                raise

    def atualizar(
        self,
        manutencao,
    ):
        dados = manutencao.to_dict()

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            try:
                existente = sessao.get(ManutencaoModel, dados["id"])
                if existente is None:
                    raise RuntimeError("Manutenção não encontrada.")

                model_veiculo = buscar_por_id_para_atualizacao(
                    sessao,
                    VeiculoModel,
                    existente.veiculo_id,
                )
                if model_veiculo is None:
                    raise RuntimeError("Veículo não encontrado.")

                model = buscar_por_id_para_atualizacao(
                    sessao,
                    ManutencaoModel,
                    dados["id"],
                )
                if model is None:
                    raise RuntimeError("Manutenção não encontrada.")
                if model.status != "ativa":
                    raise ConflitoConcorrencia(
                        "A manutenção foi finalizada por outra operação."
                    )

                conflito_reserva = self._buscar_reserva_conflitante(
                    sessao,
                    model.veiculo_id,
                    dados.get("data_prevista"),
                )
                if conflito_reserva is not None:
                    if not dados.get("data_prevista"):
                        raise ConflitoConcorrencia(
                            "Há reserva futura ativa; mantenha uma previsão "
                            "de conclusão para a manutenção."
                        )
                    raise ConflitoConcorrencia(
                        "Uma reserva futura passou a conflitar com a "
                        "nova previsão da manutenção."
                    )

                model.motivo = dados["motivo"]
                model.tipo = dados["tipo"]
                model.prioridade = dados["prioridade"]
                model.fornecedor = dados.get("fornecedor")
                model.custo_estimado = dados["custo_estimado"]
                model.data_prevista = dados.get("data_prevista")
                model.observacoes = dados.get("observacoes")
                persistir_eventos_outbox(sessao)
                sessao.commit()
            except Exception:
                sessao.rollback()
                raise
        return None

    def registrar_finalizacao(
        self,
        manutencao,
        veiculo,
    ):
        dados_manutencao = manutencao.to_dict()
        dados_veiculo = veiculo.to_dict()

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            try:
                model_veiculo = buscar_por_id_para_atualizacao(
                    sessao,
                    VeiculoModel,
                    dados_veiculo["id"],
                )
                if model_veiculo is None:
                    raise RuntimeError(
                        "Veículo em manutenção não encontrado."
                    )

                model_manutencao = buscar_por_id_para_atualizacao(
                    sessao,
                    ManutencaoModel,
                    dados_manutencao["id"],
                )
                if model_manutencao is None:
                    raise RuntimeError(
                        "Manutenção ativa não encontrada."
                    )

                if model_manutencao.status != "ativa":
                    raise ConflitoConcorrencia(
                        "A manutenção já foi finalizada por outra operação."
                    )
                if model_veiculo.status != "manutencao":
                    raise ConflitoConcorrencia(
                        "O estado do veículo mudou antes da finalização "
                        "da manutenção."
                    )

                model_manutencao.custo = dados_manutencao["custo"]
                model_manutencao.data_fim = dados_manutencao.get("data_fim")
                model_manutencao.status = dados_manutencao["status"]

                model_veiculo.status = dados_veiculo["status"]
                model_veiculo.disponivel = dados_veiculo["disponivel"]
                model_veiculo.alugado_por = dados_veiculo.get("alugado_por")
                model_veiculo.ativo = dados_veiculo["ativo"]
                persistir_eventos_outbox(sessao)
                sessao.commit()
            except Exception:
                sessao.rollback()
                raise
        return None
