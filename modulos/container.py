from modulos.config import Configuracao

from modulos.database import (
    BancoSQLAlchemy,
)

from modulos.repositories.aluguel_repository import (
    AluguelRepository,
)
from modulos.repositories.cliente_repository import (
    ClienteRepository,
)
from modulos.repositories.manutencao_repository import (
    ManutencaoRepository,
)
from modulos.repositories.relatorio_repository import (
    RelatorioRepository,
)
from modulos.repositories.token_recuperacao_repository import (
    TokenRecuperacaoRepository,
)
from modulos.repositories.usuario_repository import (
    UsuarioRepository,
)
from modulos.repositories.veiculo_repository import (
    VeiculoRepository,
)

from modulos.servicos.admin_service import (
    AdminService,
)
from modulos.servicos.alugueis_service import (
    AluguelService,
)
from modulos.servicos.auth_service import (
    AuthService,
)
from modulos.servicos.clientes_service import (
    ClienteService,
)
from modulos.servicos.email_service import (
    EmailService,
)
from modulos.servicos.manutencao_service import (
    ManutencaoService,
)
from modulos.servicos.relatorios_service import (
    RelatorioService,
)
from modulos.servicos.recuperacao_senha_service import (
    RecuperacaoSenhaService,
)
from modulos.servicos.veiculos_service import (
    VeiculoService,
)

from modulos.usuarios import Role

from modulos.excecoes import (
    ErroAplicacao,
)


class Container:
    """
    Monta e compartilha as dependências da aplicação.

    O SQLAlchemy é a única infraestrutura de persistência
    utilizada pelo Container. O GerenciadorDados e as
    coleções carregadas em memória não fazem mais parte
    da composição da aplicação.
    """

    def __init__(
        self,
        config=None,
        banco_sqlalchemy=None,
    ):
        self.config = (
            config
            or Configuracao()
        )

        self.banco_sqlalchemy = (
            banco_sqlalchemy
        )

        if self.banco_sqlalchemy is None:
            database_url = getattr(
                self.config,
                "database_url",
                None,
            )

            if not database_url:
                raise RuntimeError(
                    "A configuração do banco "
                    "SQLAlchemy não foi informada."
                )

            self.banco_sqlalchemy = (
                BancoSQLAlchemy(
                    database_url
                )
            )

        self.banco_sqlalchemy.aplicar_migrations()

        self._criar_repositories()
        self._criar_services()
        self._garantir_admin_padrao()

    # ================================================================
    # REPOSITORIES
    # ================================================================

    def _criar_repositories(
        self,
    ):
        """
        Todos os repositories recebem a mesma infraestrutura
        SQLAlchemy. O Container não conhece mais DadosFake,
        GerenciadorDados nem coleções em memória.
        """
        self.usuario_repository = (
            UsuarioRepository(
                banco_sqlalchemy=(
                    self.banco_sqlalchemy
                ),
            )
        )

        self.token_recuperacao_repository = (
            TokenRecuperacaoRepository(
                banco_sqlalchemy=(
                    self.banco_sqlalchemy
                ),
            )
        )

        self.cliente_repository = (
            ClienteRepository(
                banco_sqlalchemy=(
                    self.banco_sqlalchemy
                ),
            )
        )

        self.veiculo_repository = (
            VeiculoRepository(
                banco_sqlalchemy=(
                    self.banco_sqlalchemy
                ),
            )
        )

        self.aluguel_repository = (
            AluguelRepository(
                banco_sqlalchemy=(
                    self.banco_sqlalchemy
                ),
            )
        )

        self.manutencao_repository = (
            ManutencaoRepository(
                banco_sqlalchemy=(
                    self.banco_sqlalchemy
                ),
            )
        )

        self.relatorio_repository = (
            RelatorioRepository(
                banco_sqlalchemy=(
                    self.banco_sqlalchemy
                ),
            )
        )

    # ================================================================
    # SERVICES
    # ================================================================

    def _criar_services(
        self,
    ):
        self.auth_service = (
            AuthService(
                usuario_repository=(
                    self.usuario_repository
                ),
            )
        )

        self.email_service = (
            EmailService(
                self.config
            )
        )

        self.recuperacao_senha_service = (
            RecuperacaoSenhaService(
                usuario_repository=(
                    self.usuario_repository
                ),
                token_recuperacao_repository=(
                    self.token_recuperacao_repository
                ),
                cliente_repository=(
                    self.cliente_repository
                ),
                email_service=(
                    self.email_service
                ),
            )
        )

        self.veiculo_service = (
            VeiculoService(
                veiculo_repository=(
                    self.veiculo_repository
                ),
            )
        )

        self.manutencao_service = (
            ManutencaoService(
                veiculo_service=(
                    self.veiculo_service
                ),
                manutencao_repository=(
                    self.manutencao_repository
                ),
            )
        )

        self.cliente_service = (
            ClienteService(
                auth_service=(
                    self.auth_service
                ),
                cliente_repository=(
                    self.cliente_repository
                ),
                aluguel_repository=(
                    self.aluguel_repository
                ),
            )
        )

        self.aluguel_service = (
            AluguelService(
                veiculo_service=(
                    self.veiculo_service
                ),
                aluguel_repository=(
                    self.aluguel_repository
                ),
            )
        )

        self.relatorio_service = (
            RelatorioService(
                aluguel_repository=(
                    self.aluguel_repository
                ),
                veiculo_repository=(
                    self.veiculo_repository
                ),
                cliente_repository=(
                    self.cliente_repository
                ),
                relatorio_repository=(
                    self.relatorio_repository
                ),
            )
        )

        self.admin_service = (
            AdminService(
                self.auth_service
            )
        )

    # ================================================================
    # ADMIN PADRÃO
    # ================================================================

    def _garantir_admin_padrao(
        self,
    ):
        usuario = (
            self.auth_service
            .buscar_por_usuario(
                self.config.admin_usuario
            )
        )

        if usuario is not None:
            if (
                usuario.role
                != Role.ADMIN
            ):
                raise RuntimeError(
                    f"O nome "
                    f"'{self.config.admin_usuario}' "
                    "já está sendo utilizado por "
                    "uma conta que não é "
                    "administradora."
                )

            return

        try:
            (
                self.auth_service
                .criar_usuario(
                    nome_usuario=(
                        self.config.admin_usuario
                    ),
                    senha=(
                        self.config.admin_senha
                    ),
                    role=Role.ADMIN,
                )
            )

        except ErroAplicacao as erro:
            raise RuntimeError(
                "Não foi possível criar "
                "o administrador inicial: "
                f"{erro.mensagem}"
            ) from erro
