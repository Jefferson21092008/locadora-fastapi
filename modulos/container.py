from modulos.config import Configuracao

from modulos.cache import (
    CacheRedis,
)
from modulos.database import (
    BancoSQLAlchemy,
)

from modulos.repositories.background_job_repository import (
    BackgroundJobRepository,
)
from modulos.repositories.aluguel_repository import (
    AluguelRepository,
)
from modulos.repositories.auditoria_repository import (
    AuditoriaRepository,
)
from modulos.repositories.cliente_repository import (
    ClienteRepository,
)
from modulos.repositories.manutencao_repository import (
    ManutencaoRepository,
)
from modulos.repositories.notificacao_repository import (
    NotificacaoRepository,
)
from modulos.repositories.outbox_repository import (
    OutboxRepository,
)
from modulos.repositories.pagamento_repository import (
    PagamentoRepository,
)
from modulos.repositories.relatorio_repository import (
    RelatorioRepository,
)
from modulos.repositories.reserva_repository import (
    ReservaRepository,
)
from modulos.repositories.sessao_repository import (
    SessaoRepository,
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
from modulos.repositories.vistoria_repository import (
    VistoriaRepository,
)

from modulos.servicos.background_job_service import (
    BackgroundJobService,
)
from modulos.servicos.cache_service import (
    CacheService,
)
from modulos.servicos.admin_service import (
    AdminService,
)
from modulos.servicos.auditoria_service import (
    AuditoriaService,
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
from modulos.servicos.exportacao_relatorios_service import (
    ExportacaoRelatoriosService,
)
from modulos.servicos.manutencao_service import (
    ManutencaoService,
)
from modulos.servicos.notificacao_service import (
    NotificacaoService,
)
from modulos.servicos.outbox_service import (
    OutboxService,
)
from modulos.servicos.pagamento_service import (
    PagamentoService,
)
from modulos.servicos.relatorios_service import (
    RelatorioService,
)
from modulos.servicos.reserva_service import (
    ReservaService,
)
from modulos.servicos.sessao_service import (
    SessaoService,
)
from modulos.servicos.recuperacao_senha_service import (
    RecuperacaoSenhaService,
)
from modulos.servicos.veiculos_service import (
    VeiculoService,
)
from modulos.servicos.vistoria_service import (
    VistoriaService,
)

from modulos.usuarios import Role

from modulos.event_handlers import registrar_handlers_padrao
from modulos.eventos import BarramentoEventos

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

        self.cache_backend = CacheRedis(
            redis_url=getattr(
                self.config,
                "redis_url",
                None,
            ),
            prefixo=getattr(
                self.config,
                "redis_prefixo",
                "locadora",
            ),
            timeout_ms=getattr(
                self.config,
                "redis_timeout_ms",
                500,
            ),
        )

        self.evento_barramento = BarramentoEventos(
            despacho_imediato=False
        )
        self._criar_repositories()
        self._criar_services()
        self._registrar_event_handlers()
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

        self.auditoria_repository = (
            AuditoriaRepository(
                banco_sqlalchemy=(
                    self.banco_sqlalchemy
                ),
            )
        )

        self.background_job_repository = (
            BackgroundJobRepository(
                banco_sqlalchemy=(
                    self.banco_sqlalchemy
                ),
            )
        )

        self.outbox_repository = (
            OutboxRepository(
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

        self.sessao_repository = (
            SessaoRepository(
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

        self.reserva_repository = (
            ReservaRepository(
                banco_sqlalchemy=(
                    self.banco_sqlalchemy
                ),
            )
        )

        self.pagamento_repository = (
            PagamentoRepository(
                banco_sqlalchemy=(
                    self.banco_sqlalchemy
                ),
            )
        )

        self.notificacao_repository = (
            NotificacaoRepository(
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

        self.vistoria_repository = (
            VistoriaRepository(
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
        self.cache_service = (
            CacheService(
                cache_backend=(
                    self.cache_backend
                ),
            )
        )

        self.auditoria_service = (
            AuditoriaService(
                auditoria_repository=(
                    self.auditoria_repository
                ),
            )
        )

        self.auth_service = (
            AuthService(
                usuario_repository=(
                    self.usuario_repository
                ),
            )
        )

        self.sessao_service = (
            SessaoService(
                sessao_repository=(
                    self.sessao_repository
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
                sessao_repository=(
                    self.sessao_repository
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
                reserva_repository=(
                    self.reserva_repository
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
                reserva_repository=(
                    self.reserva_repository
                ),
                evento_barramento=(
                    self.evento_barramento
                ),
            )
        )

        self.reserva_service = (
            ReservaService(
                veiculo_service=(
                    self.veiculo_service
                ),
                reserva_repository=(
                    self.reserva_repository
                ),
                aluguel_repository=(
                    self.aluguel_repository
                ),
                manutencao_repository=(
                    self.manutencao_repository
                ),
                evento_barramento=(
                    self.evento_barramento
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
                reserva_repository=(
                    self.reserva_repository
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
                reserva_service=(
                    self.reserva_service
                ),
                evento_barramento=(
                    self.evento_barramento
                ),
            )
        )

        self.vistoria_service = (
            VistoriaService(
                aluguel_repository=(
                    self.aluguel_repository
                ),
                vistoria_repository=(
                    self.vistoria_repository
                ),
            )
        )

        self.pagamento_service = (
            PagamentoService(
                aluguel_repository=(
                    self.aluguel_repository
                ),
                pagamento_repository=(
                    self.pagamento_repository
                ),
                vistoria_service=(
                    self.vistoria_service
                ),
                evento_barramento=(
                    self.evento_barramento
                ),
            )
        )

        self.notificacao_service = (
            NotificacaoService(
                notificacao_repository=(
                    self.notificacao_repository
                ),
                usuario_repository=(
                    self.usuario_repository
                ),
                cliente_repository=(
                    self.cliente_repository
                ),
                reserva_repository=(
                    self.reserva_repository
                ),
                aluguel_repository=(
                    self.aluguel_repository
                ),
                manutencao_repository=(
                    self.manutencao_repository
                ),
                pagamento_service=(
                    self.pagamento_service
                ),
                email_service=(
                    self.email_service
                ),
            )
        )

        self.background_job_service = (
            BackgroundJobService(
                background_job_repository=(
                    self.background_job_repository
                ),
                usuario_repository=(
                    self.usuario_repository
                ),
                notificacao_service=(
                    self.notificacao_service
                ),
            )
        )

        self.outbox_service = (
            OutboxService(
                outbox_repository=(
                    self.outbox_repository
                ),
                barramento=(
                    self.evento_barramento
                ),
                retry_base_segundos=getattr(
                    self.config,
                    "mensageria_retry_base_segundos",
                    5,
                ),
                retry_max_segundos=getattr(
                    self.config,
                    "mensageria_retry_max_segundos",
                    300,
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
                cache_service=(
                    self.cache_service
                ),
                dashboard_cache_ttl_segundos=getattr(
                    self.config,
                    "cache_dashboard_ttl_segundos",
                    30,
                ),
            )
        )

        self.exportacao_relatorios_service = (
            ExportacaoRelatoriosService(
                relatorio_service=(
                    self.relatorio_service
                ),
            )
        )

        self.admin_service = (
            AdminService(
                self.auth_service
            )
        )

    # ================================================================
    # EVENTOS
    # ================================================================

    def _registrar_event_handlers(
        self,
    ):
        self.event_handlers = registrar_handlers_padrao(
            barramento=self.evento_barramento,
            cache_service=self.cache_service,
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
