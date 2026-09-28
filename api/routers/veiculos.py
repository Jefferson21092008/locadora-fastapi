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

from api.erros import (
    recurso_nao_encontrado,
)

from api.schemas.consultas import VeiculosConsultaResponse
from api.schemas.veiculos import (
    VeiculoCreate,
    VeiculoResponse,
    VeiculoUpdate,
)

from modulos.permissoes import (
    Permissao,
)

from modulos.container import (
    Container,
)


router = APIRouter(
    prefix="/veiculos",
    tags=["Veículos"],
)


# ================================================================
# TRANSFORMAÇÃO
# ================================================================


def transformar_veiculo(
    veiculo,
):
    return VeiculoResponse(
        id=veiculo.id,
        tipo=veiculo.TIPO,
        modelo=veiculo.modelo,
        ano=veiculo.ano,
        diaria=veiculo.diaria,
        preco_km=veiculo.preco_km,
        quilometragem=(
            veiculo.quilometragem
        ),
        status=veiculo.status.value,
        ativo=veiculo.ativo,
    )


# ================================================================
# LISTAGEM
# ================================================================


@router.get(
    "",
    response_model=list[
        VeiculoResponse
    ],
    summary="Listar veículos",
    description=(
        "Retorna todos os veículos cadastrados "
        "na locadora, incluindo ativos e desativados. "
        "Esta rota é pública."
    ),
)
def listar_veiculos(
    container: Container = Depends(
        get_container
    ),
):
    veiculos = (
        container.veiculo_service
        .listar_todos()
    )

    return [
        transformar_veiculo(
            veiculo
        )
        for veiculo in veiculos
    ]


# ================================================================
# CONSULTA PAGINADA
# ================================================================


@router.get(
    "/consulta",
    response_model=VeiculosConsultaResponse,
    summary="Consultar veículos com paginação",
)
def consultar_veiculos(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(12, ge=1, le=100),
    busca: str = Query("", max_length=100),
    status: Literal[
        "todos",
        "disponivel",
        "alugado",
        "manutencao",
        "desativado",
    ] = "todos",
    ordenar: Literal[
        "id",
        "modelo",
        "ano",
        "diaria",
        "quilometragem",
    ] = "modelo",
    direcao: Literal["asc", "desc"] = "asc",
    container: Container = Depends(get_container),
):
    resultado = container.veiculo_service.consultar_veiculos(
        pagina=pagina,
        por_pagina=por_pagina,
        busca=busca,
        status=status,
        ordenar=ordenar,
        direcao=direcao,
    )

    return {
        "items": [transformar_veiculo(item) for item in resultado.items],
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total": resultado.total,
        "total_paginas": (resultado.total + por_pagina - 1) // por_pagina,
        "resumo": resultado.resumo,
    }


# ================================================================
# BUSCA
# ================================================================


@router.get(
    "/{id_veiculo}",
    response_model=VeiculoResponse,
    summary="Buscar veículo por ID",
    description=(
        "Retorna os dados de um veículo específico "
        "a partir do seu identificador. "
        "Esta rota é pública."
    ),
    responses={
        404: {
            "description": (
                "Veículo não encontrado."
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
def buscar_veiculo(
    id_veiculo: int,
    container: Container = Depends(
        get_container
    ),
):
    veiculo = (
        container.veiculo_service
        .buscar_por_id(
            id_veiculo
        )
    )

    if veiculo is None:
        recurso_nao_encontrado(
            "Veículo não encontrado."
        )

    return transformar_veiculo(
        veiculo
    )


# ================================================================
# CADASTRO
# ================================================================


@router.post(
    "",
    status_code=201,
    response_model=VeiculoResponse,
    summary="Cadastrar veículo",
    description=(
        "Cadastra um novo veículo na frota da locadora. "
        "A operação é restrita a administradores."
    ),
    responses={
        400: {
            "description": (
                "Os dados violam uma regra de negócio "
                "do cadastro de veículos."
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
        422: {
            "description": (
                "Os dados enviados não passaram "
                "pela validação."
            ),
        },
    },
)
def cadastrar_veiculo(
    request: Request,
    dados: VeiculoCreate,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.VEICULOS_CRIAR
        )
    ),
):
    veiculo = (
        container.veiculo_service
        .cadastrar(
            tipo=dados.tipo,
            modelo=dados.modelo,
            ano=dados.ano,
            diaria=dados.diaria,
            preco_km=dados.preco_km,
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="veiculo.cadastrado",
        recurso="veiculo",
        recurso_id=veiculo.id,
        campos_alterados=(
            "tipo",
            "modelo",
            "ano",
            "diaria",
            "preco_km",
        ),
    )

    return transformar_veiculo(
        veiculo
    )


# ================================================================
# EDIÇÃO
# ================================================================


@router.patch(
    "/{id_veiculo}",
    response_model=VeiculoResponse,
    summary="Editar veículo",
    description=(
        "Atualiza os dados editáveis de um veículo "
        "já cadastrado. Apenas os campos enviados "
        "são alterados. Operação restrita "
        "a administradores."
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
def editar_veiculo(
    request: Request,
    id_veiculo: int,
    dados: VeiculoUpdate,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.VEICULOS_EDITAR
        )
    ),
):
    veiculo = (
        container.veiculo_service
        .editar(
            id_veiculo=id_veiculo,
            modelo=dados.modelo,
            ano=dados.ano,
            diaria=dados.diaria,
            preco_km=dados.preco_km,
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="veiculo.editado",
        recurso="veiculo",
        recurso_id=veiculo.id,
        campos_alterados=sorted(
            dados.model_fields_set
        ),
    )

    return transformar_veiculo(
        veiculo
    )


# ================================================================
# DESATIVAÇÃO
# ================================================================


@router.patch(
    "/{id_veiculo}/desativar",
    response_model=VeiculoResponse,
    summary="Desativar veículo",
    description=(
        "Desativa um veículo da frota. "
        "A operação pode falhar caso o veículo "
        "não esteja em uma condição válida para "
        "desativação. Restrita a administradores."
    ),
    responses={
        400: {
            "description": (
                "O veículo não pode ser desativado "
                "no estado atual."
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
                "Identificador enviado não passou "
                "pela validação."
            ),
        },
    },
)
def desativar_veiculo(
    request: Request,
    id_veiculo: int,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.VEICULOS_GERENCIAR_STATUS
        )
    ),
):
    veiculo = (
        container.veiculo_service
        .desativar(
            id_veiculo
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="veiculo.desativado",
        recurso="veiculo",
        recurso_id=veiculo.id,
        campos_alterados=(
            "ativo",
            "status",
        ),
    )

    return transformar_veiculo(
        veiculo
    )


# ================================================================
# REATIVAÇÃO
# ================================================================


@router.patch(
    "/{id_veiculo}/reativar",
    response_model=VeiculoResponse,
    summary="Reativar veículo",
    description=(
        "Reativa um veículo anteriormente desativado. "
        "Esta operação é restrita a administradores."
    ),
    responses={
        400: {
            "description": (
                "O veículo não pode ser reativado "
                "no estado atual."
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
                "Identificador enviado não passou "
                "pela validação."
            ),
        },
    },
)
def reativar_veiculo(
    request: Request,
    id_veiculo: int,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.VEICULOS_GERENCIAR_STATUS
        )
    ),
):
    veiculo = (
        container.veiculo_service
        .reativar(
            id_veiculo
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="veiculo.reativado",
        recurso="veiculo",
        recurso_id=veiculo.id,
        campos_alterados=(
            "ativo",
            "status",
        ),
    )

    return transformar_veiculo(
        veiculo
    )
