from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
)

from api.auditoria import (
    registrar_auditoria,
)
from api.dependencias import (
    exigir_permissao,
    get_cliente_atual,
    get_container,
)
from api.schemas.reservas import (
    ReservaCreate,
    ReservaResponse,
    ReservasConsultaResponse,
)
from modulos.container import Container
from modulos.permissoes import Permissao


router = APIRouter(
    prefix="/reservas",
    tags=["Reservas"],
)


def transformar_reserva(
    reserva,
):
    return ReservaResponse(
        id=reserva.id,
        cliente_id=reserva.cliente_id,
        cliente_usuario=(
            reserva.cliente_usuario
        ),
        cliente_nome=(
            reserva.cliente_nome
        ),
        veiculo_id=reserva.veiculo_id,
        veiculo_tipo=(
            reserva.veiculo_tipo
        ),
        veiculo_modelo=(
            reserva.veiculo_modelo
        ),
        data_inicio=(
            reserva.data_inicio
        ),
        data_fim=reserva.data_fim,
        status=reserva.situacao,
        criada_em=reserva.criada_em,
        cancelada_em=(
            reserva.cancelada_em
        ),
        convertida_em=(
            reserva.convertida_em
        ),
        expirada=reserva.expirada,
    )


def resposta_consulta(
    resultado,
    pagina,
    por_pagina,
):
    return {
        "items": [
            transformar_reserva(
                item
            )
            for item in resultado.items
        ],
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total": resultado.total,
        "total_paginas": (
            resultado.total
            + por_pagina
            - 1
        ) // por_pagina,
        "resumo": resultado.resumo,
    }


@router.post(
    "",
    status_code=201,
    response_model=ReservaResponse,
    summary="Criar reserva futura",
)
def criar_reserva(
    request: Request,
    dados: ReservaCreate,
    cliente=Depends(
        get_cliente_atual
    ),
    container: Container = Depends(
        get_container
    ),
    _usuario=Depends(
        exigir_permissao(
            Permissao.RESERVAS_CRIAR
        )
    ),
):
    reserva = (
        container.reserva_service
        .criar(
            cliente=cliente,
            id_veiculo=(
                dados.id_veiculo
            ),
            data_inicio=(
                dados.data_inicio
            ),
            data_fim=dados.data_fim,
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=cliente,
        acao="reserva.criada",
        recurso="reserva",
        recurso_id=reserva.id,
        campos_alterados=(
            "status",
            "veiculo_id",
            "data_inicio",
            "data_fim",
        ),
    )

    return transformar_reserva(
        reserva
    )


@router.get(
    "",
    response_model=list[
        ReservaResponse
    ],
    summary="Listar todas as reservas",
)
def listar_reservas(
    container: Container = Depends(
        get_container
    ),
    _usuario=Depends(
        exigir_permissao(
            Permissao.RESERVAS_LER
        )
    ),
):
    return [
        transformar_reserva(
            reserva
        )
        for reserva
        in (
            container.reserva_service
            .listar_todas()
        )
    ]


@router.get(
    "/consulta",
    response_model=ReservasConsultaResponse,
    summary="Consultar reservas com paginação",
)
def consultar_reservas(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(
        12,
        ge=1,
        le=100,
    ),
    busca: str = Query(
        "",
        max_length=100,
    ),
    status: Literal[
        "todos",
        "ativa",
        "expirada",
        "cancelada",
        "convertida",
    ] = "todos",
    ordenar: Literal[
        "id",
        "data_inicio",
        "data_fim",
        "veiculo",
        "cliente",
    ] = "data_inicio",
    direcao: Literal[
        "asc",
        "desc",
    ] = "asc",
    container: Container = Depends(
        get_container
    ),
    _usuario=Depends(
        exigir_permissao(
            Permissao.RESERVAS_LER
        )
    ),
):
    resultado = (
        container.reserva_service
        .consultar(
            pagina=pagina,
            por_pagina=por_pagina,
            busca=busca,
            status=status,
            ordenar=ordenar,
            direcao=direcao,
        )
    )

    return resposta_consulta(
        resultado,
        pagina,
        por_pagina,
    )


@router.get(
    "/me",
    response_model=list[
        ReservaResponse
    ],
    summary="Listar minhas reservas",
)
def minhas_reservas(
    cliente=Depends(
        get_cliente_atual
    ),
    container: Container = Depends(
        get_container
    ),
    _usuario=Depends(
        exigir_permissao(
            Permissao.RESERVAS_PROPRIAS_LER
        )
    ),
):
    return [
        transformar_reserva(
            reserva
        )
        for reserva
        in (
            container.reserva_service
            .listar_do_cliente(
                cliente
            )
        )
    ]


@router.get(
    "/me/consulta",
    response_model=ReservasConsultaResponse,
    summary="Consultar minhas reservas",
)
def consultar_minhas_reservas(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(
        12,
        ge=1,
        le=100,
    ),
    busca: str = Query(
        "",
        max_length=100,
    ),
    status: Literal[
        "todos",
        "ativa",
        "expirada",
        "cancelada",
        "convertida",
    ] = "todos",
    ordenar: Literal[
        "id",
        "data_inicio",
        "data_fim",
        "veiculo",
    ] = "data_inicio",
    direcao: Literal[
        "asc",
        "desc",
    ] = "asc",
    cliente=Depends(
        get_cliente_atual
    ),
    container: Container = Depends(
        get_container
    ),
    _usuario=Depends(
        exigir_permissao(
            Permissao.RESERVAS_PROPRIAS_LER
        )
    ),
):
    resultado = (
        container.reserva_service
        .consultar(
            pagina=pagina,
            por_pagina=por_pagina,
            busca=busca,
            status=status,
            ordenar=ordenar,
            direcao=direcao,
            cliente_id=cliente.id,
        )
    )

    return resposta_consulta(
        resultado,
        pagina,
        por_pagina,
    )


@router.patch(
    "/me/{id_reserva}/cancelar",
    response_model=ReservaResponse,
    summary="Cancelar minha reserva",
)
def cancelar_minha_reserva(
    id_reserva: int,
    request: Request,
    cliente=Depends(
        get_cliente_atual
    ),
    container: Container = Depends(
        get_container
    ),
    _usuario=Depends(
        exigir_permissao(
            Permissao.RESERVAS_CANCELAR
        )
    ),
):
    reserva = (
        container.reserva_service
        .cancelar_do_cliente(
            id_reserva,
            cliente,
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=cliente,
        acao="reserva.cancelada",
        recurso="reserva",
        recurso_id=reserva.id,
        campos_alterados=(
            "status",
        ),
    )

    return transformar_reserva(
        reserva
    )


@router.patch(
    "/{id_reserva}/cancelar",
    response_model=ReservaResponse,
    summary="Cancelar reserva como administrador",
)
def cancelar_reserva_admin(
    id_reserva: int,
    request: Request,
    container: Container = Depends(
        get_container
    ),
    usuario=Depends(
        exigir_permissao(
            Permissao.RESERVAS_LER
        )
    ),
    _cancelar=Depends(
        exigir_permissao(
            Permissao.RESERVAS_CANCELAR
        )
    ),
):
    reserva = (
        container.reserva_service
        .cancelar_admin(
            id_reserva
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario,
        acao="reserva.cancelada",
        recurso="reserva",
        recurso_id=reserva.id,
        campos_alterados=(
            "status",
        ),
    )

    return transformar_reserva(
        reserva
    )
