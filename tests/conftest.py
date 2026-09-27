import os

# Evita que a suíte local envie exceções simuladas ao projeto real do Sentry.
# O valor vazio bloqueia o carregamento do DSN do .env pelo python-dotenv.
os.environ["LOCADORA_SENTRY_DSN"] = ""
os.environ["LOCADORA_AMBIENTE"] = "test"

import pytest

from modulos.seguranca import (
    SegurancaSenha,
)
from api.rate_limit import (
    rate_limiter,
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

@pytest.fixture(
    autouse=True
)
def limpar_rate_limiter():
    rate_limiter.limpar_tudo()

    yield

    rate_limiter.limpar_tudo()