import sentry_sdk

from api.observabilidade import (
    registrar_evento,
    request_id_atual,
)


def registrar_auditoria(
    *,
    request,
    container,
    ator,
    acao,
    recurso,
    recurso_id=None,
    campos_alterados=None,
):
    """
    Faz a ponte entre o contexto HTTP e o AuditoriaService.

    O ator pode ser uma entidade Usuario ou Cliente. Nenhum valor
    sensível da requisição é aceito por esta função.

    Como as regras atuais de negócio já confirmam suas próprias
    transações antes de chegarem aqui, uma falha isolada na escrita
    da auditoria não transforma uma operação concluída em resposta
    HTTP 500. A falha é enviada aos logs estruturados e ao Sentry.
    """
    usuario_id = getattr(
        ator,
        "usuario_id",
        None,
    )

    if usuario_id is None:
        usuario_id = getattr(
            ator,
            "id",
        )

    usuario = getattr(
        ator,
        "usuario",
    )

    role = getattr(
        ator,
        "role",
        "cliente",
    )

    role_valor = getattr(
        role,
        "value",
        role,
    )

    request_id = request_id_atual(
        request
    )

    try:
        return (
            container.auditoria_service
            .registrar(
                usuario_id=usuario_id,
                usuario=usuario,
                role=role_valor,
                acao=acao,
                recurso=recurso,
                recurso_id=recurso_id,
                campos_alterados=(
                    campos_alterados
                ),
                request_id=request_id,
            )
        )

    except Exception as erro:
        registrar_evento(
            "audit.write_failed",
            request_id=request_id,
            user_id=usuario_id,
            role=role_valor,
            status_code=500,
        )

        if sentry_sdk.is_initialized():
            sentry_sdk.capture_exception(
                erro
            )

        return None
