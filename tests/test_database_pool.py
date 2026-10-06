from unittest.mock import patch

from modulos.database import criar_engine_sqlalchemy


def test_postgresql_recebe_limites_do_pool():
    with patch("modulos.database.create_engine") as criar:
        criar_engine_sqlalchemy(
            "postgresql+psycopg://usuario:senha@localhost/locadora",
            pool_size=3,
            max_overflow=2,
            pool_timeout=15,
        )

    _, kwargs = criar.call_args
    assert kwargs["pool_size"] == 3
    assert kwargs["max_overflow"] == 2
    assert kwargs["pool_timeout"] == 15
    assert kwargs["pool_pre_ping"] is True
    assert kwargs["pool_recycle"] == 300


def test_sqlite_nao_recebe_configuracao_de_pool_postgresql():
    with (
        patch("modulos.database.create_engine") as criar,
        patch(
            "modulos.database.event.listens_for",
            return_value=lambda funcao: funcao,
        ),
    ):
        criar_engine_sqlalchemy(
            "sqlite:///:memory:",
            pool_size=99,
            max_overflow=99,
            pool_timeout=99,
        )

    _, kwargs = criar.call_args
    assert "pool_size" not in kwargs
    assert "max_overflow" not in kwargs
    assert "pool_timeout" not in kwargs
