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

from api.schemas.alugueis import (
    AluguelCreate,
    AluguelResponse,
    DevolucaoCreate,
    DevolucaoResponse,
    PagamentoResponse,
)
from api.schemas.consultas import AlugueisConsultaResponse

from modulos.permissoes import (
    Permissao,
)

from modulos.container import Container


router = APIRouter(
    prefix="/alugueis",
    tags=["Aluguéis"],
)


# ================================================================
# TRANSFORMAÇÕES
# ================================================================


def transformar_aluguel(
    aluguel,
):
    return AluguelResponse(
        id=aluguel.id,

        cliente_id=(
            aluguel.cliente_id
        ),

        cliente_usuario=(
            aluguel.cliente_usuario
        ),

        cliente_nome=(
            aluguel.cliente_nome
        ),

        veiculo_id=(
            aluguel.veiculo_id
        ),

        veiculo_tipo=(
            aluguel.veiculo_tipo
        ),

        veiculo_modelo=(
            aluguel.veiculo_modelo
        ),

        dias=aluguel.dias,
        status=aluguel.status,

        km=aluguel.km,

        pagamento=(
            aluguel.pagamento
        ),

        valor=aluguel.valor,

        data_inicio=(
            aluguel.data_inicio
        ),

        data_prevista=(
            aluguel.data_prevista
        ),

        data_fim=(
            aluguel.data_fim
        ),

        dias_atraso=(
            aluguel.dias_atraso
        ),

        multa=aluguel.multa,
    )


def transformar_pagamento(
    pagamento,
):
    return PagamentoResponse(
        valor_final=(
            pagamento[
                "valor_final"
            ]
        ),

        forma=(
            pagamento[
                "forma"
            ]
        ),

        parcelas=(
            pagamento[
                "parcelas"
            ]
        ),

        valor_parcela=(
            pagamento[
                "valor_parcela"
            ]
        ),
    )


# ================================================================
# ADMIN - TODOS OS ALUGUÉIS
# ================================================================


@router.get(
    "",
    response_model=list[
        AluguelResponse
    ],
    summary="Listar todos os aluguéis",
    description=(
        "Retorna todos os aluguéis registrados "
        "na locadora, incluindo ativos e finalizados. "
        "Esta operação é restrita a administradores."
    ),
    responses={
        401: {
            "description": (
                "Autenticação necessária ou "
                "token inválido."
            ),
        },
        403: {
            "description": (
                "Acesso permitido apenas "
                "para administradores."
            ),
        },
    },
)
def listar_alugueis(
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.ALUGUEIS_LER
        )
    ),
):
    alugueis = (
        container.aluguel_service
        .listar_alugueis()
    )

    return [
        transformar_aluguel(
            aluguel
        )
        for aluguel
        in alugueis
    ]


# ================================================================
# ADMIN - CONSULTA PAGINADA
# ================================================================


@router.get(
    "/consulta",
    response_model=AlugueisConsultaResponse,
    summary="Consultar aluguéis com paginação",
)
def consultar_alugueis(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(12, ge=1, le=100),
    busca: str = Query("", max_length=100),
    status: Literal["todos", "ativo", "finalizado"] = "todos",
    ordenar: Literal[
        "id",
        "data_inicio",
        "data_prevista",
        "valor",
    ] = "id",
    direcao: Literal["asc", "desc"] = "desc",
    container: Container = Depends(get_container),
    _usuario_admin=Depends(exigir_permissao(Permissao.ALUGUEIS_LER)),
):
    resultado = container.aluguel_service.consultar_alugueis(
        pagina=pagina,
        por_pagina=por_pagina,
        busca=busca,
        status=status,
        ordenar=ordenar,
        direcao=direcao,
    )

    return {
        "items": [transformar_aluguel(item) for item in resultado.items],
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total": resultado.total,
        "total_paginas": (resultado.total + por_pagina - 1) // por_pagina,
        "resumo": resultado.resumo,
    }


# ================================================================
# ADMIN - ALUGUÉIS ATIVOS
# ================================================================


@router.get(
    "/ativos",
    response_model=list[
        AluguelResponse
    ],
    summary="Listar aluguéis ativos",
    description=(
        "Retorna apenas os aluguéis que ainda "
        "estão ativos. Esta operação é restrita "
        "a administradores."
    ),
    responses={
        401: {
            "description": (
                "Autenticação necessária ou "
                "token inválido."
            ),
        },
        403: {
            "description": (
                "Acesso permitido apenas "
                "para administradores."
            ),
        },
    },
)
def listar_alugueis_ativos(
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.ALUGUEIS_LER
        )
    ),
):
    alugueis = (
        container.aluguel_service
        .listar_ativos()
    )

    return [
        transformar_aluguel(
            aluguel
        )
        for aluguel
        in alugueis
    ]


# ================================================================
# CLIENTE - CRIAR ALUGUEL
# ================================================================


@router.post(
    "",
    status_code=201,
    response_model=AluguelResponse,
    summary="Criar aluguel",
    description=(
        "Cria um novo aluguel para o cliente "
        "autenticado. O cliente é identificado "
        "pelo token JWT e não precisa enviar seu ID "
        "na requisição."
    ),
    responses={
        400: {
            "description": (
                "O aluguel não pode ser criado "
                "devido a uma regra de negócio."
            ),
        },
        401: {
            "description": (
                "Autenticação necessária ou "
                "token inválido."
            ),
        },
        403: {
            "description": (
                "Acesso permitido apenas "
                "para clientes."
            ),
        },
        404: {
            "description": (
                "Veículo não encontrado ou "
                "perfil do cliente indisponível."
            ),
        },
        422: {
            "description": (
                "Os dados enviados não passaram "
                "pela validação."
            ),
        },
    },
)
def criar_aluguel(
    request: Request,
    dados: AluguelCreate,

    cliente=Depends(
        get_cliente_atual
    ),

    container: Container = Depends(
        get_container
    ),

    _usuario_autorizado=Depends(
        exigir_permissao(
            Permissao.ALUGUEIS_CRIAR
        )
    ),
):
    aluguel = (
        container.aluguel_service
        .alugar(
            cliente=cliente,

            id_veiculo=(
                dados.id_veiculo
            ),

            dias=dados.dias,

            anos_habilitacao=(
                dados.anos_habilitacao
            ),
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=cliente,
        acao="aluguel.criado",
        recurso="aluguel",
        recurso_id=aluguel.id,
        campos_alterados=(
            "status",
            "veiculo_id",
            "dias",
        ),
    )

    return transformar_aluguel(
        aluguel
    )


# ================================================================
# CLIENTE - MEUS ALUGUÉIS
# ================================================================


@router.get(
    "/me/consulta",
    response_model=AlugueisConsultaResponse,
    summary="Consultar meus aluguéis com paginação",
)
def consultar_meus_alugueis(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(12, ge=1, le=100),
    busca: str = Query("", max_length=100),
    status: Literal["todos", "ativo", "finalizado"] = "todos",
    ordenar: Literal[
        "id",
        "data_inicio",
        "data_prevista",
        "valor",
    ] = "id",
    direcao: Literal["asc", "desc"] = "desc",
    cliente=Depends(get_cliente_atual),
    container: Container = Depends(get_container),
    _usuario_autorizado=Depends(
        exigir_permissao(Permissao.ALUGUEIS_PROPRIOS_LER)
    ),
):
    resultado = container.aluguel_service.consultar_alugueis(
        pagina=pagina,
        por_pagina=por_pagina,
        busca=busca,
        status=status,
        ordenar=ordenar,
        direcao=direcao,
        cliente_id=cliente.id,
    )

    return {
        "items": [transformar_aluguel(item) for item in resultado.items],
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total": resultado.total,
        "total_paginas": (resultado.total + por_pagina - 1) // por_pagina,
        "resumo": resultado.resumo,
    }


@router.get(
    "/me",
    response_model=list[
        AluguelResponse
    ],
    summary="Listar meus aluguéis",
    description=(
        "Retorna o histórico de aluguéis do cliente "
        "autenticado. O cliente é identificado "
        "automaticamente pelo token JWT."
    ),
    responses={
        401: {
            "description": (
                "Autenticação necessária ou "
                "token inválido."
            ),
        },
        403: {
            "description": (
                "Acesso permitido apenas "
                "para clientes."
            ),
        },
        404: {
            "description": (
                "Perfil de cliente não encontrado."
            ),
        },
    },
)
def meus_alugueis(
    cliente=Depends(
        get_cliente_atual
    ),

    container: Container = Depends(
        get_container
    ),

    _usuario_autorizado=Depends(
        exigir_permissao(
            Permissao.ALUGUEIS_PROPRIOS_LER
        )
    ),
):
    alugueis = (
        container.aluguel_service
        .listar_do_cliente(
            cliente
        )
    )

    return [
        transformar_aluguel(
            aluguel
        )
        for aluguel
        in alugueis
    ]


# ================================================================
# CLIENTE - DEVOLUÇÃO
# ================================================================


@router.patch(
    "/{id_veiculo}/devolver",
    response_model=DevolucaoResponse,
    summary="Devolver veículo",
    description=(
        "Finaliza o aluguel ativo do veículo informado "
        "para o cliente autenticado. A operação registra "
        "a quilometragem, calcula possíveis atrasos e multa, "
        "processa a forma de pagamento e libera o veículo."
    ),
    responses={
        400: {
            "description": (
                "A devolução viola uma regra de negócio, "
                "como dados de pagamento inválidos ou "
                "veículo não pertencente ao cliente."
            ),
        },
        401: {
            "description": (
                "Autenticação necessária ou "
                "token inválido."
            ),
        },
        403: {
            "description": (
                "Acesso permitido apenas "
                "para clientes."
            ),
        },
        404: {
            "description": (
                "Veículo, aluguel ativo ou perfil "
                "de cliente não encontrado."
            ),
        },
        422: {
            "description": (
                "Os dados enviados não passaram "
                "pela validação."
            ),
        },
    },
)
def devolver_veiculo(
    request: Request,
    id_veiculo: int,

    dados: DevolucaoCreate,

    cliente=Depends(
        get_cliente_atual
    ),

    container: Container = Depends(
        get_container
    ),

    _usuario_autorizado=Depends(
        exigir_permissao(
            Permissao.ALUGUEIS_DEVOLVER
        )
    ),
):
    resultado_devolucao = (
        container.aluguel_service
        .devolver(
            cliente=cliente,

            id_veiculo=id_veiculo,

            km=dados.km,

            forma_pagamento=(
                dados.forma_pagamento
            ),

            parcelas=(
                dados.parcelas
            ),
        )
    )

    aluguel = (
        resultado_devolucao[
            "aluguel"
        ]
    )

    pagamento = (
        resultado_devolucao[
            "pagamento"
        ]
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=cliente,
        acao="aluguel.devolvido",
        recurso="aluguel",
        recurso_id=aluguel.id,
        campos_alterados=(
            "status",
            "km",
            "pagamento",
            "data_fim",
            "multa",
        ),
    )

    return DevolucaoResponse(
        aluguel=(
            transformar_aluguel(
                aluguel
            )
        ),

        veiculo_id=(
            aluguel.veiculo_id
        ),

        valor_aluguel=(
            resultado_devolucao[
                "valor_aluguel"
            ]
        ),

        dias_atraso=(
            resultado_devolucao[
                "dias_atraso"
            ]
        ),

        multa=(
            resultado_devolucao[
                "multa"
            ]
        ),

        valor_inicial=(
            resultado_devolucao[
                "valor_inicial"
            ]
        ),

        pagamento=(
            transformar_pagamento(
                pagamento
            )
        ),
    )
