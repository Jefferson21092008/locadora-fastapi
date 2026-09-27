import os

from urllib.parse import (
    urlsplit,
    urlunsplit,
)

import sentry_sdk

from sentry_sdk.integrations.fastapi import (
    FastApiIntegration,
)


ENV_SENTRY_DSN = "LOCADORA_SENTRY_DSN"
ENV_AMBIENTE = "LOCADORA_AMBIENTE"
AMBIENTE_PADRAO = "development"


def _ambiente_atual():
    return (
        os.getenv(
            ENV_AMBIENTE,
            AMBIENTE_PADRAO,
        )
        or AMBIENTE_PADRAO
    ).strip() or AMBIENTE_PADRAO


def _url_sem_query(
    valor,
):
    if not valor:
        return valor

    partes = urlsplit(
        str(valor)
    )

    return urlunsplit(
        (
            partes.scheme,
            partes.netloc,
            partes.path,
            "",
            "",
        )
    )


def filtrar_evento_sensivel(
    evento,
    hint,
):
    """
    Remove dados de requisição que não são necessários
    para diagnosticar uma exceção.

    Mantemos método e caminho, mas removemos body,
    query string, cookies, headers e dados de usuário.
    """
    request = evento.get(
        "request"
    )

    if isinstance(
        request,
        dict,
    ):
        if "url" in request:
            request["url"] = (
                _url_sem_query(
                    request["url"]
                )
            )

        for campo in (
            "data",
            "cookies",
            "query_string",
            "headers",
            "env",
        ):
            request.pop(
                campo,
                None,
            )

    evento.pop(
        "user",
        None,
    )

    return evento


def configurar_monitoramento_erros():
    """
    Ativa Sentry apenas quando um DSN foi configurado.

    Sem LOCADORA_SENTRY_DSN a aplicação continua
    funcionando normalmente, inclusive em testes e
    desenvolvimento local.
    """
    dsn = (
        os.getenv(
            ENV_SENTRY_DSN,
            "",
        )
        or ""
    ).strip()

    if not dsn:
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=(
            _ambiente_atual()
        ),
        integrations=[
            FastApiIntegration()
        ],
        send_default_pii=False,
        traces_sample_rate=0.0,
        before_send=(
            filtrar_evento_sensivel
        ),
    )

    return True


def associar_request_id(
    request_id,
):
    """
    Liga o request ID da Etapa 5 ao evento do Sentry.

    O tag permite correlacionar um erro recebido no
    monitoramento com a linha correspondente nos logs.
    """
    if (
        not request_id
        or not sentry_sdk.is_initialized()
    ):
        return False

    scope = (
        sentry_sdk
        .get_isolation_scope()
    )
    scope.set_tag(
        "request_id",
        request_id,
    )

    return True
