from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ================================================================
# ABERTURA DE MANUTENÇÃO
# ================================================================


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
        examples=[
            1
        ],
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


# ================================================================
# FINALIZAÇÃO
# ================================================================


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
        examples=[
            450.0
        ],
    )


# ================================================================
# RESPOSTA
# ================================================================


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
                    "data_inicio": "2026-08-27",
                    "data_fim": "2026-08-28",
                    "status": "finalizada",
                }
            ]
        }
    )

    id: int = Field(
        gt=0,
        description=(
            "Identificador único da manutenção."
        ),
        examples=[
            7
        ],
    )

    veiculo_id: int = Field(
        gt=0,
        description=(
            "Identificador do veículo relacionado "
            "à manutenção."
        ),
        examples=[
            1
        ],
    )

    motivo: str = Field(
        description=(
            "Motivo registrado para a manutenção."
        ),
        examples=[
            "Troca de óleo e revisão dos freios"
        ],
    )

    quilometragem: float = Field(
        ge=0,
        description=(
            "Quilometragem do veículo registrada "
            "no momento da abertura da manutenção."
        ),
        examples=[
            25400.0
        ],
    )

    custo: float = Field(
        ge=0,
        description=(
            "Custo da manutenção. Enquanto estiver "
            "ativa, pode permanecer em zero."
        ),
        examples=[
            450.0
        ],
    )

    data_inicio: str = Field(
        description=(
            "Data de início da manutenção."
        ),
        examples=[
            "2026-08-27"
        ],
    )

    data_fim: str | None = Field(
        description=(
            "Data de finalização da manutenção. "
            "É nula enquanto a manutenção estiver ativa."
        ),
        examples=[
            "2026-08-28"
        ],
    )

    status: Literal[
        "ativa",
        "finalizada",
    ] = Field(
        description=(
            "Situação atual da manutenção."
        ),
        examples=[
            "finalizada"
        ],
    )
