from fastapi import (
    FastAPI,
    HTTPException,
    Request,
)

from fastapi.responses import (
    JSONResponse,
)

from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)


async def tratar_recurso_nao_encontrado(
    request: Request,
    erro: RecursoNaoEncontrado,
):
    return JSONResponse(
        status_code=404,
        content={
            "detail": erro.mensagem
        },
    )


async def tratar_regra_de_negocio(
    request: Request,
    erro: RegraDeNegocio,
):
    return JSONResponse(
        status_code=400,
        content={
            "detail": erro.mensagem
        },
    )


def registrar_handlers(
    app: FastAPI,
):
    app.add_exception_handler(
        RecursoNaoEncontrado,
        tratar_recurso_nao_encontrado,
    )

    app.add_exception_handler(
        RegraDeNegocio,
        tratar_regra_de_negocio,
    )


def nao_autorizado(
    mensagem,
):
    raise HTTPException(
        status_code=401,
        detail=mensagem,
    )


def acesso_negado(
    mensagem,
):
    raise HTTPException(
        status_code=403,
        detail=mensagem,
    )


def recurso_nao_encontrado(
    mensagem,
):
    raise HTTPException(
        status_code=404,
        detail=mensagem,
    )
