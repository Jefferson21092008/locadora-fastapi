from fastapi import (
    APIRouter,
    Depends,
)

from api.dependencias import (
    get_admin_atual,
    get_container,
)

from api.erros import (
    recurso_nao_encontrado,
)

from api.schemas.veiculos import (
    VeiculoCreate,
    VeiculoResponse,
    VeiculoUpdate,
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
    dados: VeiculoCreate,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        get_admin_atual
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
    id_veiculo: int,
    dados: VeiculoUpdate,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        get_admin_atual
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
    id_veiculo: int,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        get_admin_atual
    ),
):
    veiculo = (
        container.veiculo_service
        .desativar(
            id_veiculo
        )
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
    id_veiculo: int,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        get_admin_atual
    ),
):
    veiculo = (
        container.veiculo_service
        .reativar(
            id_veiculo
        )
    )

    return transformar_veiculo(
        veiculo
    )
