from modulos.usuarios import (
    Role,
    Usuario,
)

from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)


class AuthService:
    def __init__(
        self,
        usuario_repository,
    ):
        """
        Recebe a abstração responsável pela persistência de usuários.

        O Service não conhece SQLite, SQLAlchemy, listas em memória
        ou GerenciadorDados. Ele depende apenas do contrato do
        repository recebido por injeção.
        """
        if usuario_repository is None:
            raise ValueError(
                "UsuarioRepository é obrigatório."
            )

        self.usuario_repository = (
            usuario_repository
        )

    # ================================================================
    # BUSCA
    # ================================================================

    def buscar_por_id(
        self,
        id_usuario,
    ):
        return (
            self.usuario_repository
            .buscar_por_id(
                id_usuario
            )
        )

    def buscar_por_usuario(
        self,
        nome_usuario,
    ):
        return (
            self.usuario_repository
            .buscar_por_usuario(
                nome_usuario
            )
        )

    # ================================================================
    # CADASTRO
    # ================================================================

    def criar_usuario(
        self,
        nome_usuario,
        senha,
        role=Role.CLIENTE,
    ):
        if (
            self.buscar_por_usuario(
                nome_usuario
            )
            is not None
        ):
            raise RegraDeNegocio(
                "Esse usuário já existe."
            )

        valido, mensagem = (
            Usuario.validar_nova_senha(
                senha
            )
        )

        if not valido:
            raise RegraDeNegocio(
                mensagem
            )

        usuario = Usuario.criar(
            id_usuario=0,
            usuario=nome_usuario,
            senha=senha,
            role=role,
        )

        valido, mensagem = (
            usuario.validar_dados()
        )

        if not valido:
            raise RegraDeNegocio(
                mensagem
            )

        novo_id = (
            self.usuario_repository
            .inserir(
                usuario
            )
        )

        usuario.id = novo_id

        return usuario

    # ================================================================
    # AUTENTICAÇÃO
    # ================================================================

    def autenticar(
        self,
        nome_usuario,
        senha,
        role=None,
    ):
        usuario = (
            self.buscar_por_usuario(
                nome_usuario
            )
        )

        if usuario is None:
            return False

        if not usuario.ativo:
            return False

        if role is not None:
            if not isinstance(
                role,
                Role,
            ):
                role = Role(
                    role
                )

            if (
                usuario.role
                != role
            ):
                return False

        if not usuario.validar_senha(
            senha
        ):
            return False

        hash_atualizado = (
            usuario
            .atualizar_hash_senha(
                senha
            )
        )

        if hash_atualizado:
            self.usuario_repository.atualizar(
                usuario
            )

        return True

    # ================================================================
    # ALTERAÇÃO DE SENHA
    # ================================================================

    def alterar_senha(
        self,
        nome_usuario,
        senha_atual,
        nova_senha,
        role=None,
    ):
        usuario = (
            self.buscar_por_usuario(
                nome_usuario
            )
        )

        if usuario is None:
            raise RecursoNaoEncontrado(
                "Usuário não encontrado."
            )

        if not usuario.ativo:
            raise RegraDeNegocio(
                "Usuário desativado."
            )

        if role is not None:
            if not isinstance(
                role,
                Role,
            ):
                role = Role(
                    role
                )

            if (
                usuario.role
                != role
            ):
                raise RegraDeNegocio(
                    "Usuário sem permissão."
                )

        if not usuario.validar_senha(
            senha_atual
        ):
            raise RegraDeNegocio(
                "Senha atual incorreta."
            )

        if (
            senha_atual
            == nova_senha
        ):
            raise RegraDeNegocio(
                "A nova senha deve ser "
                "diferente da senha atual."
            )

        hash_anterior = (
            usuario
            .to_dict()[
                "senha_hash"
            ]
        )

        sucesso, mensagem = (
            usuario.alterar_senha(
                nova_senha
            )
        )

        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        try:
            self.usuario_repository.atualizar(
                usuario
            )

        except Exception:
            usuario._senha_hash = (
                hash_anterior
            )
            raise

        return "Senha alterada com sucesso."

    def listar_usuarios(self):
        if hasattr(
            self.usuario_repository,
            "listar",
        ):
            return (
                self.usuario_repository
                .listar()
            )

        # Compatibilidade temporária apenas com fakes de testes
        # e com ClienteService enquanto a migração dele não termina.
        return (
            self.usuario_repository
            .listar_colecao()
        )

    def adicionar_usuario_na_colecao(
        self,
        usuario,
    ):
        self.usuario_repository.adicionar_na_colecao(
            usuario
        )
