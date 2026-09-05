from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


# ================================================================
# CRIAÇÃO DO ALUGUEL
# ================================================================


class AluguelCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id_veiculo": 1,
                    "dias": 5,
                    "anos_habilitacao": 3,
                }
            ]
        }
    )

    id_veiculo: int = Field(
        gt=0,
        description=(
            "Identificador do veículo que será alugado."
        ),
        examples=[
            1
        ],
    )

    dias: int = Field(
        gt=0,
        description=(
            "Quantidade de dias prevista "
            "para o aluguel."
        ),
        examples=[
            5
        ],
    )

    anos_habilitacao: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Quantidade de anos de habilitação "
            "do cliente, quando exigida pela regra "
            "do tipo de veículo."
        ),
        examples=[
            3
        ],
    )


# ================================================================
# RESPOSTA DO ALUGUEL
# ================================================================


class AluguelResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 10,
                    "cliente_id": 2,
                    "cliente_usuario": "joao123",
                    "cliente_nome": "João da Silva",
                    "veiculo_id": 1,
                    "veiculo_tipo": "carro",
                    "veiculo_modelo": "Toyota Corolla",
                    "dias": 5,
                    "status": "ativo",
                    "km": 0.0,
                    "pagamento": None,
                    "valor": 900.0,
                    "data_inicio": "2026-08-27",
                    "data_prevista": "2026-09-01",
                    "data_fim": None,
                    "dias_atraso": 0,
                    "multa": 0.0,
                }
            ]
        }
    )

    id: int = Field(
        gt=0,
        description=(
            "Identificador único do aluguel."
        ),
        examples=[
            10
        ],
    )

    cliente_id: int = Field(
        gt=0,
        description=(
            "Identificador do cliente responsável "
            "pelo aluguel."
        ),
        examples=[
            2
        ],
    )

    cliente_usuario: str = Field(
        description=(
            "Nome de usuário do cliente."
        ),
        examples=[
            "joao123"
        ],
    )

    cliente_nome: str = Field(
        description=(
            "Nome do cliente."
        ),
        examples=[
            "João da Silva"
        ],
    )

    veiculo_id: int = Field(
        gt=0,
        description=(
            "Identificador do veículo alugado."
        ),
        examples=[
            1
        ],
    )

    veiculo_tipo: str = Field(
        description=(
            "Tipo do veículo alugado."
        ),
        examples=[
            "carro"
        ],
    )

    veiculo_modelo: str = Field(
        description=(
            "Modelo do veículo alugado."
        ),
        examples=[
            "Toyota Corolla"
        ],
    )

    dias: int = Field(
        gt=0,
        description=(
            "Quantidade de dias contratada."
        ),
        examples=[
            5
        ],
    )

    status: Literal[
        "ativo",
        "finalizado",
    ] = Field(
        description=(
            "Situação atual do aluguel."
        ),
        examples=[
            "ativo"
        ],
    )

    km: float = Field(
        ge=0,
        description=(
            "Quantidade de quilômetros registrada "
            "na devolução. Enquanto o aluguel está "
            "ativo, normalmente permanece em zero."
        ),
        examples=[
            0.0
        ],
    )

    pagamento: str | None = Field(
        description=(
            "Forma de pagamento registrada "
            "após a devolução."
        ),
        examples=[
            "PIX"
        ],
    )

    valor: float = Field(
        ge=0,
        description=(
            "Valor registrado para o aluguel."
        ),
        examples=[
            900.0
        ],
    )

    data_inicio: str = Field(
        description=(
            "Data de início do aluguel."
        ),
        examples=[
            "2026-08-27"
        ],
    )

    data_prevista: str = Field(
        description=(
            "Data prevista para devolução."
        ),
        examples=[
            "2026-09-01"
        ],
    )

    data_fim: str | None = Field(
        description=(
            "Data efetiva da devolução, quando "
            "o aluguel já estiver finalizado."
        ),
        examples=[
            "2026-09-01"
        ],
    )

    dias_atraso: int = Field(
        ge=0,
        description=(
            "Quantidade de dias de atraso "
            "calculada na devolução."
        ),
        examples=[
            0
        ],
    )

    multa: float = Field(
        ge=0,
        description=(
            "Valor da multa por atraso, "
            "quando houver."
        ),
        examples=[
            0.0
        ],
    )


# ================================================================
# DEVOLUÇÃO
# ================================================================


class DevolucaoCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "km": 320.5,
                    "forma_pagamento": 5,
                    "parcelas": 3,
                }
            ]
        }
    )

    km: float = Field(
        ge=0,
        description=(
            "Quantidade de quilômetros rodados "
            "durante o aluguel."
        ),
        examples=[
            320.5
        ],
    )

    forma_pagamento: int = Field(
        ge=1,
        le=7,
        description=(
            "Código da forma de pagamento. "
            "Os valores aceitos vão de 1 a 7, "
            "conforme as formas disponíveis "
            "na aplicação."
        ),
        examples=[
            5
        ],
    )

    parcelas: int | None = Field(
        default=None,
        ge=2,
        le=12,
        description=(
            "Quantidade de parcelas. Deve ser "
            "informada apenas quando a forma de "
            "pagamento for crédito parcelado "
            "(código 5)."
        ),
        examples=[
            3
        ],
    )

    @model_validator(
        mode="after"
    )
    def validar_pagamento(
        self,
    ):
        if (
            self.forma_pagamento == 5
            and self.parcelas is None
        ):
            raise ValueError(
                "Informe a quantidade "
                "de parcelas para o "
                "crédito parcelado."
            )

        if (
            self.forma_pagamento != 5
            and self.parcelas is not None
        ):
            raise ValueError(
                "Parcelas só podem ser "
                "informadas para crédito "
                "parcelado."
            )

        return self


# ================================================================
# PAGAMENTO
# ================================================================


class PagamentoResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "valor_final": 1380.75,
                    "forma": "Crédito parcelado",
                    "parcelas": 3,
                    "valor_parcela": 460.25,
                }
            ]
        }
    )

    valor_final: float = Field(
        ge=0,
        description=(
            "Valor final a ser pago."
        ),
        examples=[
            1380.75
        ],
    )

    forma: str = Field(
        description=(
            "Nome da forma de pagamento utilizada."
        ),
        examples=[
            "Crédito parcelado"
        ],
    )

    parcelas: int = Field(
        ge=1,
        description=(
            "Quantidade de parcelas do pagamento."
        ),
        examples=[
            3
        ],
    )

    valor_parcela: float = Field(
        ge=0,
        description=(
            "Valor de cada parcela."
        ),
        examples=[
            460.25
        ],
    )


# ================================================================
# RESPOSTA DA DEVOLUÇÃO
# ================================================================


class DevolucaoResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "aluguel": {
                        "id": 10,
                        "cliente_id": 2,
                        "cliente_usuario": "joao123",
                        "cliente_nome": "João da Silva",
                        "veiculo_id": 1,
                        "veiculo_tipo": "carro",
                        "veiculo_modelo": "Toyota Corolla",
                        "dias": 5,
                        "status": "finalizado",
                        "km": 320.5,
                        "pagamento": "Crédito parcelado",
                        "valor": 1380.75,
                        "data_inicio": "2026-08-27",
                        "data_prevista": "2026-09-01",
                        "data_fim": "2026-09-01",
                        "dias_atraso": 0,
                        "multa": 0.0,
                    },
                    "veiculo_id": 1,
                    "valor_aluguel": 1380.75,
                    "dias_atraso": 0,
                    "multa": 0.0,
                    "valor_inicial": 900.0,
                    "pagamento": {
                        "valor_final": 1380.75,
                        "forma": "Crédito parcelado",
                        "parcelas": 3,
                        "valor_parcela": 460.25,
                    },
                }
            ]
        }
    )

    aluguel: AluguelResponse = Field(
        description=(
            "Dados atualizados do aluguel "
            "após a devolução."
        ),
    )

    veiculo_id: int = Field(
        gt=0,
        description=(
            "Identificador do veículo devolvido."
        ),
        examples=[
            1
        ],
    )

    valor_aluguel: float = Field(
        ge=0,
        description=(
            "Valor final calculado para o aluguel."
        ),
        examples=[
            1380.75
        ],
    )

    dias_atraso: int = Field(
        ge=0,
        description=(
            "Quantidade de dias de atraso "
            "na devolução."
        ),
        examples=[
            0
        ],
    )

    multa: float = Field(
        ge=0,
        description=(
            "Valor da multa aplicada por atraso."
        ),
        examples=[
            0.0
        ],
    )

    valor_inicial: float = Field(
        ge=0,
        description=(
            "Valor inicialmente calculado "
            "antes dos ajustes da devolução."
        ),
        examples=[
            900.0
        ],
    )

    pagamento: PagamentoResponse = Field(
        description=(
            "Detalhes do pagamento processado."
        ),
    )
