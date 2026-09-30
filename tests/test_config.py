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


def test_configuracao_aceita_url_postgresql(
    monkeypatch,
):
    database_url = (
        "postgresql+psycopg://"
        "locadora_app:senha@"
        "localhost:5432/locadora_dev"
    )

    monkeypatch.setenv(
        "LOCADORA_ADMIN_SENHA",
        "senha-de-teste",
    )
    monkeypatch.setenv(
        "LOCADORA_JWT_SECRET",
        "segredo-de-teste",
    )
    monkeypatch.setenv(
        "LOCADORA_DATABASE_URL",
        database_url,
    )

    configuracao = Configuracao()

    assert (
        configuracao.database_url
        == database_url
    )


def test_configuracao_normaliza_url_neon_para_psycopg(
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
    monkeypatch.setenv(
        "LOCADORA_DATABASE_URL",
        (
            "postgresql://usuario:senha@"
            "ep-exemplo-pooler.us-east-1.aws.neon.tech/"
            "neondb?sslmode=require"
        ),
    )

    configuracao = Configuracao()

    assert configuracao.database_url.startswith(
        "postgresql+psycopg://"
    )
    assert "sslmode=require" in (
        configuracao.database_url
    )


def test_configuracao_background_jobs(monkeypatch):
    monkeypatch.setenv(
        "LOCADORA_ADMIN_SENHA",
        "senha-de-teste",
    )
    monkeypatch.setenv(
        "LOCADORA_JWT_SECRET",
        "segredo-de-teste",
    )
    monkeypatch.setenv(
        "LOCADORA_BACKGROUND_JOBS_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "LOCADORA_BACKGROUND_JOBS_INTERVALO_SEGUNDOS",
        "15",
    )
    monkeypatch.setenv(
        "LOCADORA_BACKGROUND_JOBS_LOTE",
        "8",
    )
    monkeypatch.setenv(
        "LOCADORA_BACKGROUND_JOBS_TIMEOUT_BLOQUEIO_SEGUNDOS",
        "120",
    )

    configuracao = Configuracao()

    assert configuracao.background_jobs_enabled is True
    assert configuracao.background_jobs_intervalo_segundos == 15
    assert configuracao.background_jobs_lote == 8
    assert configuracao.background_jobs_timeout_bloqueio_segundos == 120


def test_configuracao_redis_cache(monkeypatch):
    monkeypatch.setenv(
        "LOCADORA_ADMIN_SENHA",
        "senha-de-teste",
    )
    monkeypatch.setenv(
        "LOCADORA_JWT_SECRET",
        "segredo-de-teste",
    )
    monkeypatch.setenv(
        "LOCADORA_REDIS_URL",
        "redis://cache:6379/0",
    )
    monkeypatch.setenv(
        "LOCADORA_REDIS_PREFIXO",
        "locadora-teste",
    )
    monkeypatch.setenv(
        "LOCADORA_REDIS_TIMEOUT_MS",
        "250",
    )
    monkeypatch.setenv(
        "LOCADORA_CACHE_DASHBOARD_TTL_SEGUNDOS",
        "45",
    )

    configuracao = Configuracao()

    assert configuracao.redis_configurado is True
    assert configuracao.redis_url == "redis://cache:6379/0"
    assert configuracao.redis_prefixo == "locadora-teste"
    assert configuracao.redis_timeout_ms == 250
    assert configuracao.cache_dashboard_ttl_segundos == 45


def test_configuracao_redis_e_opcional(monkeypatch):
    monkeypatch.setenv(
        "LOCADORA_ADMIN_SENHA",
        "senha-de-teste",
    )
    monkeypatch.setenv(
        "LOCADORA_JWT_SECRET",
        "segredo-de-teste",
    )
    monkeypatch.delenv(
        "LOCADORA_REDIS_URL",
        raising=False,
    )

    configuracao = Configuracao()

    assert configuracao.redis_configurado is False
    assert configuracao.redis_url is None
    assert configuracao.redis_prefixo == "locadora"
    assert configuracao.cache_dashboard_ttl_segundos == 30
