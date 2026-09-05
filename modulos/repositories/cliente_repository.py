from sqlalchemy import (
    func,
    select,
)

from modulos.clientes import (
    Cliente,
)
from modulos.models.cliente_model import (
    ClienteModel,
)
from modulos.models.usuario_model import (
    UsuarioModel,
)


class ClienteRepository:
    """
    Repository de clientes baseado exclusivamente em SQLAlchemy.

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

        return Cliente.from_dict(
            {
                "id": model.id,
                "nome": model.nome,
                "usuario": model.usuario,
                "email": model.email,
                "ativo": model.ativo,
                "usuario_id": model.usuario_id,
            },
            id_padrao=model.id,
        )

    # ================================================================
    # BUSCAS
    # ================================================================

    def buscar_por_id(
        self,
        id_cliente,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            model = sessao.get(
                ClienteModel,
                id_cliente,
            )

            return self._para_entidade(
                model
            )

    def buscar_por_usuario_id(
        self,
        usuario_id,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = select(
                ClienteModel
            ).where(
                ClienteModel.usuario_id
                == usuario_id
            )

            model = sessao.scalar(
                comando
            )

            return self._para_entidade(
                model
            )

    def buscar_por_usuario(
        self,
        usuario,
    ):
        usuario = (
            str(usuario)
            .strip()
            .lower()
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = select(
                ClienteModel
            ).where(
                func.lower(
                    ClienteModel.usuario
                )
                == usuario
            )

            model = sessao.scalar(
                comando
            )

            return self._para_entidade(
                model
            )

    def buscar_por_email(
        self,
        email,
    ):
        if not email:
            return None

        email = (
            str(email)
            .strip()
            .lower()
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = select(
                ClienteModel
            ).where(
                func.lower(
                    ClienteModel.email
                )
                == email
            )

            model = sessao.scalar(
                comando
            )

            return self._para_entidade(
                model
            )

    # ================================================================
    # LISTAGENS
    # ================================================================

    def listar(self):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    ClienteModel
                )
                .order_by(
                    ClienteModel.id
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

    def listar_ativos(self):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    ClienteModel
                )
                .where(
                    ClienteModel.ativo
                    .is_(True)
                )
                .order_by(
                    ClienteModel.id
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

    def listar_desativados(self):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    ClienteModel
                )
                .where(
                    ClienteModel.ativo
                    .is_(False)
                )
                .order_by(
                    ClienteModel.id
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
    # INSERÇÃO / ATUALIZAÇÃO
    # ================================================================

    def inserir(
        self,
        cliente,
        senha_hash_legado="",
    ):
        dados = cliente.to_dict()

        model = ClienteModel(
            nome=dados["nome"],
            usuario=dados["usuario"],
            email=dados["email"],
            senha_hash=senha_hash_legado,
            ativo=dados["ativo"],
            usuario_id=dados.get(
                "usuario_id"
            ),
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
        cliente,
    ):
        dados = cliente.to_dict()

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                model = sessao.get(
                    ClienteModel,
                    dados["id"],
                )

                if model is None:
                    raise RuntimeError(
                        "Cliente não encontrado."
                    )

                model.nome = (
                    dados["nome"]
                )
                model.usuario = (
                    dados["usuario"]
                )
                model.email = (
                    dados["email"]
                )
                model.ativo = (
                    dados["ativo"]
                )
                model.usuario_id = (
                    dados.get(
                        "usuario_id"
                    )
                )

                sessao.commit()

                return None

            except Exception:
                sessao.rollback()
                raise

    # ================================================================
    # TRANSAÇÃO CLIENTE + USUÁRIO
    # ================================================================

    def registrar_com_usuario(
        self,
        cliente,
        usuario,
    ):
        dados_usuario = (
            usuario.to_dict()
        )

        dados_cliente = (
            cliente.to_dict()
        )

        usuario_model = UsuarioModel(
            usuario=dados_usuario[
                "usuario"
            ],
            senha_hash=dados_usuario[
                "senha_hash"
            ],
            role=dados_usuario[
                "role"
            ],
            ativo=dados_usuario[
                "ativo"
            ],
            criado_em=dados_usuario[
                "criado_em"
            ],
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                sessao.add(
                    usuario_model
                )

                # Envia o INSERT sem finalizar a transação.
                # Assim recebemos o ID do usuário para vincular
                # o perfil do cliente antes do commit.
                sessao.flush()

                cliente_model = ClienteModel(
                    nome=dados_cliente[
                        "nome"
                    ],
                    usuario=dados_cliente[
                        "usuario"
                    ],
                    email=dados_cliente[
                        "email"
                    ],
                    # Compatibilidade com a coluna antiga.
                    # A senha verdadeira pertence a usuarios.
                    senha_hash="",
                    ativo=dados_cliente[
                        "ativo"
                    ],
                    usuario_id=(
                        usuario_model.id
                    ),
                )

                sessao.add(
                    cliente_model
                )
                sessao.flush()

                cliente_id = (
                    cliente_model.id
                )
                usuario_id = (
                    usuario_model.id
                )

                # Cliente e usuário são confirmados juntos.
                sessao.commit()

                return (
                    cliente_id,
                    usuario_id,
                )

            except Exception:
                sessao.rollback()
                raise

    def atualizar_status_com_usuario(
        self,
        cliente_id,
        usuario_id,
        ativo,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                cliente_model = (
                    sessao.get(
                        ClienteModel,
                        cliente_id,
                    )
                )

                if cliente_model is None:
                    raise RuntimeError(
                        "Cliente não encontrado."
                    )

                usuario_model = (
                    sessao.get(
                        UsuarioModel,
                        usuario_id,
                    )
                )

                if (
                    usuario_model is None
                    or usuario_model.role
                    != "cliente"
                ):
                    raise RuntimeError(
                        "Usuário do cliente "
                        "não encontrado."
                    )

                cliente_model.ativo = bool(
                    ativo
                )
                usuario_model.ativo = bool(
                    ativo
                )

                sessao.commit()

                return None

            except Exception:
                sessao.rollback()
                raise

    # ================================================================
    # COMPATIBILIDADE DE INTERFACE TEMPORÁRIA
    # ================================================================

    def listar_colecao(self):
        """
        Alias temporário para consumidores ainda não migrados.
        A fonte de verdade continua sendo exclusivamente o banco.
        """
        return self.listar()
