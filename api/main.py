from pathlib import Path

from fastapi import (
    Depends,
    FastAPI,
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

from api.routers.relatorios import (
    router as relatorios_router,
)
from api.routers.reservas import (
    router as reservas_router,
)

from modulos.container import (
    Container,
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


app = FastAPI(
    title="Locadora API",
    description=descricao_api,
    version="1.0.0",
    openapi_tags=tags_metadata,
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
