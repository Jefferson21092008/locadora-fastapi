import pytest

from modulos.config import (
    Configuracao,
    ambiente_atual,
    normalizar_ambiente,
)


def configurar_segredos(monkeypatch):
    monkeypatch.setenv("LOCADORA_ADMIN_SENHA", "senha-de-teste")
    monkeypatch.setenv("LOCADORA_JWT_SECRET", "segredo-de-teste")


def test_normaliza_aliases_de_ambiente():
    assert normalizar_ambiente("dev") == "development"
    assert normalizar_ambiente("stage") == "staging"
    assert normalizar_ambiente("prod") == "production"
    assert normalizar_ambiente("testing") == "test"


def test_ambiente_invalido_falha_cedo(monkeypatch):
    monkeypatch.setenv("LOCADORA_AMBIENTE", "laboratorio")

    with pytest.raises(RuntimeError, match="LOCADORA_AMBIENTE inválido"):
        ambiente_atual()


def test_development_mantem_sqlite_local(monkeypatch):
    configurar_segredos(monkeypatch)
    monkeypatch.setenv("LOCADORA_AMBIENTE", "development")
    monkeypatch.delenv("LOCADORA_DATABASE_URL", raising=False)

    configuracao = Configuracao()

    assert configuracao.em_desenvolvimento is True
    assert configuracao.database_url.startswith("sqlite:///")
    assert configuracao.redis_prefixo == "locadora:development"


def test_test_e_ambiente_explicitamente_suportado(monkeypatch):
    configurar_segredos(monkeypatch)
    monkeypatch.setenv("LOCADORA_AMBIENTE", "test")

    configuracao = Configuracao()

    assert configuracao.em_teste is True
    assert configuracao.ambiente == "test"


@pytest.mark.parametrize("ambiente", ["staging", "production"])
def test_ambiente_remoto_nao_aceita_fallback_sqlite(monkeypatch, ambiente):
    configurar_segredos(monkeypatch)
    monkeypatch.setenv("LOCADORA_AMBIENTE", ambiente)
    monkeypatch.delenv("LOCADORA_DATABASE_URL", raising=False)
    monkeypatch.setenv("LOCADORA_PUBLIC_URL", f"https://{ambiente}.example")

    with pytest.raises(RuntimeError, match="LOCADORA_DATABASE_URL"):
        Configuracao()


@pytest.mark.parametrize("ambiente", ["staging", "production"])
def test_ambiente_remoto_exige_postgresql(monkeypatch, ambiente):
    configurar_segredos(monkeypatch)
    monkeypatch.setenv("LOCADORA_AMBIENTE", ambiente)
    monkeypatch.setenv("LOCADORA_DATABASE_URL", "sqlite:///dados/inseguro.db")
    monkeypatch.setenv("LOCADORA_PUBLIC_URL", f"https://{ambiente}.example")

    with pytest.raises(RuntimeError, match="devem usar PostgreSQL"):
        Configuracao()


@pytest.mark.parametrize("ambiente", ["staging", "production"])
def test_ambiente_remoto_exige_https(monkeypatch, ambiente):
    configurar_segredos(monkeypatch)
    monkeypatch.setenv("LOCADORA_AMBIENTE", ambiente)
    monkeypatch.setenv(
        "LOCADORA_DATABASE_URL",
        "postgresql://usuario:senha@localhost:5432/locadora",
    )
    monkeypatch.setenv("LOCADORA_PUBLIC_URL", "http://locadora.example")

    with pytest.raises(RuntimeError, match="deve usar HTTPS"):
        Configuracao()


@pytest.mark.parametrize("ambiente", ["staging", "production"])
def test_ambiente_remoto_aceita_postgresql_https(monkeypatch, ambiente):
    configurar_segredos(monkeypatch)
    monkeypatch.setenv("LOCADORA_AMBIENTE", ambiente)
    monkeypatch.setenv(
        "LOCADORA_DATABASE_URL",
        "postgresql://usuario:senha@localhost:5432/locadora",
    )
    monkeypatch.setenv("LOCADORA_PUBLIC_URL", f"https://{ambiente}.example")
    monkeypatch.delenv("LOCADORA_REDIS_PREFIXO", raising=False)

    configuracao = Configuracao()

    assert configuracao.ambiente == ambiente
    assert configuracao.database_url.startswith("postgresql+psycopg://")
    assert configuracao.redis_prefixo == f"locadora:{ambiente}"
