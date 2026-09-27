import json
import logging
import sys

from datetime import (
    datetime,
    timezone,
)
from time import perf_counter
from uuid import uuid4

from api.monitoramento import (
    associar_request_id,
)


NOME_LOGGER_BASE = "locadora"
HEADER_REQUEST_ID = "X-Request-ID"

CAMPOS_ESTRUTURADOS = (
    "event",
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "user_id",
    "role",
)


class FormatadorJSON(
    logging.Formatter
):
    """
    Formata logs da aplicação em uma linha JSON.

    Somente campos explicitamente permitidos entram
    no payload. Isso reduz o risco de registrar por
    acidente senha, token, cabeçalhos ou corpo da
    requisição.
    """

    def format(
        self,
        record,
    ):
        payload = {
            "timestamp": (
                datetime.now(
                    timezone.utc
                )
                .isoformat(
                    timespec="milliseconds"
                )
                .replace(
                    "+00:00",
                    "Z",
                )
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for campo in CAMPOS_ESTRUTURADOS:
            valor = getattr(
                record,
                campo,
                None,
            )

            if valor is not None:
                payload[campo] = valor

        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def configurar_logs():
    """
    Configura apenas os loggers da aplicação.

    Os logs internos do Uvicorn continuam sob controle
    do próprio servidor. Assim evitamos alterar a
    configuração global de bibliotecas de terceiros.
    """
    logger_base = logging.getLogger(
        NOME_LOGGER_BASE
    )

    logger_base.setLevel(
        logging.INFO
    )
    logger_base.propagate = False

    if not any(
        getattr(
            handler,
            "_locadora_json",
            False,
        )
        for handler in logger_base.handlers
    ):
        handler = logging.StreamHandler(
            sys.stdout
        )
        handler.setFormatter(
            FormatadorJSON()
        )
        handler._locadora_json = True

        logger_base.addHandler(
            handler
        )

    return logger_base


logger_http = logging.getLogger(
    "locadora.http"
)
logger_eventos = logging.getLogger(
    "locadora.eventos"
)


def gerar_request_id():
    return str(
        uuid4()
    )


def request_id_atual(
    request,
):
    return getattr(
        request.state,
        "request_id",
        None,
    )


def registrar_evento(
    evento,
    *,
    request_id=None,
    user_id=None,
    role=None,
    status_code=None,
):
    """
    Registra eventos relevantes sem aceitar campos
    arbitrários potencialmente sensíveis.
    """
    extra = {
        "event": evento,
    }

    if request_id is not None:
        extra["request_id"] = (
            request_id
        )

    if user_id is not None:
        extra["user_id"] = user_id

    if role is not None:
        extra["role"] = role

    if status_code is not None:
        extra["status_code"] = (
            status_code
        )

    logger_eventos.info(
        evento,
        extra=extra,
    )


async def middleware_observabilidade(
    request,
    call_next,
):
    """
    Cria um request ID e registra uma linha estruturada
    ao final de cada requisição HTTP.

    Não registra query string, headers nem body.
    """
    request_id = gerar_request_id()
    request.state.request_id = (
        request_id
    )
    associar_request_id(
        request_id
    )

    inicio = perf_counter()
    status_code = 500

    try:
        response = await call_next(
            request
        )
        status_code = (
            response.status_code
        )

        response.headers[
            HEADER_REQUEST_ID
        ] = request_id

        return response

    finally:
        duracao_ms = round(
            (
                perf_counter()
                - inicio
            )
            * 1000,
            2,
        )

        logger_http.info(
            "http.request",
            extra={
                "event": (
                    "http.request"
                ),
                "request_id": (
                    request_id
                ),
                "method": (
                    request.method
                ),
                "path": (
                    request.url.path
                ),
                "status_code": (
                    status_code
                ),
                "duration_ms": (
                    duracao_ms
                ),
            },
        )
