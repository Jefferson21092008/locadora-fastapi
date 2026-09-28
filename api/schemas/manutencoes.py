from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


TipoManutencao = Literal[
    "preventiva",
    "corretiva",
]

PrioridadeManutencao = Literal[
    "baixa",
    "media",
    "alta",
]


class ManutencaoCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "id_veiculo": 1,
                    "motivo": (
                        "Troca de óleo e revisão "
                        "do sistema de freios"
                    ),
                    "tipo": "preventiva",
                    "prioridade": "media",
                    "fornecedor": "Oficina Central",
                    "custo_estimado": 450.0,
                    "data_prevista": "2026-09-30",
                    "observacoes": (
                        "Confirmar desgaste das pastilhas."
                    ),
                }
            ]
        },
    )

    id_veiculo: int = Field(
        gt=0,
        description=(
            "Identificador do veículo que entrará "
            "em manutenção."
        ),
        examples=[1],
    )

    motivo: str = Field(
        min_length=3,
        max_length=300,
        description=(
            "Motivo ou descrição do serviço "
            "de manutenção."
        ),
        examples=[
            "Troca de óleo e revisão dos freios"
        ],
    )

    tipo: TipoManutencao = Field(
        default="corretiva",
        description=(
            "Classificação da manutenção."
        ),
    )

    prioridade: PrioridadeManutencao = Field(
        default="media",
        description=(
            "Prioridade operacional da manutenção."
        ),
    )

    fornecedor: str | None = Field(
        default=None,
        max_length=150,
        description=(
            "Oficina ou fornecedor responsável."
        ),
    )

    custo_estimado: float = Field(
        default=0,
        ge=0,
        description=(
            "Estimativa de custo antes da conclusão."
        ),
    )

    data_prevista: str | None = Field(
        default=None,
        max_length=30,
        description=(
            "Data prevista de conclusão em formato ISO."
        ),
        examples=["2026-09-30"],
    )

    observacoes: str | None = Field(
        default=None,
        max_length=500,
        description=(
            "Observações operacionais da manutenção."
        ),
    )


class ManutencaoUpdate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    motivo: str | None = Field(
        default=None,
        min_length=3,
        max_length=300,
    )

    tipo: TipoManutencao | None = None
    prioridade: PrioridadeManutencao | None = None

    fornecedor: str | None = Field(
        default=None,
        max_length=150,
    )

    custo_estimado: float | None = Field(
        default=None,
        ge=0,
    )

    data_prevista: str | None = Field(
        default=None,
        max_length=30,
    )

    observacoes: str | None = Field(
        default=None,
        max_length=500,
    )


class ManutencaoFinalizar(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "custo": 450.0,
                }
            ]
        }
    )

    custo: float = Field(
        ge=0,
        description=(
            "Custo total registrado ao finalizar "
            "a manutenção."
        ),
        examples=[450.0],
    )


class ManutencaoResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 7,
                    "veiculo_id": 1,
                    "motivo": (
                        "Troca de óleo e revisão "
                        "do sistema de freios"
                    ),
                    "quilometragem": 25400.0,
                    "custo": 450.0,
                    "data_inicio": "2026-09-27",
                    "data_fim": "2026-09-28",
                    "status": "finalizada",
                    "tipo": "preventiva",
                    "prioridade": "media",
                    "fornecedor": "Oficina Central",
                    "custo_estimado": 400.0,
                    "data_prevista": "2026-09-28",
                    "observacoes": None,
                    "atrasada": False,
                }
            ]
        }
    )

    id: int = Field(
        gt=0,
        description=(
            "Identificador único da manutenção."
        ),
    )

    veiculo_id: int = Field(
        gt=0,
        description=(
            "Identificador do veículo relacionado "
            "à manutenção."
        ),
    )

    motivo: str = Field(
        description=(
            "Motivo registrado para a manutenção."
        ),
    )

    quilometragem: float = Field(
        ge=0,
        description=(
            "Quilometragem do veículo registrada "
            "na abertura da manutenção."
        ),
    )

    custo: float = Field(
        ge=0,
        description=(
            "Custo real registrado ao finalizar."
        ),
    )

    data_inicio: str = Field(
        description=(
            "Data de início da manutenção."
        ),
    )

    data_fim: str | None = Field(
        description=(
            "Data de finalização. É nula enquanto "
            "a manutenção estiver ativa."
        ),
    )

    status: Literal[
        "ativa",
        "finalizada",
    ] = Field(
        description=(
            "Situação atual da manutenção."
        ),
    )

    tipo: TipoManutencao = Field(
        default="corretiva",
    )

    prioridade: PrioridadeManutencao = Field(
        default="media",
    )

    fornecedor: str | None = None

    custo_estimado: float = Field(
        default=0,
        ge=0,
    )

    data_prevista: str | None = None

    observacoes: str | None = None

    atrasada: bool = False
