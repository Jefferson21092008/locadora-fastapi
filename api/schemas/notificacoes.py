from pydantic import BaseModel, Field


class NotificacaoResponse(BaseModel):
    id: int = Field(ge=1)
    tipo: str
    titulo: str
    mensagem: str
    referencia_tipo: str | None = None
    referencia_id: int | None = None
    lida: bool
    criada_em: str
    lida_em: str | None = None
    email_status: str


class NotificacoesResumoResponse(BaseModel):
    total: int = Field(ge=0)
    nao_lidas: int = Field(ge=0)
    lidas: int = Field(ge=0)


class NotificacoesConsultaResponse(BaseModel):
    items: list[NotificacaoResponse]
    pagina: int = Field(ge=1)
    por_pagina: int = Field(ge=1)
    total: int = Field(ge=0)
    total_paginas: int = Field(ge=0)
    resumo: NotificacoesResumoResponse


class SincronizacaoNotificacoesResponse(BaseModel):
    criadas: int = Field(ge=0)
    emails_enviados: int = Field(ge=0)
    emails_falharam: int = Field(ge=0)


class LeituraNotificacoesResponse(BaseModel):
    atualizadas: int = Field(ge=0)
