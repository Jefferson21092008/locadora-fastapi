from functools import lru_cache

from fastapi import Depends

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from api.erros import (
    acesso_negado,
    nao_autorizado,
    recurso_nao_encontrado,
)

from api.seguranca import (
    decodificar_token,
)

from modulos.container import (
    Container,
)


# ================================================================
# CONTAINER
# ================================================================


@lru_cache
def get_container():
    return Container()


# ================================================================
# BEARER TOKEN
# ================================================================


bearer_scheme = HTTPBearer(
    auto_error=False
)


# ================================================================
# USUÁRIO AUTENTICADO
# ================================================================


def get_usuario_atual(
    credenciais: (
        HTTPAuthorizationCredentials
        | None
    ) = Depends(
        bearer_scheme
    ),

    container: Container = Depends(
        get_container
    ),
):
    if credenciais is None:
        nao_autorizado(
            "Autenticação necessária."
        )

    payload = decodificar_token(
        token=credenciais.credentials,
        secret=(
            container.config
            .jwt_secret
        ),
    )

    if payload is None:
        nao_autorizado(
            "Token inválido ou expirado."
        )

    id_usuario = payload.get(
        "sub"
    )

    if id_usuario is None:
        nao_autorizado(
            "Token inválido."
        )

    try:
        id_usuario = int(
            id_usuario
        )

    except (
        TypeError,
        ValueError,
    ):
        nao_autorizado(
            "Token inválido."
        )

    usuario = (
        container.auth_service
        .buscar_por_id(
            id_usuario
        )
    )

    if (
        usuario is None
        or not usuario.ativo
    ):
        nao_autorizado(
            "Usuário inválido ou inativo."
        )

    return usuario


# ================================================================
# ADMIN
# ================================================================


def get_admin_atual(
    usuario=Depends(
        get_usuario_atual
    ),
):
    if (
        usuario.role.value
        != "admin"
    ):
        acesso_negado(
            (
                "Acesso permitido "
                "apenas para "
                "administradores."
            )
        )

    return usuario


# ================================================================
# CLIENTE
# ================================================================


def get_cliente_atual(
    usuario=Depends(
        get_usuario_atual
    ),

    container: Container = Depends(
        get_container
    ),
):
    if (
        usuario.role.value
        != "cliente"
    ):
        acesso_negado(
            (
                "Acesso permitido "
                "apenas para clientes."
            )
        )

    cliente = (
        container.cliente_service
        .buscar_por_usuario_id(
            usuario.id
        )
    )

    if cliente is None:
        recurso_nao_encontrado(
            (
                "Cliente vinculado "
                "ao usuário não "
                "foi encontrado."
            )
        )

    if not cliente.ativo:
        acesso_negado(
            "Cliente desativado."
        )

    return cliente