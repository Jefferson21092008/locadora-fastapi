from modulos.clientes import Cliente

from modulos.usuarios import (
    Role,
    Usuario,
)

from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)

class ClienteService:
    """Regras e operações relacionadas aos clientes."""

    def __init__(
        self,
        auth_service,
        cliente_repository,
        aluguel_repository,
    ):
        """
        Recebe as dependências já montadas pelo Container.

        O Service não conhece listas em memória, GerenciadorDados,
        SQLite ou SQLAlchemy. Ele depende apenas dos contratos
        oferecidos pelos repositories e pelo AuthService.
        """
        if cliente_repository is None:
            raise ValueError(
                "ClienteRepository é obrigatório."
            )

        if aluguel_repository is None:
            raise ValueError(
                "AluguelRepository é obrigatório."
            )

        self.auth_service = (
            auth_service
        )
        self.cliente_repository = (
            cliente_repository
        )
        self.aluguel_repository = (
            aluguel_repository
        )

    # ================================================================
    # BUSCAS
    # ================================================================

    def buscar_por_usuario_id(
        self,
        usuario_id,
    ):
        return (
            self.cliente_repository
            .buscar_por_usuario_id(
                usuario_id
            )
        )

    def buscar_por_id(
        self,
        id_cliente,
    ):
        return (
            self.cliente_repository
            .buscar_por_id(
                id_cliente
            )
        )

    def buscar_por_usuario(
        self,
        usuario,
    ):
        return (
            self.cliente_repository
            .buscar_por_usuario(
                usuario
            )
        )

    def buscar_por_email(
        self,
        email,
    ):
        return (
            self.cliente_repository
            .buscar_por_email(
                email
            )
        )

    def buscar_conta_do_cliente(
        self,
        cliente,
    ):
        if (
            self.auth_service is None
            or cliente.usuario_id is None
        ):
            return None

        conta = (
            self.auth_service
            .buscar_por_id(
                cliente.usuario_id
            )
        )

        if (
            conta is not None
            and conta.role
            == Role.CLIENTE
        ):
            return conta

        return None

    # ================================================================
    # CADASTRO
    # ================================================================

    def criar_conta(
        self,
        nome,
        usuario,
        email,
        senha,
    ):
        # ------------------------------------------------------------
        # AUTENTICAÇÃO É OBRIGATÓRIA
        # ------------------------------------------------------------

        if self.auth_service is None:
            raise RegraDeNegocio(
                "Serviço de autenticação "
                "não configurado."
            )

        # ------------------------------------------------------------
        # CRIA O PERFIL DO CLIENTE
        # ------------------------------------------------------------

        cliente, mensagem = (
            Cliente.criar(
                id_cliente=0,
                nome=nome,
                usuario=usuario,
                email=email,
            )
        )

        if cliente is None:
            raise RegraDeNegocio(
                mensagem
            )

        # ------------------------------------------------------------
        # VALIDA A SENHA
        # ------------------------------------------------------------

        valido, mensagem = (
            Usuario.validar_nova_senha(
                senha
            )
        )

        if not valido:
            raise RegraDeNegocio(
                mensagem
            )

        # ------------------------------------------------------------
        # EVITA USUÁRIO DUPLICADO NO PERFIL
        # ------------------------------------------------------------

        if (
            self.buscar_por_usuario(
                usuario
            )
            is not None
        ):
            raise RegraDeNegocio(
                "Esse usuário já está cadastrado."
            )

        # ------------------------------------------------------------
        # EVITA E-MAIL DUPLICADO
        # ------------------------------------------------------------

        if (
            self.buscar_por_email(
                email
            )
            is not None
        ):
            raise RegraDeNegocio(
                "Esse e-mail já está cadastrado."
            )

        # ------------------------------------------------------------
        # EVITA USUÁRIO DUPLICADO NA AUTENTICAÇÃO
        # ------------------------------------------------------------

        if (
            self.auth_service
            .buscar_por_usuario(
                usuario
            )
            is not None
        ):
            raise RegraDeNegocio(
                "Esse usuário já existe."
            )

        # ------------------------------------------------------------
        # CRIA A CONTA DE AUTENTICAÇÃO
        # ------------------------------------------------------------

        conta = Usuario.criar(
            id_usuario=0,
            usuario=usuario,
            senha=senha,
            role=Role.CLIENTE,
        )

        valido, mensagem = (
            conta.validar_dados()
        )

        if not valido:
            raise RegraDeNegocio(
                mensagem
            )

        # ------------------------------------------------------------
        # CLIENTE + USUÁRIO NA MESMA TRANSAÇÃO
        # ------------------------------------------------------------

        (
            cliente_id,
            usuario_id,
        ) = (
            self.cliente_repository
            .registrar_com_usuario(
                cliente,
                conta,
            )
        )

        # ------------------------------------------------------------
        # ATUALIZA AS ENTIDADES COM OS IDS GERADOS NO BANCO
        # ------------------------------------------------------------

        cliente.id = (
            cliente_id
        )

        cliente.usuario_id = (
            usuario_id
        )

        conta.id = (
            usuario_id
        )

        return cliente

    # ================================================================
    # LOGIN
    # ================================================================

    def login(
        self,
        usuario,
        senha,
    ):
        if self.auth_service is None:
            raise RegraDeNegocio(
                "Serviço de autenticação "
                "não configurado."
            )

        # ------------------------------------------------------------
        # AUTENTICA PELO USUÁRIO
        # ------------------------------------------------------------

        autenticado = (
            self.auth_service
            .autenticar(
                nome_usuario=usuario,
                senha=senha,
                role=Role.CLIENTE,
            )
        )

        if not autenticado:
            # Mantém mensagem genérica por segurança.
            raise RegraDeNegocio(
                "Usuário ou senha incorretos."
            )

        # ------------------------------------------------------------
        # RECUPERA A CONTA
        # ------------------------------------------------------------

        conta = (
            self.auth_service
            .buscar_por_usuario(
                usuario
            )
        )

        if conta is None:
            raise RegraDeNegocio(
                "Usuário ou senha incorretos."
            )

        # ------------------------------------------------------------
        # RECUPERA O PERFIL
        # ------------------------------------------------------------

        cliente = (
            self.buscar_por_usuario_id(
                conta.id
            )
        )

        if cliente is None:
            raise RecursoNaoEncontrado(
                "Perfil do cliente "
                "não encontrado."
            )

        if not cliente.ativo:
            raise RegraDeNegocio(
                "Essa conta está desativada."
            )

        return cliente

    # ================================================================
    # ALIAS
    # ================================================================

    def autenticar(
        self,
        usuario,
        senha,
    ):
        """
        Mantém compatibilidade com chamadas que
        utilizam o nome autenticar().

        A autenticação real é feita em login().
        """

        return self.login(
            usuario,
            senha,
        )

    # ================================================================
    # NOME DE USUÁRIO
    # ================================================================

    def renomear_usuario(
        self,
        cliente,
        novo_usuario,
        senha_atual,
    ):
        conta = (
            self.buscar_conta_do_cliente(
                cliente
            )
        )

        if conta is None:
            raise RecursoNaoEncontrado(
                "Conta de usuário "
                "não encontrada."
            )

        if not conta.ativo:
            raise RegraDeNegocio(
                "Usuário desativado."
            )

        if not conta.validar_senha(
            senha_atual
        ):
            raise RegraDeNegocio(
                "Senha atual incorreta."
            )

        novo_usuario = str(
            novo_usuario
        ).strip()

        valido, mensagem = (
            Usuario.validar_nome_usuario(
                novo_usuario
            )
        )

        if not valido:
            raise RegraDeNegocio(
                mensagem
            )

        if (
            novo_usuario.lower()
            == conta.usuario.lower()
        ):
            raise RegraDeNegocio(
                "O novo usuário deve ser "
                "diferente do atual."
            )

        usuario_existente = (
            self.auth_service
            .buscar_por_usuario(
                novo_usuario
            )
        )

        if usuario_existente is not None:
            raise RegraDeNegocio(
                "Esse usuário já existe."
            )

        cliente_existente = (
            self.buscar_por_usuario(
                novo_usuario
            )
        )

        if cliente_existente is not None:
            raise RegraDeNegocio(
                "Esse usuário já está cadastrado."
            )

        usuario_anterior = (
            conta.usuario
        )

        cliente_usuario_anterior = (
            cliente.usuario
        )

        try:
            (
                self.cliente_repository
                .renomear_usuario_com_conta(
                    usuario_id=conta.id,
                    novo_usuario=novo_usuario,
                )
            )

        except Exception:
            conta.usuario = (
                usuario_anterior
            )

            cliente.usuario = (
                cliente_usuario_anterior
            )

            raise

        conta.usuario = novo_usuario
        cliente.usuario = novo_usuario

        return cliente

    # ================================================================
    # SENHA
    # ================================================================

    def alterar_senha(
        self,
        cliente,
        senha_atual,
        nova_senha,
    ):
        if self.auth_service is None:
            raise RegraDeNegocio(
                "Serviço de autenticação "
                "não configurado."
            )

        conta = (
            self.buscar_conta_do_cliente(
                cliente
            )
        )

        if conta is None:
            raise RecursoNaoEncontrado(
                "Conta de usuário "
                "não encontrada."
            )

        return (
            self.auth_service
            .alterar_senha(
                nome_usuario=conta.usuario,
                senha_atual=senha_atual,
                nova_senha=nova_senha,
                role=Role.CLIENTE,
            )
        )

    # ================================================================
    # ALUGUÉIS
    # ================================================================

    def possui_aluguel_ativo(
        self,
        cliente,
    ):
        return (
            self.aluguel_repository
            .buscar_ativo(
                cliente
            )
            is not None
        )

    # ================================================================
    # DESATIVAÇÃO
    # ================================================================

    def desativar(
        self,
        id_cliente,
    ):
        cliente = (
            self.buscar_por_id(
                id_cliente
            )
        )

        if cliente is None:
            raise RecursoNaoEncontrado(
                "Cliente não encontrado."
            )

        if (
            self.possui_aluguel_ativo(
                cliente
            )
        ):
            raise RegraDeNegocio(
                "Não é possível desativar "
                "um cliente com aluguel ativo."
            )

        if self.auth_service is None:
            raise RegraDeNegocio(
                "Serviço de autenticação "
                "não configurado."
            )

        conta = (
            self.buscar_conta_do_cliente(
                cliente
            )
        )

        if conta is None:
            raise RegraDeNegocio(
                "Conta de usuário "
                "não encontrada."
            )

        # ------------------------------------------------------------
        # GUARDA ESTADO PARA ROLLBACK EM MEMÓRIA
        # ------------------------------------------------------------

        estado_cliente = (
            cliente.ativo
        )

        estado_conta = (
            conta.ativo
        )

        # ------------------------------------------------------------
        # ALTERA A ENTIDADE
        # ------------------------------------------------------------

        sucesso, mensagem = (
            cliente.desativar()
        )

        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        # ------------------------------------------------------------
        # ALTERA CLIENTE + USUÁRIO NO SQLITE
        # ------------------------------------------------------------

        try:
            (
                self.cliente_repository
                .atualizar_status_com_usuario(
                    cliente.id,
                    cliente.usuario_id,
                    False,
                )
            )

            conta.ativo = False

        except Exception:
            cliente.ativo = estado_cliente
            conta.ativo = estado_conta
            raise

        return cliente

    # ================================================================
    # REATIVAÇÃO
    # ================================================================

    def reativar(
        self,
        id_cliente,
    ):
        cliente = (
            self.buscar_por_id(
                id_cliente
            )
        )

        if cliente is None:
            raise RecursoNaoEncontrado(
                "Cliente não encontrado."
            )

        if self.auth_service is None:
            raise RegraDeNegocio(
                "Serviço de autenticação "
                "não configurado."
            )

        conta = (
            self.buscar_conta_do_cliente(
                cliente
            )
        )

        if conta is None:
            raise RegraDeNegocio(
                "Conta de usuário "
                "não encontrada."
            )

        # ------------------------------------------------------------
        # GUARDA ESTADO
        # ------------------------------------------------------------

        estado_cliente = (
            cliente.ativo
        )

        estado_conta = (
            conta.ativo
        )

        # ------------------------------------------------------------
        # ALTERA ENTIDADE
        # ------------------------------------------------------------

        sucesso, mensagem = (
            cliente.reativar()
        )

        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        # ------------------------------------------------------------
        # PERSISTE OS DOIS ESTADOS
        # ------------------------------------------------------------

        try:
            (
                self.cliente_repository
                .atualizar_status_com_usuario(
                    cliente.id,
                    cliente.usuario_id,
                    True,
                )
            )

            conta.ativo = True

        except Exception:
            cliente.ativo = (
                estado_cliente
            )

            conta.ativo = (
                estado_conta
            )

            raise

        return cliente

    # ================================================================
    # LISTAGENS
    # ================================================================

    def listar_clientes(self):
        return (
            self.cliente_repository
            .listar()
        )


    def listar_ativos(self):
        return (
            self.cliente_repository
            .listar_ativos()
        )


    def listar_desativados(self):
        return (
            self.cliente_repository
            .listar_desativados()
        )
