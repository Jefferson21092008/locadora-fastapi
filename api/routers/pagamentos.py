from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
)

from api.auditoria import (
    registrar_auditoria,
)
from api.dependencias import (
    exigir_permissao,
    get_container,
)
from api.schemas.pagamentos import (
    ConsultaFinanceiraResponse,
    PagamentoFinanceiroCreate,
    PagamentoFinanceiroResponse,
    ResumoFinanceiroAluguelResponse,
)
from modulos.container import Container
from modulos.permissoes import Permissao


router = APIRouter(
    prefix="/pagamentos",
    tags=["Financeiro"],
)


def transformar_pagamento(
    pagamento,
):
    return PagamentoFinanceiroResponse(
        id=pagamento.id,
        aluguel_id=pagamento.aluguel_id,
        valor=pagamento.valor,
        forma=pagamento.forma,
        parcelas=pagamento.parcelas,
        observacoes=pagamento.observacoes,
        status=pagamento.status,
        criado_em=pagamento.criado_em,
        estornado_em=pagamento.estornado_em,
    )


def transformar_resumo(
    resumo,
):
    aluguel = resumo["aluguel"]

    return {
        "aluguel": {
            "id": aluguel.id,
            "cliente_id": aluguel.cliente_id,
            "cliente_nome": aluguel.cliente_nome,
            "cliente_usuario": aluguel.cliente_usuario,
            "veiculo_id": aluguel.veiculo_id,
            "veiculo_tipo": aluguel.veiculo_tipo,
            "veiculo_modelo": aluguel.veiculo_modelo,
            "status": aluguel.status,
            "data_inicio": aluguel.data_inicio,
            "data_prevista": aluguel.data_prevista,
            "data_fim": aluguel.data_fim,
            "pagamento_legado": aluguel.pagamento,
        },
        "pagamentos": [
            transformar_pagamento(item)
            for item in resumo["pagamentos"]
        ],
        "valor_devolucao": resumo["valor_devolucao"],
        "multa_atraso": resumo["multa_atraso"],
        "danos_total": resumo["danos_total"],
        "multas_transito_total": resumo[
            "multas_transito_total"
        ],
        "total_devido": resumo["total_devido"],
        "valor_legado_pago": resumo[
            "valor_legado_pago"
        ],
        "pagamentos_adicionais": resumo[
            "pagamentos_adicionais"
        ],
        "total_pago": resumo["total_pago"],
        "saldo_pendente": resumo["saldo_pendente"],
        "credito_cliente": resumo["credito_cliente"],
        "caucao_retida_disponivel": resumo[
            "caucao_retida_disponivel"
        ],
        "status_financeiro": resumo[
            "status_financeiro"
        ],
    }


@router.get(
    "/consulta",
    response_model=ConsultaFinanceiraResponse,
    summary="Consultar contas financeiras",
)
def consultar_contas(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(12, ge=1, le=100),
    busca: str = Query("", max_length=100),
    ordenar: Literal[
        "id",
        "data_inicio",
        "data_prevista",
        "valor",
    ] = "id",
    direcao: Literal[
        "asc",
        "desc",
    ] = "desc",
    container: Container = Depends(
        get_container
    ),
    _usuario_admin=Depends(
        exigir_permissao(
            Permissao.FINANCEIRO_LER
        )
    ),
):
    resultado = (
        container.pagamento_service
        .consultar_contas(
            pagina=pagina,
            por_pagina=por_pagina,
            busca=busca,
            ordenar=ordenar,
            direcao=direcao,
        )
    )

    items = []
    for resumo in resultado.items:
        aluguel = resumo["aluguel"]
        items.append(
            {
                "aluguel_id": aluguel.id,
                "cliente_nome": aluguel.cliente_nome,
                "veiculo": (
                    f"{aluguel.veiculo_tipo} "
                    f"{aluguel.veiculo_modelo}"
                ),
                "data_fim": aluguel.data_fim,
                "total_devido": resumo["total_devido"],
                "total_pago": resumo["total_pago"],
                "saldo_pendente": resumo["saldo_pendente"],
                "credito_cliente": resumo["credito_cliente"],
                "caucao_retida_disponivel": resumo[
                    "caucao_retida_disponivel"
                ],
                "status_financeiro": resumo[
                    "status_financeiro"
                ],
            }
        )

    return {
        "items": items,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total": resultado.total,
        "total_paginas": (
            resultado.total
            + por_pagina
            - 1
        ) // por_pagina,
        "resumo": resultado.resumo,
    }


@router.get(
    "/alugueis/{id_aluguel}",
    response_model=ResumoFinanceiroAluguelResponse,
    summary="Consultar financeiro de um aluguel",
)
def obter_resumo_financeiro(
    id_aluguel: int,
    container: Container = Depends(
        get_container
    ),
    _usuario_admin=Depends(
        exigir_permissao(
            Permissao.FINANCEIRO_LER
        )
    ),
):
    resumo = (
        container.pagamento_service
        .obter_resumo(id_aluguel)
    )

    return transformar_resumo(
        resumo
    )


@router.post(
    "/alugueis/{id_aluguel}",
    status_code=201,
    response_model=PagamentoFinanceiroResponse,
    summary="Registrar pagamento financeiro",
)
def registrar_pagamento(
    request: Request,
    id_aluguel: int,
    dados: PagamentoFinanceiroCreate,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.FINANCEIRO_RECEBER
        )
    ),
):
    pagamento = (
        container.pagamento_service
        .registrar_pagamento(
            id_aluguel=id_aluguel,
            valor=dados.valor,
            forma=dados.forma,
            parcelas=dados.parcelas,
            observacoes=dados.observacoes,
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="financeiro.pagamento_registrado",
        recurso="pagamento_financeiro",
        recurso_id=pagamento.id,
        campos_alterados=(
            "valor",
            "forma",
            "parcelas",
        ),
    )

    return transformar_pagamento(
        pagamento
    )


@router.patch(
    "/{id_pagamento}/estornar",
    response_model=PagamentoFinanceiroResponse,
    summary="Estornar pagamento financeiro",
)
def estornar_pagamento(
    request: Request,
    id_pagamento: int,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.FINANCEIRO_ESTORNAR
        )
    ),
):
    pagamento = (
        container.pagamento_service
        .estornar_pagamento(
            id_pagamento
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="financeiro.pagamento_estornado",
        recurso="pagamento_financeiro",
        recurso_id=pagamento.id,
        campos_alterados=(
            "status",
            "estornado_em",
        ),
    )

    return transformar_pagamento(
        pagamento
    )
