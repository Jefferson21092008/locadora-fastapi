import os

import pytest

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.engine import (
    make_url,
)
from sqlalchemy.exc import (
    IntegrityError,
)

from modulos.container import (
    Container,
)
from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.usuarios import (
    Role,
)


load_dotenv()


pytestmark = pytest.mark.postgresql


TABELAS_ESPERADAS = {
    "alembic_version",
    "alugueis",
    "clientes",
    "manutencoes",
    "tokens_recuperacao_senha",
    "usuarios",
    "veiculos",
}


def obter_url_postgresql_teste():
    database_url = os.getenv(
        "LOCADORA_TEST_DATABASE_URL"
    )

    if not database_url:
        pytest.skip(
            "LOCADORA_TEST_DATABASE_URL não foi configurada."
        )

    url = make_url(
        database_url
    )

    if (
        url.get_backend_name()
        != "postgresql"
    ):
        pytest.fail(
            "LOCADORA_TEST_DATABASE_URL deve apontar "
            "para PostgreSQL."
        )

    if url.database != "locadora_test":
        pytest.fail(
            "Por segurança, os testes destrutivos aceitam "
            "somente o banco locadora_test."
        )

    if url.username != "locadora_app":
        pytest.fail(
            "Os testes devem usar o usuário limitado "
            "locadora_app."
        )

    return database_url


def recriar_schema_public(database_url):
    engine = create_engine(
        database_url
    )

    try:
        with engine.begin() as conexao:
            banco_atual = conexao.scalar(
                text(
                    "SELECT current_database()"
                )
            )
            usuario_atual = conexao.scalar(
                text(
                    "SELECT current_user"
                )
            )

            if (
                banco_atual
                != "locadora_test"
                or usuario_atual
                != "locadora_app"
            ):
                pytest.fail(
                    "A conexão real não corresponde ao banco "
                    "locadora_test e ao usuário locadora_app."
                )

            conexao.exec_driver_sql(
                "DROP SCHEMA IF EXISTS public CASCADE"
            )
            conexao.exec_driver_sql(
                "CREATE SCHEMA public"
            )

    finally:
        engine.dispose()


@pytest.fixture
def banco_postgresql():
    database_url = (
        obter_url_postgresql_teste()
    )
    recriar_schema_public(
        database_url
    )

    banco = BancoSQLAlchemy(
        database_url
    )

    try:
        banco.aplicar_migrations()
        yield banco

    finally:
        banco.fechar()
        recriar_schema_public(
            database_url
        )


def test_postgresql_conecta_com_usuario_limitado(
    banco_postgresql,
):
    assert (
        banco_postgresql.testar_conexao()
        is True
    )

    with banco_postgresql.engine.connect() as conexao:
        identidade = conexao.execute(
            text(
                "SELECT current_user, current_database()"
            )
        ).one()

    assert tuple(identidade) == (
        "locadora_app",
        "locadora_test",
    )


def test_alembic_cria_schema_postgresql_completo(
    banco_postgresql,
):
    inspetor = inspect(
        banco_postgresql.engine
    )

    assert set(
        inspetor.get_table_names()
    ) == TABELAS_ESPERADAS

    with banco_postgresql.engine.connect() as conexao:
        revisao = conexao.scalar(
            text(
                "SELECT version_num "
                "FROM alembic_version"
            )
        )

    assert revisao == "20260903_0001"

    fks_clientes = (
        inspetor.get_foreign_keys(
            "clientes"
        )
    )

    assert any(
        fk["referred_table"]
        == "usuarios"
        for fk in fks_clientes
    )

    colunas_usuarios = {
        coluna["name"]: coluna
        for coluna in inspetor.get_columns(
            "usuarios"
        )
    }

    assert isinstance(
        colunas_usuarios["ativo"]["type"],
        Boolean,
    )


def test_indice_permite_apenas_uma_manutencao_ativa(
    banco_postgresql,
):
    with banco_postgresql.engine.begin() as conexao:
        veiculo_id = conexao.scalar(
            text(
                """
                INSERT INTO veiculos (
                    tipo, modelo, ano, diaria, preco_km,
                    quilometragem, status, disponivel,
                    alugado_por, ativo
                ) VALUES (
                    'Carro', 'Teste PostgreSQL', 2026,
                    150, 1, 0, 'manutencao', FALSE,
                    NULL, TRUE
                )
                RETURNING id
                """
            )
        )

        conexao.execute(
            text(
                """
                INSERT INTO manutencoes (
                    veiculo_id, motivo, quilometragem,
                    custo, data_inicio, data_fim, status
                ) VALUES (
                    :veiculo_id, 'Revisão anterior', 0,
                    100, '2026-09-01', '2026-09-02',
                    'finalizada'
                )
                """
            ),
            {
                "veiculo_id": veiculo_id,
            },
        )

        conexao.execute(
            text(
                """
                INSERT INTO manutencoes (
                    veiculo_id, motivo, quilometragem,
                    custo, data_inicio, data_fim, status
                ) VALUES (
                    :veiculo_id, 'Revisão atual', 0,
                    0, '2026-09-05', NULL, 'ativa'
                )
                """
            ),
            {
                "veiculo_id": veiculo_id,
            },
        )

    with pytest.raises(
        IntegrityError
    ):
        with banco_postgresql.engine.begin() as conexao:
            conexao.execute(
                text(
                    """
                    INSERT INTO manutencoes (
                        veiculo_id, motivo, quilometragem,
                        custo, data_inicio, data_fim, status
                    ) VALUES (
                        :veiculo_id, 'Duplicada', 0,
                        0, '2026-09-05', NULL, 'ativa'
                    )
                    """
                ),
                {
                    "veiculo_id": veiculo_id,
                },
            )


class ConfiguracaoPostgreSQLTeste:
    admin_usuario = "admin_postgresql"
    admin_senha = "SenhaAdmin123"
    jwt_secret = "segredo-postgresql-de-teste"
    email_configurado = False

    def __init__(
        self,
        database_url,
    ):
        self.database_url = database_url


def test_container_e_repository_funcionam_no_postgresql(
    banco_postgresql,
):
    config = ConfiguracaoPostgreSQLTeste(
        banco_postgresql.database_url
    )
    container = Container(
        config=config,
        banco_sqlalchemy=banco_postgresql,
    )

    administrador = (
        container.usuario_repository
        .buscar_por_usuario(
            "ADMIN_POSTGRESQL"
        )
    )

    assert administrador is not None
    assert administrador.role == Role.ADMIN
