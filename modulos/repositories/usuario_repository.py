from sqlalchemy import (
    func,
    select,
)

from modulos.models.usuario_model import (
    UsuarioModel,
)
from modulos.usuarios import (
    Usuario,
)


class UsuarioRepository:
    """
    Repository de usuários baseado exclusivamente em SQLAlchemy.

    A fonte de verdade é sempre o banco de dados. Não existem mais
    coleções em memória nem fallback para GerenciadorDados.
    """

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

        return Usuario.from_dict(
            {
                "id": model.id,
                "usuario": model.usuario,
                "senha_hash": model.senha_hash,
                "role": model.role,
                "ativo": model.ativo,
                "criado_em": model.criado_em,
            }
        )

    # ================================================================
    # BUSCAS
    # ================================================================

    def buscar_por_usuario(
        self,
        nome_usuario,
    ):
        nome_usuario = (
            str(nome_usuario)
            .strip()
            .lower()
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = select(
                UsuarioModel
            ).where(
                func.lower(
                    UsuarioModel.usuario
                )
                == nome_usuario
            )

            model = sessao.scalar(
                comando
            )

            return self._para_entidade(
                model
            )

    def buscar_por_id(
        self,
        id_usuario,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            model = sessao.get(
                UsuarioModel,
                id_usuario,
            )

            return self._para_entidade(
                model
            )

    def listar(self):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    UsuarioModel
                )
                .order_by(
                    UsuarioModel.id
                )
            )

            models = (
                sessao.scalars(
                    comando
                )
                .all()
            )

            return [
                self._para_entidade(
                    model
                )
                for model in models
            ]

    # ================================================================
    # ESCRITA
    # ================================================================

    def inserir(
        self,
        usuario,
    ):
        dados = usuario.to_dict()

        model = UsuarioModel(
            usuario=dados["usuario"],
            senha_hash=dados["senha_hash"],
            role=dados["role"],
            ativo=dados["ativo"],
            criado_em=dados["criado_em"],
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

    def atualizar(
        self,
        usuario,
    ):
        dados = usuario.to_dict()

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                model = sessao.get(
                    UsuarioModel,
                    dados["id"],
                )

                if model is None:
                    raise RuntimeError(
                        "Usuário não encontrado."
                    )

                model.usuario = (
                    dados["usuario"]
                )
                model.senha_hash = (
                    dados["senha_hash"]
                )
                model.role = (
                    dados["role"]
                )
                model.ativo = (
                    dados["ativo"]
                )
                model.criado_em = (
                    dados["criado_em"]
                )

                sessao.commit()

                return None

            except Exception:
                sessao.rollback()
                raise

    # ================================================================
    # COMPATIBILIDADE DE INTERFACE TEMPORÁRIA
    # ================================================================

    def adicionar_na_colecao(
        self,
        usuario,
    ):
        """
        Mantido temporariamente porque ClienteService ainda chama
        esta operação depois da transação Cliente + Usuario.

        No SQLAlchemy não há coleção para sincronizar, então é no-op.
        """
        return None

    def listar_colecao(self):
        """
        Alias temporário. A fonte de verdade continua sendo o banco.
        """
        return self.listar()
