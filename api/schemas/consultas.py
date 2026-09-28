from pydantic import BaseModel, Field

from api.schemas.alugueis import AluguelResponse
from api.schemas.clientes import ClienteResponse
from api.schemas.manutencoes import ManutencaoResponse
from api.schemas.veiculos import VeiculoResponse


class PaginacaoResponse(BaseModel):
    pagina: int = Field(ge=1)
    por_pagina: int = Field(ge=1)
    total: int = Field(ge=0)
    total_paginas: int = Field(ge=0)


class ClientesResumoResponse(BaseModel):
    total: int = Field(ge=0)
    ativos: int = Field(ge=0)
    desativados: int = Field(ge=0)


class ClientesConsultaResponse(PaginacaoResponse):
    items: list[ClienteResponse]
    resumo: ClientesResumoResponse


class VeiculosResumoResponse(BaseModel):
    total: int = Field(ge=0)
    disponiveis: int = Field(ge=0)
    alugados: int = Field(ge=0)
    manutencao: int = Field(ge=0)
    desativados: int = Field(ge=0)


class VeiculosConsultaResponse(PaginacaoResponse):
    items: list[VeiculoResponse]
    resumo: VeiculosResumoResponse


class AlugueisResumoResponse(BaseModel):
    total: int = Field(ge=0)
    ativos: int = Field(ge=0)
    finalizados: int = Field(ge=0)
    atrasados: int = Field(ge=0)


class AlugueisConsultaResponse(PaginacaoResponse):
    items: list[AluguelResponse]
    resumo: AlugueisResumoResponse


class ManutencoesResumoResponse(BaseModel):
    total: int = Field(ge=0)
    ativas: int = Field(ge=0)
    finalizadas: int = Field(ge=0)
    custo_finalizado: float = Field(ge=0)


class ManutencoesConsultaResponse(PaginacaoResponse):
    items: list[ManutencaoResponse]
    resumo: ManutencoesResumoResponse
