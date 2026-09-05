from logging.config import fileConfig
import os

from alembic import context
from sqlalchemy import (
    engine_from_config,
    pool,
)

from modulos.config import (
    DATABASE_URL_PADRAO,
)
from modulos.models import (
    Base,
)


config = context.config

if config.config_file_name is not None:
    fileConfig(
        config.config_file_name
    )

database_url = (
    os.getenv(
        "LOCADORA_DATABASE_URL"
    )
    or config.get_main_option(
        "sqlalchemy.url"
    )
    or DATABASE_URL_PADRAO
)

config.set_main_option(
    "sqlalchemy.url",
    database_url.replace(
        "%",
        "%%",
    ),
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def executar_migrations(
    conexao,
) -> None:
    context.configure(
        connection=conexao,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=(
            conexao.dialect.name
            == "sqlite"
        ),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    conexao_injetada = (
        config.attributes.get(
            "connection"
        )
    )

    if conexao_injetada is not None:
        executar_migrations(
            conexao_injetada
        )
        return

    engine = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with engine.connect() as conexao:
        executar_migrations(
            conexao
        )


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
