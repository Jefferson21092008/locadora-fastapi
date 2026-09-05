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

from api.schemas.clientes import (
    ClienteCreate,
    ClienteResponse,
)

from modulos.container import Container


router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
)


# ================================================================
# TRANSFORMAÇÃO
# ================================================================


def transformar_cliente(
    cliente,
):
    return ClienteResponse(
        id=cliente.id,
        nome=cliente.nome,
        usuario=cliente.usuario,
        email=cliente.email,
        ativo=cliente.ativo,
    )


# ================================================================
# LISTAGEM
# ================================================================


@router.get(
    "",
    response_model=list[
        ClienteResponse
    ],
    summary="Listar clientes",
    description=(
        "Retorna todos os clientes cadastrados "
        "na locadora. Esta operação é restrita "
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
def listar_clientes(
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        get_admin_atual
    ),
):
    clientes = (
        container.cliente_service
        .listar_clientes()
    )

    return [
        transformar_cliente(
            cliente
        )
        for cliente
        in clientes
    ]


# ================================================================
# BUSCA
# ================================================================


@router.get(
    "/{id_cliente}",
    response_model=ClienteResponse,
    summary="Buscar cliente por ID",
    description=(
        "Retorna os dados de um cliente específico "
        "a partir do seu identificador. Esta operação "
        "é restrita a administradores."
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
        404: {
            "description": (
                "Cliente não encontrado."
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
def buscar_cliente(
    id_cliente: int,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        get_admin_atual
    ),
):
    cliente = (
        container.cliente_service
        .buscar_por_id(
            id_cliente
        )
    )

    if cliente is None:
        recurso_nao_encontrado(
            "Cliente não encontrado."
        )

    return transformar_cliente(
        cliente
    )


# ================================================================
# CRIAÇÃO
# ================================================================


@router.post(
    "",
    status_code=201,
    response_model=ClienteResponse,
    summary="Cadastrar cliente",
    description=(
        "Cria uma nova conta de cliente e o respectivo "
        "usuário de autenticação. Esta rota é pública "
        "e pode ser utilizada para cadastro."
    ),
    responses={
        400: {
            "description": (
                "Não foi possível criar a conta por "
                "uma regra de negócio, como usuário "
                "ou e-mail já cadastrado."
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
def criar_cliente(
    dados: ClienteCreate,
    container: Container = Depends(
        get_container
    ),
):
    cliente = (
        container.cliente_service
        .criar_conta(
            nome=dados.nome,
            usuario=dados.usuario,
            email=dados.email,
            senha=dados.senha,
        )
    )

    return transformar_cliente(
        cliente
    )


# ================================================================
# DESATIVAÇÃO
# ================================================================


@router.patch(
    "/{id_cliente}/desativar",
    response_model=ClienteResponse,
    summary="Desativar cliente",
    description=(
        "Desativa o perfil do cliente e sua conta "
        "de autenticação. Um cliente com aluguel ativo "
        "não pode ser desativado. Operação restrita "
        "a administradores."
    ),
    responses={
        400: {
            "description": (
                "A desativação viola uma regra de negócio, "
                "como a existência de um aluguel ativo."
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
                "Cliente não encontrado."
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
def desativar_cliente(
    id_cliente: int,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        get_admin_atual
    ),
):
    cliente = (
        container.cliente_service
        .desativar(
            id_cliente
        )
    )

    return transformar_cliente(
        cliente
    )


# ================================================================
# REATIVAÇÃO
# ================================================================


@router.patch(
    "/{id_cliente}/reativar",
    response_model=ClienteResponse,
    summary="Reativar cliente",
    description=(
        "Reativa o perfil do cliente e sua conta "
        "de autenticação. Esta operação é restrita "
        "a administradores."
    ),
    responses={
        400: {
            "description": (
                "A reativação viola uma regra "
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
                "Cliente não encontrado."
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
def reativar_cliente(
    id_cliente: int,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        get_admin_atual
    ),
):
    cliente = (
        container.cliente_service
        .reativar(
            id_cliente
        )
    )

    return transformar_cliente(
        cliente
    )
