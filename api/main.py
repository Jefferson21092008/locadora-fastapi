from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
)

from fastapi.staticfiles import (
    StaticFiles,
)

from fastapi.responses import (
    FileResponse,
)

from api.dependencias import (
    get_container,
)

from api.erros import (
    registrar_handlers,
)

from api.observabilidade import (
    configurar_logs,
    middleware_observabilidade,
)

from api.monitoramento import (
    configurar_monitoramento_erros,
)

from api.headers_seguranca import (
    middleware_headers_seguranca,
)

from api.routers.veiculos import (
    router as veiculos_router,
)

from api.routers.clientes import (
    router as clientes_router,
)

from api.routers.auth import (
    router as auth_router,
)

from api.routers.alugueis import (
    router as alugueis_router,
)
from api.routers.auditoria import (
    router as auditoria_router,
)

from api.routers.manutencoes import (
    router as manutencoes_router,
)
from api.routers.notificacoes import (
    router as notificacoes_router,
)
from api.routers.pagamentos import (
    router as pagamentos_router,
)

from api.routers.relatorios import (
    router as relatorios_router,
)
from api.routers.reservas import (
    router as reservas_router,
)
from api.routers.vistorias import (
    router as vistorias_router,
)

from modulos.container import (
    Container,
)
from modulos.background_worker import (
    background_jobs_habilitados_por_ambiente,
    criar_worker_do_container,
)
from modulos.outbox_worker import (
    criar_worker_outbox_do_container,
    mensageria_habilitada_por_ambiente,
)
from modulos.escala_horizontal import (
    identificador_instancia,
    workers_embutidos_habilitados,
)


# ================================================================
# DOCUMENTAÇÃO OPENAPI
# ================================================================


descricao_api = """
API REST para gerenciamento de uma locadora de veículos.

## Principais recursos

- Autenticação com access token JWT e refresh token rotativo.
- Controle de acesso RBAC por permissões granulares.
- Cadastro e gerenciamento de clientes.
- Cadastro e gerenciamento de veículos.
- Controle de aluguéis e devoluções.
- Controle de manutenções.
- Reservas futuras de veículos.
- Vistorias, danos, multas de trânsito, cauções e combustível.
- Pagamentos adicionais e liquidação financeira dos aluguéis.
- Notificações persistentes e lembretes por e-mail.
- Relatórios administrativos e financeiros.

## Respostas de erro

A API utiliza respostas HTTP padronizadas:

- **400** — regra de negócio inválida.
- **401** — autenticação necessária ou token inválido.
- **403** — usuário autenticado sem permissão.
- **404** — recurso não encontrado.
- **422** — dados enviados não passaram pela validação.
"""


tags_metadata = [
    {
        "name": "Autenticação",
        "description": (
            "Login, refresh token, gerenciamento de sessões "
            "e identificação do usuário autenticado."
        ),
    },
    {
        "name": "Clientes",
        "description": (
            "Cadastro, consulta e gerenciamento "
            "dos clientes da locadora."
        ),
    },
    {
        "name": "Veículos",
        "description": (
            "Cadastro, consulta e gerenciamento "
            "da frota de veículos."
        ),
    },
    {
        "name": "Aluguéis",
        "description": (
            "Criação de aluguéis, devoluções "
            "e consultas relacionadas."
        ),
    },
    {
        "name": "Manutenções",
        "description": (
            "Controle do histórico e das "
            "manutenções da frota."
        ),
    },
    {
        "name": "Reservas",
        "description": (
            "Reservas futuras, cancelamentos e "
            "consulta de disponibilidade por período."
        ),
    },
    {
        "name": "Vistorias",
        "description": (
            "Inspeções de retirada e devolução, danos, "
            "multas de trânsito, caução e combustível."
        ),
    },
    {
        "name": "Financeiro",
        "description": (
            "Liquidação de cobranças adicionais, pagamentos "
            "e acompanhamento de saldos por aluguel."
        ),
    },
    {
        "name": "Notificações",
        "description": (
            "Lembretes persistentes da operação, com envio de e-mail "
            "para clientes quando o canal estiver configurado."
        ),
    },
    {
        "name": "Relatórios",
        "description": (
            "Relatórios operacionais, "
            "administrativos e financeiros."
        ),
    },
    {
        "name": "Auditoria",
        "description": (
            "Histórico persistente de ações "
            "sensíveis realizadas no sistema."
        ),
    },
    {
        "name": "Sistema",
        "description": (
            "Rotas básicas para verificar "
            "o funcionamento da API."
        ),
    },
]


configurar_monitoramento_erros()
configurar_logs()


@asynccontextmanager
async def lifespan(app):
    background_worker = None
    outbox_worker = None
    container = None

    workers_embutidos = workers_embutidos_habilitados()

    if workers_embutidos and (
        background_jobs_habilitados_por_ambiente()
        or mensageria_habilitada_por_ambiente()
    ):
        container = get_container()

    if (
        workers_embutidos
        and background_jobs_habilitados_por_ambiente()
    ):
        background_worker = criar_worker_do_container(container)
        background_worker.iniciar()
        app.state.background_worker = background_worker

    if (
        workers_embutidos
        and mensageria_habilitada_por_ambiente()
    ):
        outbox_worker = criar_worker_outbox_do_container(container)
        outbox_worker.iniciar()
        app.state.outbox_worker = outbox_worker

    try:
        yield
    finally:
        if outbox_worker is not None:
            outbox_worker.parar()
        if background_worker is not None:
            background_worker.parar()


app = FastAPI(
    title="Locadora API",
    description=descricao_api,
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.middleware("http")(
    middleware_observabilidade
)

app.middleware("http")(
    middleware_headers_seguranca
)


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

FRONTEND_DIR = (
    BASE_DIR
    / "frontend"
)


# ================================================================
# HANDLERS GLOBAIS
# ================================================================


registrar_handlers(
    app
)


# ================================================================
# ROUTERS
# ================================================================


API_V1_PREFIX = "/api/v1"

ROUTERS_API = (
    auth_router,
    clientes_router,
    veiculos_router,
    alugueis_router,
    manutencoes_router,
    reservas_router,
    vistorias_router,
    pagamentos_router,
    notificacoes_router,
    relatorios_router,
    auditoria_router,
)


# As rotas versionadas são a interface canônica da API e aparecem
# no OpenAPI. As rotas legadas permanecem temporariamente ativas
# para preservar compatibilidade durante a migração do frontend e
# de consumidores externos.
for router in ROUTERS_API:
    app.include_router(
        router,
        prefix=API_V1_PREFIX,
    )

    app.include_router(
        router,
        include_in_schema=False,
    )


# ================================================================
# FRONTEND
# ================================================================


@app.get(
    "/app/",
    include_in_schema=False,
)
def pagina_login():
    """
    Entrega explicitamente a página inicial.

    Isso evita diferenças entre sistemas
    operacionais ao resolver o index.html
    de um diretório montado.
    """
    return FileResponse(
        FRONTEND_DIR
        / "index.html"
    )


app.mount(
    "/app",
    StaticFiles(
        directory=FRONTEND_DIR,
        html=True,
    ),
    name="frontend",
)


# ================================================================
# ROTAS BÁSICAS
# ================================================================


@app.get(
    "/health",
    include_in_schema=False,
)
def health(
    container: Container = Depends(
        get_container
    ),
):
    """
    Health check usado pelo Render.

    Além de confirmar que a API respondeu,
    valida uma consulta simples ao banco.
    """
    container.banco_sqlalchemy.testar_conexao()

    return {
        "status": "ok"
    }


@app.get(
    "/ready",
    include_in_schema=False,
)
def readiness(
    container: Container = Depends(
        get_container
    ),
):
    """Readiness para balanceadores e orquestradores."""
    container.banco_sqlalchemy.testar_conexao()

    if (
        getattr(
            container.config,
            "escala_horizontal_enabled",
            False,
        )
        and not container.cache_backend.ping()
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "Redis compartilhado indisponível para "
                "escala horizontal."
            ),
        )

    return {
        "status": "ready",
        "instance_id": identificador_instancia(),
    }


@app.get(
    "/",
    include_in_schema=False,
)
@app.get(
    f"{API_V1_PREFIX}",
    tags=["Sistema"],
    summary="Verificar a API",
    description=(
        "Retorna uma mensagem simples confirmando "
        "que a API está em funcionamento."
    ),
)
def inicio():
    return {
        "mensagem": (
            "API da Locadora funcionando"
        )
    }


@app.get(
    "/status",
    include_in_schema=False,
)
@app.get(
    f"{API_V1_PREFIX}/status",
    tags=["Sistema"],
    summary="Consultar status da locadora",
    description=(
        "Retorna a quantidade atualmente carregada "
        "de clientes, veículos, aluguéis e manutenções."
    ),
)
def status(
    container: Container = Depends(
        get_container
    ),
):
    return {
        "clientes": len(
            container.cliente_repository
            .listar_colecao()
        ),

        "veiculos": len(
            container.veiculo_repository
            .listar_colecao()
        ),

        "alugueis": len(
            container.aluguel_repository
            .listar_colecao()
        ),

        "manutencoes": len(
            container.manutencao_repository
            .listar_colecao()
        ),

        "reservas": len(
            container.reserva_repository
            .listar_colecao()
        ),
    }
