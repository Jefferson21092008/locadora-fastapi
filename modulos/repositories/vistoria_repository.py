from sqlalchemy import (
    select,
)

from modulos.models.vistoria_model import (
    CaucaoAluguelModel,
    DanoAluguelModel,
    InspecaoAluguelModel,
    MultaTransitoModel,
)
from modulos.vistorias import (
    CaucaoAluguel,
    DanoAluguel,
    InspecaoAluguel,
    MultaTransito,
)


class VistoriaRepository:
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
    # MAPEAMENTO
    # ================================================================

    @staticmethod
    def _inspecao_para_entidade(
        model,
    ):
        if model is None:
            return None

        return InspecaoAluguel.from_dict(
            {
                "id": model.id,
                "aluguel_id": model.aluguel_id,
                "tipo": model.tipo,
                "quilometragem": model.quilometragem,
                "combustivel_percentual": (
                    model.combustivel_percentual
                ),
                "observacoes": model.observacoes,
                "criada_em": model.criada_em,
            }
        )

    @staticmethod
    def _dano_para_entidade(
        model,
    ):
        if model is None:
            return None

        return DanoAluguel.from_dict(
            {
                "id": model.id,
                "aluguel_id": model.aluguel_id,
                "descricao": model.descricao,
                "valor_estimado": (
                    model.valor_estimado
                ),
                "status": model.status,
                "criada_em": model.criada_em,
                "cancelada_em": (
                    model.cancelada_em
                ),
            }
        )

    @staticmethod
    def _multa_para_entidade(
        model,
    ):
        if model is None:
            return None

        return MultaTransito.from_dict(
            {
                "id": model.id,
                "aluguel_id": model.aluguel_id,
                "descricao": model.descricao,
                "valor": model.valor,
                "data_ocorrencia": (
                    model.data_ocorrencia
                ),
                "status": model.status,
                "criada_em": model.criada_em,
                "cancelada_em": (
                    model.cancelada_em
                ),
            }
        )

    @staticmethod
    def _caucao_para_entidade(
        model,
    ):
        if model is None:
            return None

        return CaucaoAluguel.from_dict(
            {
                "id": model.id,
                "aluguel_id": model.aluguel_id,
                "valor": model.valor,
                "valor_liberado": (
                    model.valor_liberado
                ),
                "status": model.status,
                "observacoes": model.observacoes,
                "criada_em": model.criada_em,
                "atualizada_em": (
                    model.atualizada_em
                ),
            }
        )

    # ================================================================
    # INSPEÇÕES
    # ================================================================

    def buscar_inspecao(
        self,
        aluguel_id,
        tipo,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            model = sessao.scalar(
                select(
                    InspecaoAluguelModel
                )
                .where(
                    InspecaoAluguelModel.aluguel_id
                    == aluguel_id,
                    InspecaoAluguelModel.tipo
                    == tipo,
                )
            )

            return (
                self._inspecao_para_entidade(
                    model
                )
            )

    def listar_inspecoes(
        self,
        aluguel_id,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            models = (
                sessao.scalars(
                    select(
                        InspecaoAluguelModel
                    )
                    .where(
                        InspecaoAluguelModel.aluguel_id
                        == aluguel_id
                    )
                    .order_by(
                        InspecaoAluguelModel.id
                    )
                )
                .all()
            )

            return [
                self._inspecao_para_entidade(
                    model
                )
                for model
                in models
            ]

    def registrar_inspecao(
        self,
        inspecao,
    ):
        dados = (
            inspecao.to_dict()
        )

        model = InspecaoAluguelModel(
            aluguel_id=dados[
                "aluguel_id"
            ],
            tipo=dados["tipo"],
            quilometragem=dados[
                "quilometragem"
            ],
            combustivel_percentual=dados[
                "combustivel_percentual"
            ],
            observacoes=dados[
                "observacoes"
            ],
            criada_em=dados[
                "criada_em"
            ],
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                sessao.add(
                    model
                )
                sessao.commit()
                sessao.refresh(
                    model
                )
                return model.id
            except Exception:
                sessao.rollback()
                raise

    # ================================================================
    # DANOS
    # ================================================================

    def listar_danos(
        self,
        aluguel_id,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            models = (
                sessao.scalars(
                    select(
                        DanoAluguelModel
                    )
                    .where(
                        DanoAluguelModel.aluguel_id
                        == aluguel_id
                    )
                    .order_by(
                        DanoAluguelModel.id
                    )
                )
                .all()
            )

            return [
                self._dano_para_entidade(
                    model
                )
                for model
                in models
            ]

    def buscar_dano(
        self,
        id_dano,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            return (
                self._dano_para_entidade(
                    sessao.get(
                        DanoAluguelModel,
                        id_dano,
                    )
                )
            )

    def registrar_dano(
        self,
        dano,
    ):
        dados = dano.to_dict()

        model = DanoAluguelModel(
            aluguel_id=dados[
                "aluguel_id"
            ],
            descricao=dados[
                "descricao"
            ],
            valor_estimado=dados[
                "valor_estimado"
            ],
            status=dados[
                "status"
            ],
            criada_em=dados[
                "criada_em"
            ],
            cancelada_em=dados[
                "cancelada_em"
            ],
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                sessao.add(
                    model
                )
                sessao.commit()
                sessao.refresh(
                    model
                )
                return model.id
            except Exception:
                sessao.rollback()
                raise

    def atualizar_dano(
        self,
        dano,
    ):
        dados = dano.to_dict()

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                model = sessao.get(
                    DanoAluguelModel,
                    dados["id"],
                )

                if model is None:
                    raise RuntimeError(
                        "Dano não encontrado "
                        "durante a atualização."
                    )

                model.status = dados[
                    "status"
                ]
                model.cancelada_em = dados[
                    "cancelada_em"
                ]

                sessao.commit()
            except Exception:
                sessao.rollback()
                raise

    # ================================================================
    # MULTAS DE TRÂNSITO
    # ================================================================

    def listar_multas(
        self,
        aluguel_id,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            models = (
                sessao.scalars(
                    select(
                        MultaTransitoModel
                    )
                    .where(
                        MultaTransitoModel.aluguel_id
                        == aluguel_id
                    )
                    .order_by(
                        MultaTransitoModel.id
                    )
                )
                .all()
            )

            return [
                self._multa_para_entidade(
                    model
                )
                for model
                in models
            ]

    def buscar_multa(
        self,
        id_multa,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            return (
                self._multa_para_entidade(
                    sessao.get(
                        MultaTransitoModel,
                        id_multa,
                    )
                )
            )

    def registrar_multa(
        self,
        multa,
    ):
        dados = multa.to_dict()

        model = MultaTransitoModel(
            aluguel_id=dados[
                "aluguel_id"
            ],
            descricao=dados[
                "descricao"
            ],
            valor=dados[
                "valor"
            ],
            data_ocorrencia=dados[
                "data_ocorrencia"
            ],
            status=dados[
                "status"
            ],
            criada_em=dados[
                "criada_em"
            ],
            cancelada_em=dados[
                "cancelada_em"
            ],
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                sessao.add(
                    model
                )
                sessao.commit()
                sessao.refresh(
                    model
                )
                return model.id
            except Exception:
                sessao.rollback()
                raise

    def atualizar_multa(
        self,
        multa,
    ):
        dados = multa.to_dict()

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                model = sessao.get(
                    MultaTransitoModel,
                    dados["id"],
                )

                if model is None:
                    raise RuntimeError(
                        "Multa não encontrada "
                        "durante a atualização."
                    )

                model.status = dados[
                    "status"
                ]
                model.cancelada_em = dados[
                    "cancelada_em"
                ]

                sessao.commit()
            except Exception:
                sessao.rollback()
                raise

    # ================================================================
    # CAUÇÃO
    # ================================================================

    def buscar_caucao(
        self,
        aluguel_id,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            model = sessao.scalar(
                select(
                    CaucaoAluguelModel
                )
                .where(
                    CaucaoAluguelModel.aluguel_id
                    == aluguel_id
                )
            )

            return (
                self._caucao_para_entidade(
                    model
                )
            )

    def salvar_caucao(
        self,
        caucao,
    ):
        dados = caucao.to_dict()

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                model = sessao.scalar(
                    select(
                        CaucaoAluguelModel
                    )
                    .where(
                        CaucaoAluguelModel.aluguel_id
                        == dados["aluguel_id"]
                    )
                )

                if model is None:
                    model = CaucaoAluguelModel(
                        aluguel_id=dados[
                            "aluguel_id"
                        ],
                        valor=dados[
                            "valor"
                        ],
                        valor_liberado=dados[
                            "valor_liberado"
                        ],
                        status=dados[
                            "status"
                        ],
                        observacoes=dados[
                            "observacoes"
                        ],
                        criada_em=dados[
                            "criada_em"
                        ],
                        atualizada_em=dados[
                            "atualizada_em"
                        ],
                    )
                    sessao.add(
                        model
                    )
                else:
                    model.valor = dados[
                        "valor"
                    ]
                    model.valor_liberado = dados[
                        "valor_liberado"
                    ]
                    model.status = dados[
                        "status"
                    ]
                    model.observacoes = dados[
                        "observacoes"
                    ]
                    model.atualizada_em = dados[
                        "atualizada_em"
                    ]

                sessao.commit()
                sessao.refresh(
                    model
                )

                return (
                    self._caucao_para_entidade(
                        model
                    )
                )
            except Exception:
                sessao.rollback()
                raise
