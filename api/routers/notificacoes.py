from typing import Literal

from fastapi import APIRouter, Depends, Query

from api.dependencias import exigir_permissao, get_container
from api.schemas.notificacoes import (
    LeituraNotificacoesResponse,
    NotificacaoResponse,
    NotificacoesConsultaResponse,
    SincronizacaoNotificacoesResponse,
)
from modulos.container import Container
from modulos.permissoes import Permissao


router = APIRouter(
    prefix="/notificacoes",
    tags=["Notificações"],
)


def transformar_notificacao(notificacao):
    return NotificacaoResponse(
        id=notificacao.id,
        tipo=notificacao.tipo,
        titulo=notificacao.titulo,
        mensagem=notificacao.mensagem,
        referencia_tipo=notificacao.referencia_tipo,
        referencia_id=notificacao.referencia_id,
        lida=notificacao.lida,
        criada_em=notificacao.criada_em,
        lida_em=notificacao.lida_em,
        email_status=notificacao.email_status,
    )


@router.post(
    "/sincronizar",
    response_model=SincronizacaoNotificacoesResponse,
    summary="Sincronizar lembretes do usuário",
)
def sincronizar_notificacoes(
    container: Container = Depends(get_container),
    usuario=Depends(
        exigir_permissao(
            Permissao.NOTIFICACOES_LER
        )
    ),
):
    return container.notificacao_service.processar_usuario(
        usuario
    )


@router.get(
    "/consulta",
    response_model=NotificacoesConsultaResponse,
    summary="Consultar minhas notificações",
)
def consultar_notificacoes(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    status: Literal[
        "todas",
        "nao_lidas",
        "lidas",
    ] = "todas",
    container: Container = Depends(get_container),
    usuario=Depends(
        exigir_permissao(
            Permissao.NOTIFICACOES_LER
        )
    ),
):
    resultado = container.notificacao_service.consultar(
        usuario_id=usuario.id,
        pagina=pagina,
        por_pagina=por_pagina,
        status=status,
    )

    return {
        "items": [
            transformar_notificacao(item)
            for item in resultado.items
        ],
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


@router.patch(
    "/ler-todas",
    response_model=LeituraNotificacoesResponse,
    summary="Marcar todas as notificações como lidas",
)
def marcar_todas_lidas(
    container: Container = Depends(get_container),
    usuario=Depends(
        exigir_permissao(
            Permissao.NOTIFICACOES_LER
        )
    ),
):
    atualizadas = (
        container.notificacao_service
        .marcar_todas_como_lidas(
            usuario.id
        )
    )
    return {
        "atualizadas": atualizadas,
    }


@router.patch(
    "/{id_notificacao}/ler",
    response_model=NotificacaoResponse,
    summary="Marcar uma notificação como lida",
)
def marcar_notificacao_lida(
    id_notificacao: int,
    container: Container = Depends(get_container),
    usuario=Depends(
        exigir_permissao(
            Permissao.NOTIFICACOES_LER
        )
    ),
):
    notificacao = (
        container.notificacao_service
        .marcar_como_lida(
            id_notificacao=id_notificacao,
            usuario_id=usuario.id,
        )
    )
    return transformar_notificacao(
        notificacao
    )
