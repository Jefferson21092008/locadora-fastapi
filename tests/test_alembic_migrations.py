import sqlite3

from alembic import (
    command,
)
from alembic.autogenerate import (
    compare_metadata,
)
from alembic.config import (
    Config,
)
from alembic.migration import (
    MigrationContext,
)
from sqlalchemy import (
    create_engine,
    inspect,
    text,
)

from modulos.models import (
    Base,
)


TABELAS_ESPERADAS = {
    "usuarios",
    "clientes",
    "veiculos",
    "alugueis",
    "manutencoes",
    "tokens_recuperacao_senha",
}


def criar_configuracao(
    database_url,
):
    configuracao = Config(
        "alembic.ini"
    )
    configuracao.set_main_option(
        "sqlalchemy.url",
        database_url,
    )
    return configuracao


def criar_schema_legado(
    caminho,
):
    with sqlite3.connect(
        caminho
    ) as conexao:
        conexao.executescript(
            """
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                usuario TEXT NOT NULL,
                senha_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL
            );

            CREATE TABLE veiculos (
                id INTEGER PRIMARY KEY,
                tipo TEXT NOT NULL,
                modelo TEXT NOT NULL,
                ano INTEGER NOT NULL,
                diaria REAL NOT NULL,
                preco_km REAL NOT NULL,
                disponivel INTEGER NOT NULL DEFAULT 1,
                alugado_por TEXT,
                ativo INTEGER NOT NULL DEFAULT 1,
                quilometragem REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'disponivel'
            );

            CREATE TABLE clientes (
                id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                usuario TEXT NOT NULL,
                email TEXT NOT NULL,
                senha_hash TEXT NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1,
                usuario_id INTEGER
            );

            CREATE TABLE alugueis (
                id INTEGER PRIMARY KEY,
                cliente_id INTEGER NOT NULL,
                veiculo_id INTEGER NOT NULL,
                cliente_usuario TEXT NOT NULL,
                cliente_nome TEXT NOT NULL,
                veiculo_tipo TEXT NOT NULL,
                veiculo_modelo TEXT NOT NULL,
                dias INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'ativo',
                km REAL NOT NULL DEFAULT 0,
                pagamento TEXT,
                valor REAL NOT NULL DEFAULT 0,
                data_inicio TEXT NOT NULL,
                data_prevista TEXT NOT NULL,
                data_fim TEXT,
                dias_atraso INTEGER NOT NULL DEFAULT 0,
                multa REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE manutencoes (
                id INTEGER PRIMARY KEY,
                veiculo_id INTEGER NOT NULL,
                motivo TEXT NOT NULL,
                quilometragem REAL NOT NULL,
                custo REAL NOT NULL DEFAULT 0,
                data_inicio TEXT NOT NULL,
                data_fim TEXT,
                status TEXT NOT NULL DEFAULT 'ativa'
            );

            CREATE TABLE tokens_recuperacao_senha (
                id INTEGER PRIMARY KEY,
                usuario_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL,
                expira_em TEXT NOT NULL,
                usado INTEGER NOT NULL DEFAULT 0,
                criado_em TEXT NOT NULL,
                usado_em TEXT
            );

            INSERT INTO usuarios VALUES (
                1, 'admin', 'hash', 'admin', 1,
                '2026-09-03T10:00:00'
            );
            INSERT INTO veiculos VALUES (
                1, 'Carro', 'Civic', 2025, 150, 0.5,
                1, NULL, 1, 12345, 'disponivel'
            );
            INSERT INTO clientes VALUES (
                1, 'Lucas', 'lucas', 'lucas@email.com',
                '', 1, 1
            );
            INSERT INTO alugueis VALUES (
                1, 1, 1, 'lucas', 'Lucas', 'Carro',
                'Civic', 2, 'finalizado', 100, 'Pix',
                350, '2026-09-01', '2026-09-03',
                '2026-09-03', 0, 0
            );
            INSERT INTO manutencoes VALUES (
                1, 1, 'Revisao', 12345, 200,
                '2026-08-01', '2026-08-02', 'finalizada'
            );
            INSERT INTO tokens_recuperacao_senha VALUES (
                1, 1,
                'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                '2026-09-03T10:15:00', 1,
                '2026-09-03T10:00:00',
                '2026-09-03T10:05:00'
            );
            """
        )


def test_upgrade_head_cria_schema_completo(
    tmp_path,
):
    caminho = (
        tmp_path
        / "alembic_novo.db"
    )
    database_url = (
        f"sqlite:///{caminho.as_posix()}"
    )

    command.upgrade(
        criar_configuracao(
            database_url
        ),
        "head",
    )

    engine = create_engine(
        database_url
    )

    try:
        inspetor = inspect(engine)
        tabelas = set(
            inspetor.get_table_names()
        )

        assert {
            "alembic_version",
            *TABELAS_ESPERADAS,
        } == tabelas

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

        checks_veiculos = {
            check["name"]
            for check in (
                inspetor
                .get_check_constraints(
                    "veiculos"
                )
            )
        }

        assert (
            "ck_veiculos_status"
            in checks_veiculos
        )

    finally:
        engine.dispose()


def test_schema_migrado_corresponde_aos_models(
    tmp_path,
):
    caminho = (
        tmp_path
        / "alembic_models.db"
    )
    database_url = (
        f"sqlite:///{caminho.as_posix()}"
    )

    command.upgrade(
        criar_configuracao(
            database_url
        ),
        "head",
    )

    engine = create_engine(
        database_url
    )

    try:
        with engine.connect() as conexao:
            contexto = (
                MigrationContext
                .configure(
                    conexao,
                    opts={
                        "compare_type": True,
                    },
                )
            )

            diferencas = (
                compare_metadata(
                    contexto,
                    Base.metadata,
                )
            )

        assert diferencas == []

    finally:
        engine.dispose()


def test_downgrade_base_remove_schema(
    tmp_path,
):
    caminho = (
        tmp_path
        / "alembic_downgrade.db"
    )
    database_url = (
        f"sqlite:///{caminho.as_posix()}"
    )
    configuracao = criar_configuracao(
        database_url
    )

    command.upgrade(
        configuracao,
        "head",
    )
    command.downgrade(
        configuracao,
        "base",
    )

    engine = create_engine(
        database_url
    )

    try:
        tabelas = set(
            inspect(
                engine
            ).get_table_names()
        )

        assert not (
            tabelas
            & TABELAS_ESPERADAS
        )

    finally:
        engine.dispose()


def test_upgrade_registra_revisao_atual(
    tmp_path,
):
    caminho = (
        tmp_path
        / "alembic_versao.db"
    )
    database_url = (
        f"sqlite:///{caminho.as_posix()}"
    )

    command.upgrade(
        criar_configuracao(
            database_url
        ),
        "head",
    )

    engine = create_engine(
        database_url
    )

    try:
        with engine.connect() as conexao:
            revisao = conexao.scalar(
                text(
                    "SELECT version_num "
                    "FROM alembic_version"
                )
            )

        assert revisao == "20260903_0001"

    finally:
        engine.dispose()


def test_upgrade_preserva_dados_do_schema_legado(
    tmp_path,
):
    caminho = (
        tmp_path
        / "alembic_legado.db"
    )
    criar_schema_legado(
        caminho
    )
    database_url = (
        f"sqlite:///{caminho.as_posix()}"
    )

    command.upgrade(
        criar_configuracao(
            database_url
        ),
        "head",
    )

    engine = create_engine(
        database_url
    )

    try:
        with engine.connect() as conexao:
            veiculo = conexao.execute(
                text(
                    "SELECT quilometragem, status, "
                    "disponivel, ativo "
                    "FROM veiculos WHERE id = 1"
                )
            ).one()

            assert tuple(veiculo) == (
                12345.0,
                "disponivel",
                1,
                1,
            )

            for tabela in TABELAS_ESPERADAS:
                total = conexao.scalar(
                    text(
                        f"SELECT COUNT(*) "
                        f"FROM {tabela}"
                    )
                )
                assert total == 1

            contexto = (
                MigrationContext
                .configure(
                    conexao,
                    opts={
                        "compare_type": True,
                    },
                )
            )

            assert compare_metadata(
                contexto,
                Base.metadata,
            ) == []

    finally:
        engine.dispose()
