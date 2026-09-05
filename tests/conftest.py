import pytest

from modulos.seguranca import (
    SegurancaSenha,
)


@pytest.fixture(
    autouse=True
)
def reduzir_pbkdf2_nos_testes(
    monkeypatch,
):
    monkeypatch.setattr(
        SegurancaSenha,
        "ITERACOES",
        10_000,
    )