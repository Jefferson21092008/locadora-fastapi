from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ================================================================
# RESUMO GERAL
# ================================================================


class ResumoGeralResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "clientes_ativos": 24,
                    "veiculos_ativos": 12,
                    "alugueis_ativos": 4,
                    "alugueis_finalizados": 38,
                    "total_arrecadado": 18650.0,
                }
            ]
        }
    )

    clientes_ativos: int = Field(
        ge=0,
        description=(
            "Quantidade de clientes ativos "
            "cadastrados na locadora."
        ),
        examples=[
            24
        ],
    )

    veiculos_ativos: int = Field(
        ge=0,
        description=(
            "Quantidade de veículos ativos "
            "na frota."
        ),
        examples=[
            12
        ],
    )

    alugueis_ativos: int = Field(
        ge=0,
        description=(
            "Quantidade de aluguéis atualmente ativos."
        ),
        examples=[
            4
        ],
    )

    alugueis_finalizados: int = Field(
        ge=0,
        description=(
            "Quantidade de aluguéis já finalizados."
        ),
        examples=[
            38
        ],
    )

    total_arrecadado: float = Field(
        ge=0,
        description=(
            "Valor total arrecadado com aluguéis "
            "finalizados."
        ),
        examples=[
            18650.0
        ],
    )


# ================================================================
# VEÍCULOS MAIS ALUGADOS
# ================================================================


class VeiculoMaisAlugadoResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 3,
                    "tipo": "carro",
                    "modelo": "Toyota Corolla",
                    "total_alugueis": 12,
                }
            ]
        }
    )

    id: int = Field(
        gt=0,
        description=(
            "Identificador único do veículo."
        ),
        examples=[
            3
        ],
    )

    tipo: str = Field(
        min_length=1,
        description=(
            "Tipo do veículo."
        ),
        examples=[
            "carro"
        ],
    )

    modelo: str = Field(
        min_length=1,
        description=(
            "Modelo do veículo."
        ),
        examples=[
            "Toyota Corolla"
        ],
    )

    total_alugueis: int = Field(
        gt=0,
        description=(
            "Quantidade total de aluguéis "
            "registrados para o veículo."
        ),
        examples=[
            12
        ],
    )


# ================================================================
# FATURAMENTO POR TIPO
# ================================================================


class FaturamentoPorTipoResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "tipo": "carro",
                    "total_alugueis": 25,
                    "faturamento": 14800.0,
                }
            ]
        }
    )

    tipo: str = Field(
        min_length=1,
        description=(
            "Tipo de veículo utilizado no agrupamento."
        ),
        examples=[
            "carro"
        ],
    )

    total_alugueis: int = Field(
        gt=0,
        description=(
            "Quantidade de aluguéis registrados "
            "para esse tipo de veículo."
        ),
        examples=[
            25
        ],
    )

    faturamento: float = Field(
        ge=0,
        description=(
            "Faturamento total gerado pelo tipo "
            "de veículo."
        ),
        examples=[
            14800.0
        ],
    )


# ================================================================
# CUSTOS DE MANUTENÇÃO
# ================================================================


class CustoManutencaoResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 3,
                    "tipo": "carro",
                    "modelo": "Toyota Corolla",
                    "total_manutencoes": 4,
                    "custo_total": 2350.0,
                }
            ]
        }
    )

    id: int = Field(
        gt=0,
        description=(
            "Identificador único do veículo."
        ),
        examples=[
            3
        ],
    )

    tipo: str = Field(
        min_length=1,
        description=(
            "Tipo do veículo."
        ),
        examples=[
            "carro"
        ],
    )

    modelo: str = Field(
        min_length=1,
        description=(
            "Modelo do veículo."
        ),
        examples=[
            "Toyota Corolla"
        ],
    )

    total_manutencoes: int = Field(
        gt=0,
        description=(
            "Quantidade de manutenções registradas "
            "para o veículo."
        ),
        examples=[
            4
        ],
    )

    custo_total: float = Field(
        ge=0,
        description=(
            "Soma dos custos de manutenção "
            "registrados para o veículo."
        ),
        examples=[
            2350.0
        ],
    )


# ================================================================
# CLIENTES QUE MAIS ALUGAM
# ================================================================


class ClienteMaisAlugaResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "cliente_id": 5,
                    "cliente_nome": "João da Silva",
                    "cliente_usuario": "joao123",
                    "total_alugueis": 9,
                    "total_gasto": 7250.0,
                }
            ]
        }
    )

    cliente_id: int = Field(
        gt=0,
        description=(
            "Identificador único do cliente."
        ),
        examples=[
            5
        ],
    )

    cliente_nome: str = Field(
        min_length=1,
        description=(
            "Nome do cliente."
        ),
        examples=[
            "João da Silva"
        ],
    )

    cliente_usuario: str = Field(
        min_length=1,
        description=(
            "Nome de usuário associado ao cliente."
        ),
        examples=[
            "joao123"
        ],
    )

    total_alugueis: int = Field(
        gt=0,
        description=(
            "Quantidade total de aluguéis "
            "realizados pelo cliente."
        ),
        examples=[
            9
        ],
    )

    total_gasto: float = Field(
        ge=0,
        description=(
            "Valor total gasto pelo cliente "
            "em aluguéis."
        ),
        examples=[
            7250.0
        ],
    )


# ================================================================
# RESUMO FINANCEIRO
# ================================================================


class ResumoFinanceiroResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "receita_alugueis": 18650.0,
                    "custos_manutencao": 4300.0,
                    "resultado_bruto": 14350.0,
                }
            ]
        }
    )

    receita_alugueis: float = Field(
        ge=0,
        description=(
            "Receita total obtida com os aluguéis."
        ),
        examples=[
            18650.0
        ],
    )

    custos_manutencao: float = Field(
        ge=0,
        description=(
            "Total de custos registrados "
            "com manutenções."
        ),
        examples=[
            4300.0
        ],
    )

    resultado_bruto: float = Field(
        description=(
            "Resultado bruto calculado pela diferença "
            "entre receitas de aluguéis e custos "
            "de manutenção. Pode ser negativo."
        ),
        examples=[
            14350.0
        ],
    )


# ================================================================
# RESULTADO POR VEÍCULO
# ================================================================


class ResultadoVeiculoResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 3,
                    "tipo": "carro",
                    "modelo": "Toyota Corolla",
                    "total_alugueis": 12,
                    "receita": 8900.0,
                    "total_manutencoes": 4,
                    "custo_manutencao": 2350.0,
                    "resultado_bruto": 6550.0,
                }
            ]
        }
    )

    id: int = Field(
        gt=0,
        description=(
            "Identificador único do veículo."
        ),
        examples=[
            3
        ],
    )

    tipo: str = Field(
        min_length=1,
        description=(
            "Tipo do veículo."
        ),
        examples=[
            "carro"
        ],
    )

    modelo: str = Field(
        min_length=1,
        description=(
            "Modelo do veículo."
        ),
        examples=[
            "Toyota Corolla"
        ],
    )

    total_alugueis: int = Field(
        ge=0,
        description=(
            "Quantidade total de aluguéis "
            "registrados para o veículo."
        ),
        examples=[
            12
        ],
    )

    receita: float = Field(
        ge=0,
        description=(
            "Receita total gerada pelo veículo."
        ),
        examples=[
            8900.0
        ],
    )

    total_manutencoes: int = Field(
        ge=0,
        description=(
            "Quantidade total de manutenções "
            "registradas para o veículo."
        ),
        examples=[
            4
        ],
    )

    custo_manutencao: float = Field(
        ge=0,
        description=(
            "Custo total de manutenção "
            "do veículo."
        ),
        examples=[
            2350.0
        ],
    )

    resultado_bruto: float = Field(
        description=(
            "Resultado bruto individual do veículo, "
            "calculado pela diferença entre sua receita "
            "e seus custos de manutenção. Pode ser negativo."
        ),
        examples=[
            6550.0
        ],
    )
