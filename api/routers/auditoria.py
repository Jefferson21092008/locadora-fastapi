from fastapi import (
    APIRouter,
    Depends,
)

from api.dependencias import (
    get_admin_atual,
    get_container,
)
from api.schemas.auditoria import (
    AuditLogResponse,
)
from modulos.container import (
    Container,
)


router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoria"],
)


@router.get(
    "",
    response_model=list[
        AuditLogResponse
    ],
    summary="Listar registros de auditoria",
    description=(
        "Retorna o histórico persistente de ações "
        "sensíveis realizadas por usuários "
        "autenticados. Operação restrita a "
        "administradores."
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
def listar_auditoria(
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        get_admin_atual
    ),
):
    return [
        AuditLogResponse(
            **registro.to_dict()
        )
        for registro in (
            container.auditoria_service
            .listar()
        )
    ]
