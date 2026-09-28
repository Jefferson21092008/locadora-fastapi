from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.headers_seguranca import (
    middleware_headers_seguranca,
)
from api.main import app


client = TestClient(app)


def test_frontend_recebe_headers_de_hardening():
    response = client.get(
        "/app/"
    )

    assert response.status_code == 200
    assert (
        response.headers[
            "x-content-type-options"
        ]
        == "nosniff"
    )
    assert (
        response.headers[
            "x-frame-options"
        ]
        == "DENY"
    )
    assert (
        response.headers[
            "referrer-policy"
        ]
        == "strict-origin-when-cross-origin"
    )
    assert (
        "frame-ancestors 'none'"
        in response.headers[
            "content-security-policy"
        ]
    )
    assert (
        "script-src 'self'"
        in response.headers[
            "content-security-policy"
        ]
    )


def test_auth_nao_deve_ser_cacheada():
    app_teste = FastAPI()
    app_teste.middleware("http")(
        middleware_headers_seguranca
    )

    @app_teste.post(
        "/api/v1/auth/teste"
    )
    def auth_teste():
        return {"ok": True}

    with TestClient(
        app_teste
    ) as client_teste:
        response = client_teste.post(
            "/api/v1/auth/teste"
        )

    assert response.status_code == 200
    assert (
        response.headers[
            "cache-control"
        ]
        == "no-store"
    )
    assert (
        response.headers[
            "pragma"
        ]
        == "no-cache"
    )


def test_tela_de_redefinicao_nao_envia_referrer():
    response = client.get(
        "/app/redefinir-senha.html"
    )

    assert response.status_code == 200
    assert (
        response.headers[
            "referrer-policy"
        ]
        == "no-referrer"
    )
    assert (
        response.headers[
            "cache-control"
        ]
        == "no-store"
    )


def test_hsts_so_e_ativado_em_producao_https(
    monkeypatch,
):
    monkeypatch.setenv(
        "LOCADORA_AMBIENTE",
        "production",
    )
    monkeypatch.setenv(
        "LOCADORA_PUBLIC_URL",
        "https://locadora.example",
    )

    response = client.get(
        "/"
    )

    assert (
        response.headers[
            "strict-transport-security"
        ]
        == "max-age=31536000"
    )
