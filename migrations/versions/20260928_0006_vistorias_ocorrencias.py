"""Adiciona vistorias e ocorrências operacionais dos aluguéis.

Revision ID: 20260928_0006
Revises: 20260928_0005
Create Date: 2026-09-28
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa


revision: str = "20260928_0006"
down_revision: str | Sequence[str] | None = "20260928_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    tabelas = set(
        inspect(
            op.get_bind()
        ).get_table_names()
    )

    if "inspecoes" not in tabelas:
        op.create_table(
            "inspecoes",
            sa.Column(
                "id",
                sa.Integer(),
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column(
                "aluguel_id",
                sa.Integer(),
                sa.ForeignKey("alugueis.id"),
                nullable=False,
            ),
            sa.Column(
                "tipo",
                sa.String(20),
                nullable=False,
            ),
            sa.Column(
                "quilometragem",
                sa.Float(),
                nullable=False,
            ),
            sa.Column(
                "combustivel_percentual",
                sa.Integer(),
                nullable=False,
            ),
            sa.Column(
                "observacoes",
                sa.String(500),
                nullable=True,
            ),
            sa.Column(
                "criada_em",
                sa.String(40),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "aluguel_id",
                "tipo",
                name="uq_inspecoes_aluguel_tipo",
            ),
            sa.CheckConstraint(
                "tipo IN ('retirada', 'devolucao')",
                name="ck_inspecoes_tipo",
            ),
            sa.CheckConstraint(
                "quilometragem >= 0",
                name="ck_inspecoes_quilometragem",
            ),
            sa.CheckConstraint(
                (
                    "combustivel_percentual >= 0 "
                    "AND combustivel_percentual <= 100"
                ),
                name="ck_inspecoes_combustivel",
            ),
        )
        op.create_index(
            "idx_inspecoes_aluguel",
            "inspecoes",
            ["aluguel_id"],
            unique=False,
        )

    if "danos" not in tabelas:
        op.create_table(
            "danos",
            sa.Column(
                "id",
                sa.Integer(),
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column(
                "aluguel_id",
                sa.Integer(),
                sa.ForeignKey("alugueis.id"),
                nullable=False,
            ),
            sa.Column(
                "descricao",
                sa.String(500),
                nullable=False,
            ),
            sa.Column(
                "valor_estimado",
                sa.Float(),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "status",
                sa.String(20),
                nullable=False,
                server_default="ativo",
            ),
            sa.Column(
                "criada_em",
                sa.String(40),
                nullable=False,
            ),
            sa.Column(
                "cancelada_em",
                sa.String(40),
                nullable=True,
            ),
            sa.CheckConstraint(
                "valor_estimado >= 0",
                name="ck_danos_valor_estimado",
            ),
            sa.CheckConstraint(
                "status IN ('ativo', 'cancelado')",
                name="ck_danos_status",
            ),
        )
        op.create_index(
            "idx_danos_aluguel_status",
            "danos",
            [
                "aluguel_id",
                "status",
            ],
            unique=False,
        )

    if "multas_transito" not in tabelas:
        op.create_table(
            "multas_transito",
            sa.Column(
                "id",
                sa.Integer(),
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column(
                "aluguel_id",
                sa.Integer(),
                sa.ForeignKey("alugueis.id"),
                nullable=False,
            ),
            sa.Column(
                "descricao",
                sa.String(500),
                nullable=False,
            ),
            sa.Column(
                "valor",
                sa.Float(),
                nullable=False,
            ),
            sa.Column(
                "data_ocorrencia",
                sa.String(30),
                nullable=False,
            ),
            sa.Column(
                "status",
                sa.String(20),
                nullable=False,
                server_default="ativa",
            ),
            sa.Column(
                "criada_em",
                sa.String(40),
                nullable=False,
            ),
            sa.Column(
                "cancelada_em",
                sa.String(40),
                nullable=True,
            ),
            sa.CheckConstraint(
                "valor >= 0",
                name="ck_multas_transito_valor",
            ),
            sa.CheckConstraint(
                "status IN ('ativa', 'cancelada')",
                name="ck_multas_transito_status",
            ),
        )
        op.create_index(
            "idx_multas_transito_aluguel_status",
            "multas_transito",
            [
                "aluguel_id",
                "status",
            ],
            unique=False,
        )

    if "caucoes" not in tabelas:
        op.create_table(
            "caucoes",
            sa.Column(
                "id",
                sa.Integer(),
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column(
                "aluguel_id",
                sa.Integer(),
                sa.ForeignKey("alugueis.id"),
                nullable=False,
            ),
            sa.Column(
                "valor",
                sa.Float(),
                nullable=False,
            ),
            sa.Column(
                "valor_liberado",
                sa.Float(),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "status",
                sa.String(20),
                nullable=False,
                server_default="retida",
            ),
            sa.Column(
                "observacoes",
                sa.String(500),
                nullable=True,
            ),
            sa.Column(
                "criada_em",
                sa.String(40),
                nullable=False,
            ),
            sa.Column(
                "atualizada_em",
                sa.String(40),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "aluguel_id",
                name="uq_caucoes_aluguel",
            ),
            sa.CheckConstraint(
                "valor > 0",
                name="ck_caucoes_valor",
            ),
            sa.CheckConstraint(
                "valor_liberado >= 0",
                name="ck_caucoes_valor_liberado",
            ),
            sa.CheckConstraint(
                "valor_liberado <= valor",
                name="ck_caucoes_liberado_limite",
            ),
            sa.CheckConstraint(
                "status IN ('retida', 'parcial', 'liberada')",
                name="ck_caucoes_status",
            ),
        )


def downgrade() -> None:
    tabelas = set(
        inspect(
            op.get_bind()
        ).get_table_names()
    )

    if "caucoes" in tabelas:
        op.drop_table(
            "caucoes"
        )

    if "multas_transito" in tabelas:
        op.drop_index(
            "idx_multas_transito_aluguel_status",
            table_name="multas_transito",
        )
        op.drop_table(
            "multas_transito"
        )

    if "danos" in tabelas:
        op.drop_index(
            "idx_danos_aluguel_status",
            table_name="danos",
        )
        op.drop_table(
            "danos"
        )

    if "inspecoes" in tabelas:
        op.drop_index(
            "idx_inspecoes_aluguel",
            table_name="inspecoes",
        )
        op.drop_table(
            "inspecoes"
        )
