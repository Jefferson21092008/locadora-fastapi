import json
import logging

from uuid import UUID

from fastapi.testclient import TestClient

from api.main import app
from api.observabilidade import (
    FormatadorJSON,
    HEADER_REQUEST_ID,
    logger_eventos,
    logger_http,
    registrar_evento,
)


def test_resposta_recebe_request_id_uuid():
    with TestClient(app) as client:
        resposta = client.get(
            "/"
        )

    request_id = resposta.headers[
        HEADER_REQUEST_ID
    ]

    assert resposta.status_code == 200
    assert str(UUID(request_id)) == request_id


def test_request_id_muda_entre_requisicoes():
    with TestClient(app) as client:
        primeira = client.get(
            "/"
        )
        segunda = client.get(
            "/"
        )

    assert (
        primeira.headers[
            HEADER_REQUEST_ID
        ]
        != segunda.headers[
            HEADER_REQUEST_ID
        ]
    )


def test_log_http_registra_campos_estruturados(
    monkeypatch,
):
    registros = []

    def capturar(
        mensagem,
        *,
        extra,
    ):
        registros.append(
            (mensagem, extra)
        )

    monkeypatch.setattr(
        logger_http,
        "info",
        capturar,
    )

    with TestClient(app) as client:
        resposta = client.get(
            "/"
        )

    assert len(registros) == 1

    mensagem, extra = registros[0]

    assert mensagem == "http.request"
    assert extra["event"] == "http.request"
    assert extra["method"] == "GET"
    assert extra["path"] == "/"
    assert extra["status_code"] == 200
    assert extra["duration_ms"] >= 0
    assert (
        extra["request_id"]
        == resposta.headers[
            HEADER_REQUEST_ID
        ]
    )


def test_log_http_nao_registra_query_headers_ou_body(
    monkeypatch,
):
    registros = []

    def capturar(
        mensagem,
        *,
        extra,
    ):
        registros.append(
            (mensagem, extra)
        )

    monkeypatch.setattr(
        logger_http,
        "info",
        capturar,
    )

    segredo_query = (
        "token-super-secreto-query"
    )
    segredo_header = (
        "token-super-secreto-header"
    )

    with TestClient(app) as client:
        client.get(
            f"/?token={segredo_query}",
            headers={
                "Authorization": (
                    "Bearer "
                    f"{segredo_header}"
                )
            },
        )

    conteudo = repr(
        registros
    )

    assert segredo_query not in conteudo
    assert segredo_header not in conteudo


def test_formatador_json_ignora_campo_sensivel_arbitrario():
    registro = logging.LogRecord(
        name="locadora.http",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="http.request",
        args=(),
        exc_info=None,
    )

    registro.event = "http.request"
    registro.request_id = "abc-123"
    registro.method = "POST"
    registro.path = "/auth/login"
    registro.status_code = 401
    registro.duration_ms = 2.5
    registro.senha = "senha-super-secreta"
    registro.token = "token-super-secreto"

    payload = json.loads(
        FormatadorJSON().format(
            registro
        )
    )

    conteudo = json.dumps(
        payload
    )

    assert payload["event"] == "http.request"
    assert payload["status_code"] == 401
    assert "senha-super-secreta" not in conteudo
    assert "token-super-secreto" not in conteudo


def test_evento_importante_aceita_apenas_campos_previstos(
    monkeypatch,
):
    registros = []

    def capturar(
        mensagem,
        *,
        extra,
    ):
        registros.append(
            (mensagem, extra)
        )

    monkeypatch.setattr(
        logger_eventos,
        "info",
        capturar,
    )

    registrar_evento(
        "auth.login.succeeded",
        request_id="request-123",
        user_id=7,
        role="cliente",
        status_code=200,
    )

    assert registros == [
        (
            "auth.login.succeeded",
            {
                "event": (
                    "auth.login.succeeded"
                ),
                "request_id": (
                    "request-123"
                ),
                "user_id": 7,
                "role": "cliente",
                "status_code": 200,
            },
        )
    ]
