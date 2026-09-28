from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


FormaPagamentoFinanceiro = Literal[
    "dinheiro",
    "pix",
    "debito",
    "credito",
    "boleto",
    "transferencia",
]


class PagamentoFinanceiroCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    valor: float = Field(gt=0)
    forma: FormaPagamentoFinanceiro
    parcelas: int = Field(
        default=1,
        ge=1,
        le=12,
    )
    observacoes: str | None = Field(
        default=None,
        max_length=500,
    )

    @model_validator(mode="after")
    def validar_parcelamento(self):
        if (
            self.forma != "credito"
            and self.parcelas != 1
        ):
            raise ValueError(
                "Parcelas só podem ser usadas "
                "em pagamento por crédito."
            )

        return self


class PagamentoFinanceiroResponse(BaseModel):
    id: int = Field(gt=0)
    aluguel_id: int = Field(gt=0)
    valor: float = Field(gt=0)
    forma: FormaPagamentoFinanceiro
    parcelas: int = Field(ge=1, le=12)
    observacoes: str | None = None
    status: Literal[
        "confirmado",
        "estornado",
    ]
    criado_em: str
    estornado_em: str | None = None


class AluguelFinanceiroResponse(BaseModel):
    id: int = Field(gt=0)
    cliente_id: int = Field(gt=0)
    cliente_nome: str
    cliente_usuario: str
    veiculo_id: int = Field(gt=0)
    veiculo_tipo: str
    veiculo_modelo: str
    status: Literal[
        "ativo",
        "finalizado",
    ]
    data_inicio: str
    data_prevista: str
    data_fim: str | None = None
    pagamento_legado: str | None = None


class ResumoFinanceiroAluguelResponse(BaseModel):
    aluguel: AluguelFinanceiroResponse
    pagamentos: list[
        PagamentoFinanceiroResponse
    ]
    valor_devolucao: float = Field(ge=0)
    multa_atraso: float = Field(ge=0)
    danos_total: float = Field(ge=0)
    multas_transito_total: float = Field(ge=0)
    total_devido: float = Field(ge=0)
    valor_legado_pago: float = Field(ge=0)
    pagamentos_adicionais: float = Field(ge=0)
    total_pago: float = Field(ge=0)
    saldo_pendente: float = Field(ge=0)
    credito_cliente: float = Field(ge=0)
    caucao_retida_disponivel: float = Field(ge=0)
    status_financeiro: Literal[
        "pendente",
        "parcial",
        "liquidado",
        "credito",
    ]


class ResumoFinanceiroListaResponse(BaseModel):
    aluguel_id: int = Field(gt=0)
    cliente_nome: str
    veiculo: str
    data_fim: str | None = None
    total_devido: float = Field(ge=0)
    total_pago: float = Field(ge=0)
    saldo_pendente: float = Field(ge=0)
    credito_cliente: float = Field(ge=0)
    caucao_retida_disponivel: float = Field(ge=0)
    status_financeiro: Literal[
        "pendente",
        "parcial",
        "liquidado",
        "credito",
    ]


class ConsultaFinanceiraResumoResponse(BaseModel):
    total: int = Field(ge=0)
    ativos: int = Field(ge=0)
    finalizados: int = Field(ge=0)
    atrasados: int = Field(ge=0)


class ConsultaFinanceiraResponse(BaseModel):
    items: list[
        ResumoFinanceiroListaResponse
    ]
    pagina: int = Field(ge=1)
    por_pagina: int = Field(ge=1)
    total: int = Field(ge=0)
    total_paginas: int = Field(ge=0)
    resumo: ConsultaFinanceiraResumoResponse
