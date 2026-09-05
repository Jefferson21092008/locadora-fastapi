from sqlalchemy import select

from modulos.models.veiculo_model import VeiculoModel
from modulos.veiculos import StatusVeiculo, Veiculo


class VeiculoRepository:
    """Acesso aos veículos usando exclusivamente SQLAlchemy."""

    def __init__(
        self,
        banco_sqlalchemy,
    ):
        if banco_sqlalchemy is None:
            raise ValueError(
                "BancoSQLAlchemy é obrigatório."
            )

        self.banco_sqlalchemy = banco_sqlalchemy

    # ================================================================
    # MAPEAMENTO MODEL -> ENTIDADE
    # ================================================================

    @staticmethod
    def _para_entidade(
        model,
    ):
        if model is None:
            return None

        return Veiculo.from_dict(
            {
                "id": model.id,
                "tipo": model.tipo,
                "modelo": model.modelo,
                "ano": model.ano,
                "diaria": model.diaria,
                "preco_km": model.preco_km,
                "quilometragem": model.quilometragem,
                "status": model.status,
                "disponivel": model.disponivel,
                "alugado_por": model.alugado_por,
                "ativo": model.ativo,
            },
            id_padrao=model.id,
        )

    @classmethod
    def _para_entidades(
        cls,
        models,
    ):
        return [
            cls._para_entidade(model)
            for model in models
        ]

    # ================================================================
    # BUSCAS
    # ================================================================

    def buscar_por_id(
        self,
        id_veiculo,
    ):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.get(
                VeiculoModel,
                id_veiculo,
            )

            return self._para_entidade(
                model
            )

    def buscar(
        self,
        termo,
    ):
        termo = str(
            termo
        ).strip()

        if not termo:
            return []

        # A normalização do domínio remove acentos e trata
        # tipo/modelo da mesma forma que o sistema antigo.
        ativos = self.listar_ativos()

        return [
            veiculo
            for veiculo in ativos
            if veiculo.corresponde_busca(
                termo
            )
        ]

    # ================================================================
    # LISTAGENS
    # ================================================================

    def _listar_por_status(
        self,
        status,
    ):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            comando = (
                select(VeiculoModel)
                .where(
                    VeiculoModel.status
                    == status.value
                )
                .order_by(
                    VeiculoModel.id
                )
            )

            models = sessao.scalars(
                comando
            ).all()

            return self._para_entidades(
                models
            )

    def listar_colecao(self):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            comando = (
                select(VeiculoModel)
                .order_by(
                    VeiculoModel.id
                )
            )

            models = sessao.scalars(
                comando
            ).all()

            return self._para_entidades(
                models
            )

    def listar_disponiveis(self):
        return self._listar_por_status(
            StatusVeiculo.DISPONIVEL
        )

    def listar_ativos(self):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            comando = (
                select(VeiculoModel)
                .where(
                    VeiculoModel.status
                    != StatusVeiculo.DESATIVADO.value
                )
                .order_by(
                    VeiculoModel.id
                )
            )

            models = sessao.scalars(
                comando
            ).all()

            return self._para_entidades(
                models
            )

    def listar_desativados(self):
        return self._listar_por_status(
            StatusVeiculo.DESATIVADO
        )

    def listar_em_manutencao(self):
        return self._listar_por_status(
            StatusVeiculo.MANUTENCAO
        )

    def listar_alugados(self):
        return self._listar_por_status(
            StatusVeiculo.ALUGADO
        )

    # ================================================================
    # INSERÇÃO / ATUALIZAÇÃO
    # ================================================================

    def inserir(
        self,
        veiculo,
    ):
        dados = veiculo.to_dict()

        model = VeiculoModel(
            tipo=dados["tipo"],
            modelo=dados["modelo"],
            ano=dados["ano"],
            diaria=dados["diaria"],
            preco_km=dados["preco_km"],
            quilometragem=dados[
                "quilometragem"
            ],
            status=dados["status"],
            disponivel=dados[
                "disponivel"
            ],
            alugado_por=dados.get(
                "alugado_por"
            ),
            ativo=dados["ativo"],
        )

        with self.banco_sqlalchemy.criar_sessao() as sessao:
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

    def atualizar(
        self,
        veiculo,
    ):
        dados = veiculo.to_dict()

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            try:
                model = sessao.get(
                    VeiculoModel,
                    dados["id"],
                )

                if model is None:
                    raise RuntimeError(
                        "Veículo não encontrado."
                    )

                model.tipo = dados["tipo"]
                model.modelo = dados["modelo"]
                model.ano = dados["ano"]
                model.diaria = dados["diaria"]
                model.preco_km = dados["preco_km"]
                model.quilometragem = dados[
                    "quilometragem"
                ]
                model.status = dados["status"]
                model.disponivel = dados[
                    "disponivel"
                ]
                model.alugado_por = dados.get(
                    "alugado_por"
                )
                model.ativo = dados["ativo"]

                sessao.commit()

                return None

            except Exception:
                sessao.rollback()
                raise
