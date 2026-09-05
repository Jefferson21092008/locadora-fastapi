import pytest

from modulos.config import (
    Configuracao,
)


def test_configuracao_exige_senha_do_admin(
    monkeypatch,
):
    monkeypatch.delenv(
        "LOCADORA_ADMIN_SENHA",
        raising=False,
    )
    monkeypatch.setenv(
        "LOCADORA_JWT_SECRET",
        "segredo-de-teste",
    )

    with pytest.raises(
        RuntimeError,
        match="LOCADORA_ADMIN_SENHA",
    ):
        Configuracao()


def test_configuracao_exige_segredo_jwt(
    monkeypatch,
):
    monkeypatch.setenv(
        "LOCADORA_ADMIN_SENHA",
        "senha-de-teste",
    )
    monkeypatch.delenv(
        "LOCADORA_JWT_SECRET",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match="LOCADORA_JWT_SECRET",
    ):
        Configuracao()


def test_configuracao_aceita_variaveis_obrigatorias(
    monkeypatch,
):
    monkeypatch.setenv(
        "LOCADORA_ADMIN_SENHA",
        "senha-de-teste",
    )
    monkeypatch.setenv(
        "LOCADORA_JWT_SECRET",
        "segredo-de-teste",
    )

    configuracao = Configuracao()

    assert (
        configuracao.admin_senha
        == "senha-de-teste"
    )
    assert (
        configuracao.jwt_secret
        == "segredo-de-teste"
    )
