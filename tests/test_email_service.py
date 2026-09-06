import pytest

from modulos.servicos.email_service import (
    EmailService,
)


class ConfigFake:
    brevo_api_key = "chave-teste"
    email_remetente = "locadora@teste.com"
    public_url = "https://locadora-fastapi.onrender.com"
    email_configurado = True


class RespostaFake:
    def __init__(self):
        self.raise_for_status_chamado = False

    def raise_for_status(self):
        self.raise_for_status_chamado = True


def test_email_service_envia_recuperacao_pela_brevo(
    monkeypatch,
):
    chamada = {}

    def post_fake(
        url,
        headers,
        json,
        timeout,
    ):
        chamada["url"] = url
        chamada["headers"] = headers
        chamada["json"] = json
        chamada["timeout"] = timeout

        resposta = RespostaFake()
        chamada["resposta"] = resposta

        return resposta

    monkeypatch.setattr(
        "modulos.servicos.email_service.httpx.post",
        post_fake,
    )

    service = EmailService(
        ConfigFake()
    )

    service.enviar_recuperacao_senha(
        "cliente@teste.com",
        "token-123",
    )

    assert chamada["url"] == (
        "https://api.brevo.com/v3/smtp/email"
    )

    assert chamada["headers"]["api-key"] == (
        "chave-teste"
    )

    assert chamada["json"]["sender"] == {
        "name": "Locadora FastAPI",
        "email": "locadora@teste.com",
    }

    assert chamada["json"]["to"] == [
        {
            "email": "cliente@teste.com",
        }
    ]

    assert (
        "token=token-123"
        in chamada["json"]["htmlContent"]
    )

    assert (
        "https://locadora-fastapi.onrender.com"
        in chamada["json"]["htmlContent"]
    )

    assert chamada["timeout"] == 15.0

    assert (
        chamada["resposta"]
        .raise_for_status_chamado
        is True
    )


def test_email_service_codifica_token_na_url(
    monkeypatch,
):
    chamada = {}

    def post_fake(
        url,
        headers,
        json,
        timeout,
    ):
        chamada["json"] = json
        return RespostaFake()

    monkeypatch.setattr(
        "modulos.servicos.email_service.httpx.post",
        post_fake,
    )

    service = EmailService(
        ConfigFake()
    )

    service.enviar_recuperacao_senha(
        "cliente@teste.com",
        "abc+123/=",
    )

    assert (
        "token=abc%2B123%2F%3D"
        in chamada["json"]["htmlContent"]
    )


def test_email_service_exige_configuracao():
    class ConfigSemEmail:
        email_configurado = False

    service = EmailService(
        ConfigSemEmail()
    )

    with pytest.raises(
        RuntimeError,
        match="não foi configurado",
    ):
        service.enviar_recuperacao_senha(
            "cliente@teste.com",
            "token",
        )