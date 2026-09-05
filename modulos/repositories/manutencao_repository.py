from sqlalchemy import (
    select,
)

from modulos.manutencoes import (
    Manutencao,
)
from modulos.models.manutencao_model import (
    ManutencaoModel,
)
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

    # ================================================================
    # MAPEAMENTO MODEL -> ENTIDADE
    # ================================================================

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

    # ================================================================
    # CONSULTAS
    # ================================================================

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

    # ================================================================
    # ABERTURA
    # ================================================================

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

        model_manutencao = ManutencaoModel(
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
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                model_veiculo = sessao.get(
                    VeiculoModel,
                    dados_veiculo["id"],
                )

                if model_veiculo is None:
                    raise RuntimeError(
                        "Veículo não encontrado "
                        "durante a manutenção."
                    )

                if (
                    model_veiculo.status
                    != "disponivel"
                ):
                    raise RuntimeError(
                        "Não foi possível alterar "
                        "o veículo para manutenção."
                    )

                sessao.add(
                    model_manutencao
                )

                model_veiculo.status = (
                    dados_veiculo[
                        "status"
                    ]
                )
                model_veiculo.disponivel = (
                    dados_veiculo[
                        "disponivel"
                    ]
                )
                model_veiculo.alugado_por = (
                    dados_veiculo.get(
                        "alugado_por"
                    )
                )
                model_veiculo.ativo = (
                    dados_veiculo[
                        "ativo"
                    ]
                )

                # A manutenção e a alteração do veículo
                # pertencem à mesma transação.
                sessao.flush()

                novo_id = (
                    model_manutencao.id
                )

                sessao.commit()

                return novo_id

            except Exception:
                sessao.rollback()
                raise

    # ================================================================
    # FINALIZAÇÃO
    # ================================================================

    def registrar_finalizacao(
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

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                model_manutencao = sessao.get(
                    ManutencaoModel,
                    dados_manutencao["id"],
                )

                if (
                    model_manutencao is None
                    or model_manutencao.status
                    != "ativa"
                ):
                    raise RuntimeError(
                        "Manutenção ativa "
                        "não encontrada."
                    )

                model_veiculo = sessao.get(
                    VeiculoModel,
                    dados_veiculo["id"],
                )

                if (
                    model_veiculo is None
                    or model_veiculo.status
                    != "manutencao"
                ):
                    raise RuntimeError(
                        "Veículo em manutenção "
                        "não encontrado."
                    )

                model_manutencao.custo = (
                    dados_manutencao[
                        "custo"
                    ]
                )
                model_manutencao.data_fim = (
                    dados_manutencao.get(
                        "data_fim"
                    )
                )
                model_manutencao.status = (
                    dados_manutencao[
                        "status"
                    ]
                )

                model_veiculo.status = (
                    dados_veiculo[
                        "status"
                    ]
                )
                model_veiculo.disponivel = (
                    dados_veiculo[
                        "disponivel"
                    ]
                )
                model_veiculo.alugado_por = (
                    dados_veiculo.get(
                        "alugado_por"
                    )
                )
                model_veiculo.ativo = (
                    dados_veiculo[
                        "ativo"
                    ]
                )

                # Finalização e liberação do veículo
                # acontecem em uma única transação.
                sessao.commit()

            except Exception:
                sessao.rollback()
                raise

        return None
