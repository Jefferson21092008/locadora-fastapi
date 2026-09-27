from pydantic import (
    BaseModel,
    Field,
)


class AuditLogResponse(BaseModel):
    id: int
    usuario_id: int
    usuario: str
    role: str
    acao: str
    recurso: str
    recurso_id: str | None = None
    campos_alterados: list[str] = Field(
        default_factory=list
    )
    request_id: str | None = None
    criado_em: str
