from datetime import date

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


ANO_ATUAL = date.today().year


class VeiculoCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "tipo": "carro",
                    "modelo": "Toyota Corolla",
                    "ano": ANO_ATUAL,
                    "diaria": 180.0,
                    "preco_km": 1.5,
                }
            ]
        },
    )

    tipo: str = Field(
        min_length=2,
        max_length=30,
        description=(
            "Tipo do veículo que será cadastrado."
        ),
        examples=[
            "carro"
        ],
    )

    modelo: str = Field(
        min_length=2,
        max_length=100,
        description=(
            "Modelo do veículo."
        ),
        examples=[
            "Toyota Corolla"
        ],
    )

    ano: int = Field(
        ge=1886,
        le=ANO_ATUAL + 1,
        description=(
            "Ano de fabricação ou modelo do veículo."
        ),
        examples=[
            ANO_ATUAL
        ],
    )

    diaria: float = Field(
        gt=0,
        description=(
            "Valor cobrado por dia de aluguel."
        ),
        examples=[
            180.0
        ],
    )

    preco_km: float = Field(
        ge=0,
        description=(
            "Valor cobrado por quilômetro rodado."
        ),
        examples=[
            1.5
        ],
    )

    @field_validator(
        "tipo",
        "modelo",
    )
    @classmethod
    def validar_textos(
        cls,
        valor,
    ):
        if not valor.strip():
            raise ValueError(
                "O campo não pode "
                "ficar vazio."
            )

        return valor


class VeiculoUpdate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "modelo": "Toyota Corolla Altis",
                    "ano": ANO_ATUAL,
                    "diaria": 200.0,
                    "preco_km": 1.75,
                }
            ]
        },
    )

    modelo: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description=(
            "Novo modelo do veículo. "
            "Campo opcional."
        ),
        examples=[
            "Toyota Corolla Altis"
        ],
    )

    ano: int | None = Field(
        default=None,
        ge=1886,
        le=ANO_ATUAL + 1,
        description=(
            "Novo ano do veículo. "
            "Campo opcional."
        ),
        examples=[
            ANO_ATUAL
        ],
    )

    diaria: float | None = Field(
        default=None,
        gt=0,
        description=(
            "Novo valor da diária. "
            "Campo opcional."
        ),
        examples=[
            200.0
        ],
    )

    preco_km: float | None = Field(
        default=None,
        ge=0,
        description=(
            "Novo valor cobrado por quilômetro. "
            "Campo opcional."
        ),
        examples=[
            1.75
        ],
    )

    @field_validator(
        "modelo",
    )
    @classmethod
    def validar_modelo(
        cls,
        valor,
    ):
        if valor is None:
            return valor

        if not valor.strip():
            raise ValueError(
                "O modelo não pode "
                "ficar vazio."
            )

        return valor


class VeiculoResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "tipo": "carro",
                    "modelo": "Toyota Corolla",
                    "ano": ANO_ATUAL,
                    "diaria": 180.0,
                    "preco_km": 1.5,
                    "quilometragem": 25400.0,
                    "status": "disponivel",
                    "ativo": True,
                }
            ]
        }
    )

    id: int = Field(
        description=(
            "Identificador único do veículo."
        ),
        examples=[
            1
        ],
    )

    tipo: str = Field(
        description=(
            "Tipo do veículo."
        ),
        examples=[
            "carro"
        ],
    )

    modelo: str = Field(
        description=(
            "Modelo do veículo."
        ),
        examples=[
            "Toyota Corolla"
        ],
    )

    ano: int = Field(
        description=(
            "Ano do veículo."
        ),
        examples=[
            ANO_ATUAL
        ],
    )

    diaria: float = Field(
        description=(
            "Valor atual da diária do veículo."
        ),
        examples=[
            180.0
        ],
    )

    preco_km: float = Field(
        description=(
            "Valor cobrado por quilômetro rodado."
        ),
        examples=[
            1.5
        ],
    )

    quilometragem: float = Field(
        description=(
            "Quilometragem atual registrada "
            "para o veículo."
        ),
        examples=[
            25400.0
        ],
    )

    status: str = Field(
        description=(
            "Situação operacional atual do veículo."
        ),
        examples=[
            "disponivel"
        ],
    )

    ativo: bool = Field(
        description=(
            "Indica se o veículo está ativo "
            "no cadastro da locadora."
        ),
        examples=[
            True
        ],
    )
