from pathlib import Path

from alembic import (
    command,
)
from alembic.config import (
    Config,
)

from sqlalchemy import (
    create_engine,
    event,
    text,
)
from sqlalchemy.engine import (
    make_url,
)

from sqlalchemy.orm import (
    sessionmaker,
)


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

ALEMBIC_INI = (
    BASE_DIR
    / "alembic.ini"
)


# ================================================================
# ENGINE
# ================================================================


def criar_engine_sqlalchemy(
    database_url,
):
    argumentos_conexao = {}
    backend = (
        make_url(
            database_url
        ).get_backend_name()
    )

    if backend == "sqlite":
        argumentos_conexao[
            "check_same_thread"
        ] = False

    argumentos_engine = {
        "connect_args": (
            argumentos_conexao
        ),
        "pool_pre_ping": True,
    }

    if backend == "postgresql":
        argumentos_engine[
            "pool_recycle"
        ] = 300

    engine = create_engine(
        database_url,
        **argumentos_engine,
    )

    if backend == "sqlite":
        @event.listens_for(
            engine,
            "connect",
        )
        def ativar_foreign_keys(
            dbapi_connection,
            connection_record,
        ):
            cursor = (
                dbapi_connection
                .cursor()
            )

            cursor.execute(
                "PRAGMA foreign_keys = ON"
            )

            cursor.close()

    return engine


# ================================================================
# BANCO SQLALCHEMY
# ================================================================


class BancoSQLAlchemy:
    """
    Centraliza o Engine, a criação das
    sessões e a estrutura ORM da aplicação.

    A partir desta etapa, esta é a infraestrutura
    principal de persistência usada pelo Container.
    """

    def __init__(
        self,
        database_url,
    ):
        self.database_url = (
            database_url
        )

        self.engine = (
            criar_engine_sqlalchemy(
                database_url
            )
        )

        self.SessionLocal = (
            sessionmaker(
                bind=self.engine,
                autoflush=False,
                expire_on_commit=False,
            )
        )

    def aplicar_migrations(
        self,
    ):
        """
        Atualiza a estrutura do banco até a
        revisão mais recente do Alembic.
        """
        configuracao = Config(
            str(ALEMBIC_INI)
        )

        configuracao.set_main_option(
            "sqlalchemy.url",
            self.database_url.replace(
                "%",
                "%%",
            ),
        )
        configuracao.attributes[
            "database_url_override"
        ] = self.database_url

        with self.engine.connect() as conexao:
            configuracao.attributes[
                "connection"
            ] = conexao

            command.upgrade(
                configuracao,
                "head",
            )

    def criar_sessao(
        self,
    ):
        return self.SessionLocal()

    def testar_conexao(
        self,
    ):
        with self.engine.connect() as conexao:
            resultado = conexao.scalar(
                text(
                    "SELECT 1"
                )
            )

        return resultado == 1

    def fechar(
        self,
    ):
        self.engine.dispose()
