from unittest.mock import patch

import pytest

from modulos import container_entrypoint


def test_ler_booleano_ambiente_usa_padrao(monkeypatch):
    monkeypatch.delenv("LOCADORA_EXECUTAR_MIGRATIONS", raising=False)

    assert container_entrypoint.ler_booleano_ambiente(
        "LOCADORA_EXECUTAR_MIGRATIONS",
        True,
    ) is True


@pytest.mark.parametrize("valor", ["1", "true", "YES", "on"])
def test_ler_booleano_ambiente_aceita_true(monkeypatch, valor):
    monkeypatch.setenv("FLAG_TESTE", valor)
    assert container_entrypoint.ler_booleano_ambiente("FLAG_TESTE", False) is True


@pytest.mark.parametrize("valor", ["0", "false", "NO", "off"])
def test_ler_booleano_ambiente_aceita_false(monkeypatch, valor):
    monkeypatch.setenv("FLAG_TESTE", valor)
    assert container_entrypoint.ler_booleano_ambiente("FLAG_TESTE", True) is False


def test_ler_booleano_ambiente_rejeita_valor_invalido(monkeypatch):
    monkeypatch.setenv("FLAG_TESTE", "talvez")

    with pytest.raises(RuntimeError, match="FLAG_TESTE deve ser"):
        container_entrypoint.ler_booleano_ambiente("FLAG_TESTE", True)


def test_obter_porta_usa_padrao(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    assert container_entrypoint.obter_porta() == 10000


@pytest.mark.parametrize("valor", ["0", "65536", "abc"])
def test_obter_porta_rejeita_valores_invalidos(monkeypatch, valor):
    monkeypatch.setenv("PORT", valor)

    with pytest.raises(RuntimeError, match="PORT deve"):
        container_entrypoint.obter_porta()


def test_comando_uvicorn_endurecido():
    comando = container_entrypoint.comando_uvicorn(8123)

    assert comando[:4] == [
        container_entrypoint.sys.executable,
        "-m",
        "uvicorn",
        "api.main:app",
    ]
    assert "0.0.0.0" in comando
    assert "8123" in comando
    assert "--no-server-header" in comando


def test_executar_migrations_sem_shell():
    with patch.object(container_entrypoint.subprocess, "run") as executar:
        container_entrypoint.executar_migrations()

    executar.assert_called_once_with(
        [
            container_entrypoint.sys.executable,
            "-m",
            "alembic",
            "upgrade",
            "head",
        ],
        check=True,
    )


def test_main_executa_migration_e_substitui_pid(monkeypatch):
    monkeypatch.setenv("LOCADORA_EXECUTAR_MIGRATIONS", "true")
    monkeypatch.setenv("PORT", "9000")

    with (
        patch.object(container_entrypoint, "executar_migrations") as migrar,
        patch.object(container_entrypoint.os, "execv") as execv,
    ):
        container_entrypoint.main()

    migrar.assert_called_once_with()
    comando = container_entrypoint.comando_uvicorn(9000)
    execv.assert_called_once_with(container_entrypoint.sys.executable, comando)


def test_main_pode_pular_migration(monkeypatch):
    monkeypatch.setenv("LOCADORA_EXECUTAR_MIGRATIONS", "false")

    with (
        patch.object(container_entrypoint, "executar_migrations") as migrar,
        patch.object(container_entrypoint.os, "execv"),
    ):
        container_entrypoint.main()

    migrar.assert_not_called()

def test_main_bloqueia_migration_em_replica_horizontal(monkeypatch):
    monkeypatch.setenv("LOCADORA_ESCALA_HORIZONTAL_ENABLED", "true")
    monkeypatch.setenv("LOCADORA_EXECUTAR_MIGRATIONS", "true")

    with pytest.raises(RuntimeError, match="migrations fora das réplicas"):
        container_entrypoint.main()
