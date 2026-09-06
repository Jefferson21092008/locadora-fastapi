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

from api.routers.manutencoes import (
    router as manutencoes_router,
)

from api.routers.relatorios import (
    router as relatorios_router,
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

- Autenticação com JWT.
- Controle de acesso por perfil de usuário.
- Cadastro e gerenciamento de clientes.
- Cadastro e gerenciamento de veículos.
- Controle de aluguéis e devoluções.
- Controle de manutenções.
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
            "Login, geração de token JWT "
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
        "name": "Relatórios",
        "description": (
            "Relatórios operacionais, "
            "administrativos e financeiros."
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


app = FastAPI(
    title="Locadora API",
    description=descricao_api,
    version="1.0.0",
    openapi_tags=tags_metadata,
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


app.include_router(
    auth_router
)

app.include_router(
    clientes_router
)

app.include_router(
    veiculos_router
)

app.include_router(
    alugueis_router
)

app.include_router(
    manutencoes_router
)

app.include_router(
    relatorios_router
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
    }
