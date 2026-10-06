from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from modulos.config import Configuracao
from modulos.container import Container
from modulos.escala_horizontal import (
    escala_horizontal_habilitada,
    identificador_instancia,
    workers_embutidos_habilitados,
)
from modulos.usuarios import Role


def configurar_base(monkeypatch):
    monkeypatch.setenv("LOCADORA_ADMIN_SENHA", "Senha123")
    monkeypatch.setenv("LOCADORA_JWT_SECRET", "segredo-teste")
    monkeypatch.setenv(
        "LOCADORA_DATABASE_URL",
        "postgresql://usuario:senha@localhost:5432/locadora",
    )
    monkeypatch.setenv("LOCADORA_REDIS_URL", "redis://cache:6379/0")


def test_flags_de_escala_desabilitam_workers_embutidos_por_padrao(monkeypatch):
    monkeypatch.setenv("LOCADORA_ESCALA_HORIZONTAL_ENABLED", "true")
    monkeypatch.delenv("LOCADORA_WORKERS_EMBUTIDOS", raising=False)

    assert escala_horizontal_habilitada() is True
    assert workers_embutidos_habilitados() is False


def test_configuracao_de_escala_exige_infra_compartilhada(monkeypatch):
    configurar_base(monkeypatch)
    monkeypatch.setenv("LOCADORA_ESCALA_HORIZONTAL_ENABLED", "true")
    monkeypatch.setenv("LOCADORA_WORKERS_EMBUTIDOS", "false")
    monkeypatch.setenv("LOCADORA_CONTAINER_APLICAR_MIGRATIONS", "false")

    configuracao = Configuracao()

    assert configuracao.escala_horizontal_enabled is True
    assert configuracao.workers_embutidos is False
    assert configuracao.container_aplicar_migrations is False


def test_escala_horizontal_rejeita_redis_ausente(monkeypatch):
    configurar_base(monkeypatch)
    monkeypatch.setenv("LOCADORA_ESCALA_HORIZONTAL_ENABLED", "true")
    monkeypatch.setenv("LOCADORA_WORKERS_EMBUTIDOS", "false")
    monkeypatch.setenv("LOCADORA_CONTAINER_APLICAR_MIGRATIONS", "false")
    monkeypatch.delenv("LOCADORA_REDIS_URL", raising=False)

    with pytest.raises(RuntimeError, match="REDIS"):
        Configuracao()


def test_escala_horizontal_rejeita_workers_embutidos(monkeypatch):
    configurar_base(monkeypatch)
    monkeypatch.setenv("LOCADORA_ESCALA_HORIZONTAL_ENABLED", "true")
    monkeypatch.setenv("LOCADORA_WORKERS_EMBUTIDOS", "true")
    monkeypatch.setenv("LOCADORA_CONTAINER_APLICAR_MIGRATIONS", "false")

    with pytest.raises(RuntimeError, match="WORKERS_EMBUTIDOS"):
        Configuracao()


def test_escala_horizontal_rejeita_migration_em_cada_replica(monkeypatch):
    configurar_base(monkeypatch)
    monkeypatch.setenv("LOCADORA_ESCALA_HORIZONTAL_ENABLED", "true")
    monkeypatch.setenv("LOCADORA_WORKERS_EMBUTIDOS", "false")
    monkeypatch.setenv("LOCADORA_CONTAINER_APLICAR_MIGRATIONS", "true")

    with pytest.raises(RuntimeError, match="APLICAR_MIGRATIONS"):
        Configuracao()


def test_pool_de_conexoes_e_configuravel(monkeypatch):
    configurar_base(monkeypatch)
    monkeypatch.setenv("LOCADORA_DB_POOL_SIZE", "4")
    monkeypatch.setenv("LOCADORA_DB_MAX_OVERFLOW", "1")
    monkeypatch.setenv("LOCADORA_DB_POOL_TIMEOUT_SEGUNDOS", "12")

    configuracao = Configuracao()

    assert configuracao.db_pool_size == 4
    assert configuracao.db_max_overflow == 1
    assert configuracao.db_pool_timeout_segundos == 12


def test_identificador_instancia_explicito(monkeypatch):
    identificador_instancia.cache_clear()
    monkeypatch.setenv("LOCADORA_INSTANCIA_ID", "api-teste-2")

    try:
        assert identificador_instancia() == "api-teste-2"
    finally:
        identificador_instancia.cache_clear()


def test_identificador_instancia_rejeita_valor_inseguro(monkeypatch):
    identificador_instancia.cache_clear()
    monkeypatch.setenv("LOCADORA_INSTANCIA_ID", "api com espaco")

    try:
        with pytest.raises(RuntimeError, match="LOCADORA_INSTANCIA_ID"):
            identificador_instancia()
    finally:
        identificador_instancia.cache_clear()


def test_admin_padrao_tolera_corrida_entre_replicas():
    admin = SimpleNamespace(role=Role.ADMIN)

    class AuthServiceFake:
        def __init__(self):
            self.buscas = 0

        def buscar_por_usuario(self, _usuario):
            self.buscas += 1
            if self.buscas == 1:
                return None
            return admin

        def criar_usuario(self, **_kwargs):
            raise IntegrityError(
                "INSERT",
                {},
                RuntimeError("duplicado"),
            )

    container = Container.__new__(Container)
    container.config = SimpleNamespace(
        admin_usuario="admin",
        admin_senha="Senha123",
    )
    container.auth_service = AuthServiceFake()

    container._garantir_admin_padrao()

    assert container.auth_service.buscas == 2
