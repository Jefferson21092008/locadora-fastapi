from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


StatusReserva = Literal[
    "ativa",
    "cancelada",
    "convertida",
    "expirada",
]


class ReservaCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "id_veiculo": 1,
                    "data_inicio": "2026-10-10",
                    "data_fim": "2026-10-15",
                }
            ]
        },
    )

    id_veiculo: int = Field(
        gt=0,
    )
    data_inicio: str = Field(
        min_length=10,
        max_length=10,
    )
    data_fim: str = Field(
        min_length=10,
        max_length=10,
    )


class ReservaResponse(BaseModel):
    id: int
    cliente_id: int
    cliente_usuario: str
    cliente_nome: str
    veiculo_id: int
    veiculo_tipo: str
    veiculo_modelo: str
    data_inicio: str
    data_fim: str
    status: StatusReserva
    criada_em: str
    cancelada_em: str | None = None
    convertida_em: str | None = None
    expirada: bool = False


class ReservasResumo(BaseModel):
    total: int = 0
    ativas: int = 0
    expiradas: int = 0
    canceladas: int = 0
    convertidas: int = 0


class ReservasConsultaResponse(BaseModel):
    items: list[ReservaResponse]
    pagina: int
    por_pagina: int
    total: int
    total_paginas: int
    resumo: ReservasResumo
