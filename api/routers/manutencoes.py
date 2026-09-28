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
    get_container,
)

from api.schemas.consultas import ManutencoesConsultaResponse
from api.schemas.manutencoes import (
    ManutencaoCreate,
    ManutencaoFinalizar,
    ManutencaoResponse,
    ManutencaoUpdate,
)

from modulos.permissoes import (
    Permissao,
)

from modulos.container import Container


router = APIRouter(
    prefix="/manutencoes",
    tags=["Manutenções"],
)


# ================================================================
# SERIALIZAÇÃO
# ================================================================


def transformar_manutencao(
    manutencao,
):
    return ManutencaoResponse(
        id=manutencao.id,

        veiculo_id=(
            manutencao.veiculo_id
        ),

        motivo=manutencao.motivo,

        quilometragem=(
            manutencao.quilometragem
        ),

        custo=manutencao.custo,

        data_inicio=(
            manutencao.data_inicio
        ),

        data_fim=(
            manutencao.data_fim
        ),

        status=manutencao.status,

        tipo=manutencao.tipo,

        prioridade=(
            manutencao.prioridade
        ),

        fornecedor=(
            manutencao.fornecedor
        ),

        custo_estimado=(
            manutencao.custo_estimado
        ),

        data_prevista=(
            manutencao.data_prevista
        ),

        observacoes=(
            manutencao.observacoes
        ),

        atrasada=manutencao.atrasada,
    )


# ================================================================
# LISTAR TODAS
# ================================================================


@router.get(
    "",
    response_model=list[
        ManutencaoResponse
    ],
    summary="Listar manutenções",
    description=(
        "Retorna todas as manutenções registradas "
        "na locadora, incluindo manutenções ativas "
        "e finalizadas. Esta operação é restrita "
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
def listar_manutencoes(
    container: Container = Depends(
        get_container
    ),

    usuario_admin=Depends(
        exigir_permissao(
            Permissao.MANUTENCOES_LER
        )
    ),
):
    manutencoes = (
        container.manutencao_service
        .listar_manutencoes()
    )

    return [
        transformar_manutencao(
            manutencao
        )
        for manutencao
        in manutencoes
    ]


# ================================================================
# CONSULTA PAGINADA
# ================================================================


@router.get(
    "/consulta",
    response_model=ManutencoesConsultaResponse,
    summary="Consultar manutenções com paginação",
)
def consultar_manutencoes(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(12, ge=1, le=100),
    busca: str = Query("", max_length=100),
    status: Literal["todos", "ativa", "finalizada"] = "todos",
    tipo: Literal[
        "todos",
        "preventiva",
        "corretiva",
    ] = "todos",
    prioridade: Literal[
        "todos",
        "baixa",
        "media",
        "alta",
    ] = "todos",
    ordenar: Literal[
        "id",
        "data_inicio",
        "data_prevista",
        "custo",
        "custo_estimado",
        "quilometragem",
    ] = "id",
    direcao: Literal["asc", "desc"] = "desc",
    container: Container = Depends(get_container),
    _usuario_admin=Depends(exigir_permissao(Permissao.MANUTENCOES_LER)),
):
    resultado = container.manutencao_service.consultar_manutencoes(
        pagina=pagina,
        por_pagina=por_pagina,
        busca=busca,
        status=status,
        tipo=tipo,
        prioridade=prioridade,
        ordenar=ordenar,
        direcao=direcao,
    )

    return {
        "items": [transformar_manutencao(item) for item in resultado.items],
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total": resultado.total,
        "total_paginas": (resultado.total + por_pagina - 1) // por_pagina,
        "resumo": resultado.resumo,
    }


# ================================================================
# LISTAR ATIVAS
# ================================================================


@router.get(
    "/ativas",
    response_model=list[
        ManutencaoResponse
    ],
    summary="Listar manutenções ativas",
    description=(
        "Retorna apenas as manutenções que ainda "
        "estão em andamento. Esta operação é "
        "restrita a administradores."
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
def listar_manutencoes_ativas(
    container: Container = Depends(
        get_container
    ),

    usuario_admin=Depends(
        exigir_permissao(
            Permissao.MANUTENCOES_LER
        )
    ),
):
    manutencoes = (
        container.manutencao_service
        .listar_ativas()
    )

    return [
        transformar_manutencao(
            manutencao
        )
        for manutencao
        in manutencoes
    ]


# ================================================================
# HISTÓRICO POR VEÍCULO
# ================================================================


@router.get(
    "/veiculo/{id_veiculo}",
    response_model=list[
        ManutencaoResponse
    ],
    summary="Listar manutenções de um veículo",
    description=(
        "Retorna o histórico de manutenções associado "
        "ao veículo informado. Esta operação é "
        "restrita a administradores."
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
        422: {
            "description": (
                "Identificador enviado não passou "
                "pela validação."
            ),
        },
    },
)
def listar_manutencoes_do_veiculo(
    id_veiculo: int,

    container: Container = Depends(
        get_container
    ),

    usuario_admin=Depends(
        exigir_permissao(
            Permissao.MANUTENCOES_LER
        )
    ),
):
    manutencoes = (
        container.manutencao_service
        .listar_por_veiculo(
            id_veiculo
        )
    )

    return [
        transformar_manutencao(
            manutencao
        )
        for manutencao
        in manutencoes
    ]


# ================================================================
# ABRIR MANUTENÇÃO
# ================================================================


@router.post(
    "",
    status_code=201,
    response_model=ManutencaoResponse,
    summary="Abrir manutenção",
    description=(
        "Registra uma nova manutenção para um veículo. "
        "O veículo precisa existir e estar em condição "
        "válida para entrar em manutenção. Esta operação "
        "é restrita a administradores."
    ),
    responses={
        400: {
            "description": (
                "A manutenção não pode ser aberta "
                "devido a uma regra de negócio, como "
                "já existir uma manutenção ativa."
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
                "para administradores."
            ),
        },
        404: {
            "description": (
                "Veículo não encontrado."
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
def abrir_manutencao(
    request: Request,
    dados: ManutencaoCreate,

    container: Container = Depends(
        get_container
    ),

    usuario_admin=Depends(
        exigir_permissao(
            Permissao.MANUTENCOES_CRIAR
        )
    ),
):
    manutencao = (
        container.manutencao_service
        .abrir(
            id_veiculo=(
                dados.id_veiculo
            ),

            motivo=dados.motivo,
            tipo=dados.tipo,
            prioridade=dados.prioridade,
            fornecedor=dados.fornecedor,
            custo_estimado=(
                dados.custo_estimado
            ),
            data_prevista=(
                dados.data_prevista
            ),
            observacoes=dados.observacoes,
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="manutencao.aberta",
        recurso="manutencao",
        recurso_id=manutencao.id,
        campos_alterados=(
            "status",
            "motivo",
            "tipo",
            "prioridade",
            "fornecedor",
            "custo_estimado",
            "data_prevista",
            "observacoes",
        ),
    )

    return transformar_manutencao(
        manutencao
    )


# ================================================================
# EDITAR MANUTENÇÃO ATIVA
# ================================================================


@router.patch(
    "/{id_manutencao}",
    response_model=ManutencaoResponse,
    summary="Editar manutenção ativa",
    description=(
        "Atualiza os detalhes operacionais de uma "
        "manutenção que ainda está em andamento."
    ),
    responses={
        400: {
            "description": (
                "A alteração viola uma regra "
                "de negócio."
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
                "Usuário sem permissão para editar "
                "manutenções."
            ),
        },
        404: {
            "description": (
                "Manutenção não encontrada."
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
def atualizar_manutencao(
    request: Request,
    id_manutencao: int,
    dados: ManutencaoUpdate,

    container: Container = Depends(
        get_container
    ),

    usuario_admin=Depends(
        exigir_permissao(
            Permissao.MANUTENCOES_EDITAR
        )
    ),
):
    alteracoes = dados.model_dump(
        exclude_unset=True
    )

    manutencao = (
        container.manutencao_service
        .atualizar(
            id_manutencao=(
                id_manutencao
            ),
            alteracoes=alteracoes,
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="manutencao.atualizada",
        recurso="manutencao",
        recurso_id=manutencao.id,
        campos_alterados=tuple(
            sorted(
                alteracoes
            )
        ),
    )

    return transformar_manutencao(
        manutencao
    )


# ================================================================
# FINALIZAR MANUTENÇÃO
# ================================================================


@router.patch(
    "/{id_veiculo}/finalizar",
    response_model=ManutencaoResponse,
    summary="Finalizar manutenção",
    description=(
        "Finaliza a manutenção ativa de um veículo, "
        "registrando seu custo e liberando o veículo "
        "conforme as regras da aplicação. Esta operação "
        "é restrita a administradores."
    ),
    responses={
        400: {
            "description": (
                "A finalização viola uma regra "
                "de negócio."
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
                "para administradores."
            ),
        },
        404: {
            "description": (
                "Veículo não encontrado ou o veículo "
                "não possui manutenção ativa."
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
def finalizar_manutencao(
    request: Request,
    id_veiculo: int,

    dados: ManutencaoFinalizar,

    container: Container = Depends(
        get_container
    ),

    usuario_admin=Depends(
        exigir_permissao(
            Permissao.MANUTENCOES_FINALIZAR
        )
    ),
):
    manutencao = (
        container.manutencao_service
        .finalizar(
            id_veiculo=id_veiculo,
            custo=dados.custo,
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="manutencao.finalizada",
        recurso="manutencao",
        recurso_id=manutencao.id,
        campos_alterados=(
            "status",
            "custo",
            "data_fim",
        ),
    )

    return transformar_manutencao(
        manutencao
    )
