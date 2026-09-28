"""Adiciona liquidações financeiras adicionais dos aluguéis.

Revision ID: 20260928_0007
Revises: 20260928_0006
Create Date: 2026-09-28
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa


revision: str = "20260928_0007"
down_revision: str | Sequence[str] | None = "20260928_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    tabelas = set(
        inspect(
            op.get_bind()
        ).get_table_names()
    )

    if "pagamentos_financeiros" in tabelas:
        return

    op.create_table(
        "pagamentos_financeiros",
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
            "forma",
            sa.String(30),
            nullable=False,
        ),
        sa.Column(
            "parcelas",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "observacoes",
            sa.String(500),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="confirmado",
        ),
        sa.Column(
            "criado_em",
            sa.String(40),
            nullable=False,
        ),
        sa.Column(
            "estornado_em",
            sa.String(40),
            nullable=True,
        ),
        sa.CheckConstraint(
            "valor > 0",
            name="ck_pagamentos_financeiros_valor",
        ),
        sa.CheckConstraint(
            (
                "forma IN ('dinheiro', 'pix', 'debito', "
                "'credito', 'boleto', 'transferencia')"
            ),
            name="ck_pagamentos_financeiros_forma",
        ),
        sa.CheckConstraint(
            "parcelas >= 1 AND parcelas <= 12",
            name="ck_pagamentos_financeiros_parcelas",
        ),
        sa.CheckConstraint(
            "forma = 'credito' OR parcelas = 1",
            name="ck_pagamentos_financeiros_parcelamento_forma",
        ),
        sa.CheckConstraint(
            "status IN ('confirmado', 'estornado')",
            name="ck_pagamentos_financeiros_status",
        ),
    )

    op.create_index(
        "idx_pagamentos_financeiros_aluguel_status",
        "pagamentos_financeiros",
        [
            "aluguel_id",
            "status",
        ],
        unique=False,
    )


def downgrade() -> None:
    tabelas = set(
        inspect(
            op.get_bind()
        ).get_table_names()
    )

    if "pagamentos_financeiros" not in tabelas:
        return

    op.drop_index(
        "idx_pagamentos_financeiros_aluguel_status",
        table_name="pagamentos_financeiros",
    )
    op.drop_table(
        "pagamentos_financeiros"
    )
