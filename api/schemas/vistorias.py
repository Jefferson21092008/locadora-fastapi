from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


TipoInspecao = Literal[
    "retirada",
    "devolucao",
]


class InspecaoCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    tipo: TipoInspecao
    quilometragem: float = Field(
        ge=0,
    )
    combustivel_percentual: int = Field(
        ge=0,
        le=100,
    )
    observacoes: str | None = Field(
        default=None,
        max_length=500,
    )


class InspecaoResponse(BaseModel):
    id: int = Field(
        gt=0,
    )
    aluguel_id: int = Field(
        gt=0,
    )
    tipo: TipoInspecao
    quilometragem: float = Field(
        ge=0,
    )
    combustivel_percentual: int = Field(
        ge=0,
        le=100,
    )
    observacoes: str | None = None
    criada_em: str


class DanoCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    descricao: str = Field(
        min_length=3,
        max_length=500,
    )
    valor_estimado: float = Field(
        ge=0,
    )


class DanoResponse(BaseModel):
    id: int = Field(
        gt=0,
    )
    aluguel_id: int = Field(
        gt=0,
    )
    descricao: str
    valor_estimado: float = Field(
        ge=0,
    )
    status: Literal[
        "ativo",
        "cancelado",
    ]
    criada_em: str
    cancelada_em: str | None = None


class MultaTransitoCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    descricao: str = Field(
        min_length=3,
        max_length=500,
    )
    valor: float = Field(
        ge=0,
    )
    data_ocorrencia: str = Field(
        min_length=10,
        max_length=30,
    )


class MultaTransitoResponse(BaseModel):
    id: int = Field(
        gt=0,
    )
    aluguel_id: int = Field(
        gt=0,
    )
    descricao: str
    valor: float = Field(
        ge=0,
    )
    data_ocorrencia: str
    status: Literal[
        "ativa",
        "cancelada",
    ]
    criada_em: str
    cancelada_em: str | None = None


class CaucaoUpsert(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    valor: float = Field(
        gt=0,
    )
    valor_liberado: float = Field(
        default=0,
        ge=0,
    )
    observacoes: str | None = Field(
        default=None,
        max_length=500,
    )


class CaucaoResponse(BaseModel):
    id: int = Field(
        gt=0,
    )
    aluguel_id: int = Field(
        gt=0,
    )
    valor: float = Field(
        gt=0,
    )
    valor_liberado: float = Field(
        ge=0,
    )
    valor_retido: float = Field(
        ge=0,
    )
    status: Literal[
        "retida",
        "parcial",
        "liberada",
    ]
    observacoes: str | None = None
    criada_em: str
    atualizada_em: str


class AluguelVistoriaResponse(BaseModel):
    id: int = Field(
        gt=0,
    )
    cliente_id: int = Field(
        gt=0,
    )
    cliente_nome: str
    cliente_usuario: str
    veiculo_id: int = Field(
        gt=0,
    )
    veiculo_tipo: str
    veiculo_modelo: str
    status: Literal[
        "ativo",
        "finalizado",
    ]
    data_inicio: str
    data_prevista: str
    data_fim: str | None = None


class IndicadoresVistoriaResponse(BaseModel):
    combustivel_retirada: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    combustivel_devolucao: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    combustivel_faltante: int = Field(
        ge=0,
        le=100,
    )
    danos_ativos_total: float = Field(
        ge=0,
    )
    multas_ativas_total: float = Field(
        ge=0,
    )
    caucao_retida: float = Field(
        ge=0,
    )
    pendencias_estimadas_total: float = Field(
        ge=0,
    )


class ResumoVistoriaResponse(BaseModel):
    aluguel: AluguelVistoriaResponse
    inspecoes: list[
        InspecaoResponse
    ]
    danos: list[
        DanoResponse
    ]
    multas: list[
        MultaTransitoResponse
    ]
    caucao: CaucaoResponse | None
    indicadores: IndicadoresVistoriaResponse
