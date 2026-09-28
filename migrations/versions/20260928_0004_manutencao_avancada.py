"""Evolui o cadastro de manutenções.

Revision ID: 20260928_0004
Revises: 20260927_0003
Create Date: 2026-09-28
"""

from collections.abc import (
    Sequence,
)

from alembic import op
import sqlalchemy as sa


revision: str = "20260928_0004"
down_revision: str | Sequence[str] | None = "20260927_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table(
        "manutencoes",
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "tipo",
                sa.String(20),
                nullable=False,
                server_default="corretiva",
            )
        )
        batch_op.add_column(
            sa.Column(
                "prioridade",
                sa.String(20),
                nullable=False,
                server_default="media",
            )
        )
        batch_op.add_column(
            sa.Column(
                "fornecedor",
                sa.String(150),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "custo_estimado",
                sa.Float(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "data_prevista",
                sa.String(30),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "observacoes",
                sa.String(500),
                nullable=True,
            )
        )

        batch_op.create_check_constraint(
            "ck_manutencoes_custo_estimado",
            "custo_estimado >= 0",
        )
        batch_op.create_check_constraint(
            "ck_manutencoes_tipo",
            "tipo IN ('preventiva', 'corretiva')",
        )
        batch_op.create_check_constraint(
            "ck_manutencoes_prioridade",
            "prioridade IN ('baixa', 'media', 'alta')",
        )

    op.create_index(
        "idx_manutencoes_status_previsao",
        "manutencoes",
        [
            "status",
            "data_prevista",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_manutencoes_status_previsao",
        table_name="manutencoes",
    )

    with op.batch_alter_table(
        "manutencoes",
    ) as batch_op:
        batch_op.drop_constraint(
            "ck_manutencoes_prioridade",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_manutencoes_tipo",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_manutencoes_custo_estimado",
            type_="check",
        )
        batch_op.drop_column(
            "observacoes"
        )
        batch_op.drop_column(
            "data_prevista"
        )
        batch_op.drop_column(
            "custo_estimado"
        )
        batch_op.drop_column(
            "fornecedor"
        )
        batch_op.drop_column(
            "prioridade"
        )
        batch_op.drop_column(
            "tipo"
        )
