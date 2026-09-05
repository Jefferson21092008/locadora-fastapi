from sqlalchemy import (
    or_,
    select,
)

from modulos.alugueis import (
    Aluguel,
)
from modulos.models.aluguel_model import (
    AluguelModel,
)
from modulos.models.veiculo_model import (
    VeiculoModel,
)


class AluguelRepository:
    """Acesso aos aluguéis usando exclusivamente SQLAlchemy."""

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

        return Aluguel.from_dict(
            {
                "id": model.id,
                "cliente_id": model.cliente_id,
                "cliente_usuario": model.cliente_usuario,
                "cliente_nome": model.cliente_nome,
                "veiculo_id": model.veiculo_id,
                "veiculo_tipo": model.veiculo_tipo,
                "veiculo_modelo": model.veiculo_modelo,
                "dias": model.dias,
                "status": model.status,
                "km": model.km,
                "pagamento": model.pagamento,
                "valor": model.valor,
                "data_inicio": model.data_inicio,
                "data_prevista": model.data_prevista,
                "data_fim": model.data_fim,
                "dias_atraso": model.dias_atraso,
                "multa": model.multa,
            },
            id_padrao=model.id,
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
    # FILTRO DE CLIENTE
    # ================================================================

    @staticmethod
    def _filtro_cliente(
        cliente,
    ):
        return or_(
            AluguelModel.cliente_id
            == cliente.id,
            AluguelModel.cliente_usuario
            == cliente.usuario,
        )

    # ================================================================
    # CONSULTAS
    # ================================================================

    def listar_ativos_cliente(
        self,
        cliente,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    AluguelModel
                )
                .where(
                    AluguelModel.status
                    == "ativo",
                    self._filtro_cliente(
                        cliente
                    ),
                )
                .order_by(
                    AluguelModel.id
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

    def listar_do_cliente(
        self,
        cliente,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    AluguelModel
                )
                .where(
                    self._filtro_cliente(
                        cliente
                    )
                )
                .order_by(
                    AluguelModel.id
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

    def buscar_ativo(
        self,
        cliente,
        id_veiculo=None,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    AluguelModel
                )
                .where(
                    AluguelModel.status
                    == "ativo",
                    self._filtro_cliente(
                        cliente
                    ),
                )
                .order_by(
                    AluguelModel.id
                )
            )

            if id_veiculo is not None:
                comando = comando.where(
                    AluguelModel.veiculo_id
                    == id_veiculo
                )

            model = sessao.scalar(
                comando
            )

            return self._para_entidade(
                model
            )

    # ================================================================
    # NOVO ALUGUEL
    # ================================================================

    def registrar(
        self,
        aluguel,
        veiculo,
    ):
        dados_aluguel = (
            aluguel.to_dict()
        )
        dados_veiculo = (
            veiculo.to_dict()
        )

        model_aluguel = AluguelModel(
            cliente_id=dados_aluguel[
                "cliente_id"
            ],
            veiculo_id=dados_aluguel[
                "veiculo_id"
            ],
            cliente_usuario=dados_aluguel[
                "cliente_usuario"
            ],
            cliente_nome=dados_aluguel[
                "cliente_nome"
            ],
            veiculo_tipo=dados_aluguel[
                "veiculo_tipo"
            ],
            veiculo_modelo=dados_aluguel[
                "veiculo_modelo"
            ],
            dias=dados_aluguel[
                "dias"
            ],
            status=dados_aluguel[
                "status"
            ],
            km=dados_aluguel.get(
                "km",
                0,
            ),
            pagamento=dados_aluguel.get(
                "pagamento"
            ),
            valor=dados_aluguel.get(
                "valor",
                0,
            ),
            data_inicio=dados_aluguel[
                "data_inicio"
            ],
            data_prevista=dados_aluguel[
                "data_prevista"
            ],
            data_fim=dados_aluguel.get(
                "data_fim"
            ),
            dias_atraso=dados_aluguel.get(
                "dias_atraso",
                0,
            ),
            multa=dados_aluguel.get(
                "multa",
                0,
            ),
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
                        "durante o aluguel."
                    )

                sessao.add(
                    model_aluguel
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

                # Aluguel e alteração do veículo são
                # confirmados na mesma transação.
                sessao.commit()
                sessao.refresh(
                    model_aluguel
                )

                return model_aluguel.id

            except Exception:
                sessao.rollback()
                raise

    # ================================================================
    # DEVOLUÇÃO
    # ================================================================

    def registrar_devolucao(
        self,
        aluguel,
        veiculo,
    ):
        dados_aluguel = (
            aluguel.to_dict()
        )
        dados_veiculo = (
            veiculo.to_dict()
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                model_aluguel = sessao.get(
                    AluguelModel,
                    dados_aluguel["id"],
                )

                if model_aluguel is None:
                    raise RuntimeError(
                        "Aluguel não encontrado "
                        "durante a devolução."
                    )

                model_veiculo = sessao.get(
                    VeiculoModel,
                    dados_veiculo["id"],
                )

                if model_veiculo is None:
                    raise RuntimeError(
                        "Veículo não encontrado "
                        "durante a devolução."
                    )

                model_aluguel.status = (
                    dados_aluguel[
                        "status"
                    ]
                )
                model_aluguel.km = (
                    dados_aluguel.get(
                        "km",
                        0,
                    )
                )
                model_aluguel.pagamento = (
                    dados_aluguel.get(
                        "pagamento"
                    )
                )
                model_aluguel.valor = (
                    dados_aluguel.get(
                        "valor",
                        0,
                    )
                )
                model_aluguel.data_fim = (
                    dados_aluguel.get(
                        "data_fim"
                    )
                )
                model_aluguel.dias_atraso = (
                    dados_aluguel.get(
                        "dias_atraso",
                        0,
                    )
                )
                model_aluguel.multa = (
                    dados_aluguel.get(
                        "multa",
                        0,
                    )
                )

                model_veiculo.quilometragem = (
                    dados_veiculo[
                        "quilometragem"
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

                # Finalização do aluguel e liberação do veículo
                # ficam na mesma transação.
                sessao.commit()

                return None

            except Exception:
                sessao.rollback()
                raise

    # ================================================================
    # LISTAGENS
    # ================================================================

    def listar_colecao(self):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    AluguelModel
                )
                .order_by(
                    AluguelModel.id
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

    def listar_ativos(self):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    AluguelModel
                )
                .where(
                    AluguelModel.status
                    == "ativo"
                )
                .order_by(
                    AluguelModel.id
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
