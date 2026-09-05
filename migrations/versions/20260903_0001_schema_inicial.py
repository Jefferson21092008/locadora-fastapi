"""Cria e alinha o schema inicial da Locadora.

Revision ID: 20260903_0001
Revises:
Create Date: 2026-09-03
"""

from collections.abc import (
    Sequence,
)

from alembic import op
from sqlalchemy import (
    inspect,
)
import sqlalchemy as sa


revision: str = "20260903_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TABELAS_APLICACAO = {
    "usuarios",
    "clientes",
    "veiculos",
    "alugueis",
    "manutencoes",
    "tokens_recuperacao_senha",
}


def _string_case_insensitive(
    tamanho,
):
    """
    Usa NOCASE somente no SQLite.

    O PostgreSQL não possui essa collation por padrão. As buscas
    continuam case-insensitive porque os repositories usam lower().
    """
    return sa.String(tamanho).with_variant(
        sa.String(
            tamanho,
            collation="NOCASE",
        ),
        "sqlite",
    )


def _criar_schema() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario", sa.String(100), nullable=False),
        sa.Column("senha_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.String(40), nullable=False),
        sa.CheckConstraint(
            "ativo IN (TRUE, FALSE)",
            name="ck_usuarios_ativo",
        ),
        sa.CheckConstraint(
            "role IN ('cliente', 'admin')",
            name="ck_usuarios_role",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_usuarios"),
        ),
        sa.UniqueConstraint(
            "usuario",
            name=op.f("uq_usuarios_usuario"),
        ),
    )

    op.create_table(
        "veiculos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("modelo", sa.String(150), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("diaria", sa.Float(), nullable=False),
        sa.Column("preco_km", sa.Float(), nullable=False),
        sa.Column("quilometragem", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("disponivel", sa.Boolean(), nullable=False),
        sa.Column("alugado_por", sa.String(100), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "ano >= 1900",
            name="ck_veiculos_ano",
        ),
        sa.CheckConstraint(
            "ativo IN (TRUE, FALSE)",
            name="ck_veiculos_ativo",
        ),
        sa.CheckConstraint(
            "diaria > 0",
            name="ck_veiculos_diaria",
        ),
        sa.CheckConstraint(
            "disponivel IN (TRUE, FALSE)",
            name="ck_veiculos_disponivel",
        ),
        sa.CheckConstraint(
            "preco_km >= 0",
            name="ck_veiculos_preco_km",
        ),
        sa.CheckConstraint(
            "status IN ("
            "'disponivel', 'alugado', "
            "'manutencao', 'desativado'"
            ")",
            name="ck_veiculos_status",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_veiculos"),
        ),
    )

    op.create_table(
        "clientes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column(
            "usuario",
            _string_case_insensitive(100),
            nullable=False,
        ),
        sa.Column(
            "email",
            _string_case_insensitive(255),
            nullable=False,
        ),
        sa.Column("senha_hash", sa.Text(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f(
                "fk_clientes_usuario_id_usuarios"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_clientes"),
        ),
        sa.UniqueConstraint(
            "email",
            name=op.f("uq_clientes_email"),
        ),
        sa.UniqueConstraint(
            "usuario",
            name=op.f("uq_clientes_usuario"),
        ),
        sa.UniqueConstraint(
            "usuario_id",
            name=op.f("uq_clientes_usuario_id"),
        ),
    )

    op.create_table(
        "alugueis",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("veiculo_id", sa.Integer(), nullable=False),
        sa.Column("cliente_usuario", sa.String(100), nullable=False),
        sa.Column("cliente_nome", sa.String(150), nullable=False),
        sa.Column("veiculo_tipo", sa.String(50), nullable=False),
        sa.Column("veiculo_modelo", sa.String(150), nullable=False),
        sa.Column("dias", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("km", sa.Float(), nullable=False),
        sa.Column("pagamento", sa.String(100), nullable=True),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("data_inicio", sa.String(30), nullable=False),
        sa.Column("data_prevista", sa.String(30), nullable=False),
        sa.Column("data_fim", sa.String(30), nullable=True),
        sa.Column("dias_atraso", sa.Integer(), nullable=False),
        sa.Column("multa", sa.Float(), nullable=False),
        sa.CheckConstraint(
            "dias > 0",
            name="ck_alugueis_dias",
        ),
        sa.CheckConstraint(
            "dias_atraso >= 0",
            name="ck_alugueis_dias_atraso",
        ),
        sa.CheckConstraint(
            "km >= 0",
            name="ck_alugueis_km",
        ),
        sa.CheckConstraint(
            "multa >= 0",
            name="ck_alugueis_multa",
        ),
        sa.CheckConstraint(
            "status IN ('ativo', 'finalizado')",
            name="ck_alugueis_status",
        ),
        sa.CheckConstraint(
            "valor >= 0",
            name="ck_alugueis_valor",
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clientes.id"],
            name=op.f(
                "fk_alugueis_cliente_id_clientes"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["veiculo_id"],
            ["veiculos.id"],
            name=op.f(
                "fk_alugueis_veiculo_id_veiculos"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_alugueis"),
        ),
    )

    op.create_table(
        "manutencoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("veiculo_id", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.String(), nullable=False),
        sa.Column("quilometragem", sa.Float(), nullable=False),
        sa.Column("custo", sa.Float(), nullable=False),
        sa.Column("data_inicio", sa.String(30), nullable=False),
        sa.Column("data_fim", sa.String(30), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.CheckConstraint(
            "custo >= 0",
            name="ck_manutencoes_custo",
        ),
        sa.CheckConstraint(
            "quilometragem >= 0",
            name="ck_manutencoes_quilometragem",
        ),
        sa.CheckConstraint(
            "status IN ('ativa', 'finalizada')",
            name="ck_manutencoes_status",
        ),
        sa.ForeignKeyConstraint(
            ["veiculo_id"],
            ["veiculos.id"],
            name=op.f(
                "fk_manutencoes_veiculo_id_veiculos"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_manutencoes"),
        ),
    )

    op.create_index(
        "idx_manutencao_ativa_veiculo",
        "manutencoes",
        ["veiculo_id"],
        unique=True,
        sqlite_where=sa.text(
            "status = 'ativa'"
        ),
        postgresql_where=sa.text(
            "status = 'ativa'"
        ),
    )

    op.create_table(
        "tokens_recuperacao_senha",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expira_em", sa.String(40), nullable=False),
        sa.Column("usado", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.String(40), nullable=False),
        sa.Column("usado_em", sa.String(40), nullable=True),
        sa.CheckConstraint(
            "usado IN (TRUE, FALSE)",
            name="ck_tokens_recuperacao_usado",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f(
                "fk_tokens_recuperacao_senha_"
                "usuario_id_usuarios"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_tokens_recuperacao_senha"
            ),
        ),
        sa.UniqueConstraint(
            "token_hash",
            name=op.f(
                "uq_tokens_recuperacao_senha_token_hash"
            ),
        ),
    )

    op.create_index(
        "idx_tokens_recuperacao_usuario",
        "tokens_recuperacao_senha",
        ["usuario_id"],
        unique=False,
    )


def _sql_tabela_temporaria(
    tabela,
) -> str:
    prefixo = "alembic_nova_"

    definicoes = {
        "usuarios": """
            id INTEGER NOT NULL,
            usuario VARCHAR(100) NOT NULL,
            senha_hash TEXT NOT NULL,
            role VARCHAR(20) NOT NULL,
            ativo BOOLEAN NOT NULL,
            criado_em VARCHAR(40) NOT NULL,
            CONSTRAINT pk_usuarios PRIMARY KEY (id),
            CONSTRAINT ck_usuarios_role
                CHECK (role IN ('cliente', 'admin')),
            CONSTRAINT ck_usuarios_ativo
                CHECK (ativo IN (0, 1)),
            CONSTRAINT uq_usuarios_usuario UNIQUE (usuario)
        """,
        "veiculos": """
            id INTEGER NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            modelo VARCHAR(150) NOT NULL,
            ano INTEGER NOT NULL,
            diaria FLOAT NOT NULL,
            preco_km FLOAT NOT NULL,
            quilometragem FLOAT NOT NULL,
            status VARCHAR(20) NOT NULL,
            disponivel BOOLEAN NOT NULL,
            alugado_por VARCHAR(100),
            ativo BOOLEAN NOT NULL,
            CONSTRAINT pk_veiculos PRIMARY KEY (id),
            CONSTRAINT ck_veiculos_ano CHECK (ano >= 1900),
            CONSTRAINT ck_veiculos_diaria CHECK (diaria > 0),
            CONSTRAINT ck_veiculos_preco_km CHECK (preco_km >= 0),
            CONSTRAINT ck_veiculos_status CHECK (
                status IN (
                    'disponivel',
                    'alugado',
                    'manutencao',
                    'desativado'
                )
            ),
            CONSTRAINT ck_veiculos_disponivel
                CHECK (disponivel IN (0, 1)),
            CONSTRAINT ck_veiculos_ativo CHECK (ativo IN (0, 1))
        """,
        "clientes": f"""
            id INTEGER NOT NULL,
            nome VARCHAR(150) NOT NULL,
            usuario VARCHAR(100) COLLATE NOCASE NOT NULL,
            email VARCHAR(255) COLLATE NOCASE NOT NULL,
            senha_hash TEXT NOT NULL,
            ativo BOOLEAN NOT NULL,
            usuario_id INTEGER,
            CONSTRAINT pk_clientes PRIMARY KEY (id),
            CONSTRAINT uq_clientes_usuario UNIQUE (usuario),
            CONSTRAINT uq_clientes_email UNIQUE (email),
            CONSTRAINT uq_clientes_usuario_id UNIQUE (usuario_id),
            CONSTRAINT fk_clientes_usuario_id_usuarios
                FOREIGN KEY (usuario_id)
                REFERENCES {prefixo}usuarios (id)
        """,
        "alugueis": f"""
            id INTEGER NOT NULL,
            cliente_id INTEGER NOT NULL,
            veiculo_id INTEGER NOT NULL,
            cliente_usuario VARCHAR(100) NOT NULL,
            cliente_nome VARCHAR(150) NOT NULL,
            veiculo_tipo VARCHAR(50) NOT NULL,
            veiculo_modelo VARCHAR(150) NOT NULL,
            dias INTEGER NOT NULL,
            status VARCHAR(20) NOT NULL,
            km FLOAT NOT NULL,
            pagamento VARCHAR(100),
            valor FLOAT NOT NULL,
            data_inicio VARCHAR(30) NOT NULL,
            data_prevista VARCHAR(30) NOT NULL,
            data_fim VARCHAR(30),
            dias_atraso INTEGER NOT NULL,
            multa FLOAT NOT NULL,
            CONSTRAINT pk_alugueis PRIMARY KEY (id),
            CONSTRAINT ck_alugueis_dias CHECK (dias > 0),
            CONSTRAINT ck_alugueis_km CHECK (km >= 0),
            CONSTRAINT ck_alugueis_valor CHECK (valor >= 0),
            CONSTRAINT ck_alugueis_dias_atraso
                CHECK (dias_atraso >= 0),
            CONSTRAINT ck_alugueis_multa CHECK (multa >= 0),
            CONSTRAINT ck_alugueis_status
                CHECK (status IN ('ativo', 'finalizado')),
            CONSTRAINT fk_alugueis_cliente_id_clientes
                FOREIGN KEY (cliente_id)
                REFERENCES {prefixo}clientes (id),
            CONSTRAINT fk_alugueis_veiculo_id_veiculos
                FOREIGN KEY (veiculo_id)
                REFERENCES {prefixo}veiculos (id)
        """,
        "manutencoes": f"""
            id INTEGER NOT NULL,
            veiculo_id INTEGER NOT NULL,
            motivo VARCHAR NOT NULL,
            quilometragem FLOAT NOT NULL,
            custo FLOAT NOT NULL,
            data_inicio VARCHAR(30) NOT NULL,
            data_fim VARCHAR(30),
            status VARCHAR(20) NOT NULL,
            CONSTRAINT pk_manutencoes PRIMARY KEY (id),
            CONSTRAINT ck_manutencoes_quilometragem
                CHECK (quilometragem >= 0),
            CONSTRAINT ck_manutencoes_custo CHECK (custo >= 0),
            CONSTRAINT ck_manutencoes_status
                CHECK (status IN ('ativa', 'finalizada')),
            CONSTRAINT fk_manutencoes_veiculo_id_veiculos
                FOREIGN KEY (veiculo_id)
                REFERENCES {prefixo}veiculos (id)
        """,
        "tokens_recuperacao_senha": f"""
            id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            token_hash VARCHAR(64) NOT NULL,
            expira_em VARCHAR(40) NOT NULL,
            usado BOOLEAN NOT NULL,
            criado_em VARCHAR(40) NOT NULL,
            usado_em VARCHAR(40),
            CONSTRAINT pk_tokens_recuperacao_senha PRIMARY KEY (id),
            CONSTRAINT ck_tokens_recuperacao_usado
                CHECK (usado IN (0, 1)),
            CONSTRAINT uq_tokens_recuperacao_senha_token_hash UNIQUE (token_hash),
            CONSTRAINT fk_tokens_recuperacao_senha_usuario_id_usuarios
                FOREIGN KEY (usuario_id)
                REFERENCES {prefixo}usuarios (id)
        """,
    }

    return (
        f"CREATE TABLE {prefixo}{tabela} "
        f"({definicoes[tabela]})"
    )


def _alinhar_schema_sqlite() -> None:
    tabelas = [
        "usuarios",
        "veiculos",
        "clientes",
        "alugueis",
        "manutencoes",
        "tokens_recuperacao_senha",
    ]

    colunas = {
        "usuarios": (
            "id", "usuario", "senha_hash", "role",
            "ativo", "criado_em",
        ),
        "veiculos": (
            "id", "tipo", "modelo", "ano", "diaria",
            "preco_km", "quilometragem", "status",
            "disponivel", "alugado_por", "ativo",
        ),
        "clientes": (
            "id", "nome", "usuario", "email",
            "senha_hash", "ativo", "usuario_id",
        ),
        "alugueis": (
            "id", "cliente_id", "veiculo_id",
            "cliente_usuario", "cliente_nome",
            "veiculo_tipo", "veiculo_modelo", "dias",
            "status", "km", "pagamento", "valor",
            "data_inicio", "data_prevista", "data_fim",
            "dias_atraso", "multa",
        ),
        "manutencoes": (
            "id", "veiculo_id", "motivo", "quilometragem",
            "custo", "data_inicio", "data_fim", "status",
        ),
        "tokens_recuperacao_senha": (
            "id", "usuario_id", "token_hash", "expira_em",
            "usado", "criado_em", "usado_em",
        ),
    }

    for tabela in reversed(tabelas):
        op.execute(
            f"DROP TABLE IF EXISTS alembic_nova_{tabela}"
        )

    for tabela in tabelas:
        op.execute(
            _sql_tabela_temporaria(
                tabela
            )
        )

        nomes_colunas = ", ".join(
            colunas[tabela]
        )

        op.execute(
            f"INSERT INTO alembic_nova_{tabela} "
            f"({nomes_colunas}) "
            f"SELECT {nomes_colunas} FROM {tabela}"
        )

    for tabela in (
        "alugueis",
        "manutencoes",
        "tokens_recuperacao_senha",
        "clientes",
        "veiculos",
        "usuarios",
    ):
        op.drop_table(tabela)

    for tabela in tabelas:
        op.rename_table(
            f"alembic_nova_{tabela}",
            tabela,
        )

    op.create_index(
        "idx_manutencao_ativa_veiculo",
        "manutencoes",
        ["veiculo_id"],
        unique=True,
        sqlite_where=sa.text(
            "status = 'ativa'"
        ),
    )

    op.create_index(
        "idx_tokens_recuperacao_usuario",
        "tokens_recuperacao_senha",
        ["usuario_id"],
        unique=False,
    )


def upgrade() -> None:
    conexao = op.get_bind()
    existentes = set(
        inspect(
            conexao
        ).get_table_names()
    )
    encontradas = (
        existentes
        & TABELAS_APLICACAO
    )

    if not encontradas:
        _criar_schema()
        return

    if encontradas != TABELAS_APLICACAO:
        ausentes = sorted(
            TABELAS_APLICACAO
            - encontradas
        )
        raise RuntimeError(
            "O banco possui um schema parcial. "
            f"Tabelas ausentes: {ausentes}"
        )

    if conexao.dialect.name != "sqlite":
        raise RuntimeError(
            "A adoção automática de banco existente "
            "é suportada somente para SQLite."
        )

    _alinhar_schema_sqlite()


def downgrade() -> None:
    op.drop_index(
        "idx_tokens_recuperacao_usuario",
        table_name="tokens_recuperacao_senha",
    )
    op.drop_table(
        "tokens_recuperacao_senha"
    )

    op.drop_index(
        "idx_manutencao_ativa_veiculo",
        table_name="manutencoes",
    )
    op.drop_table("manutencoes")
    op.drop_table("alugueis")
    op.drop_table("clientes")
    op.drop_table("veiculos")
    op.drop_table("usuarios")
