"""Adiciona sessões persistentes e refresh tokens.

Revision ID: 20260927_0003
Revises: 20260927_0002
Create Date: 2026-09-27
"""

from collections.abc import (
    Sequence,
)

from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa


revision: str = "20260927_0003"
down_revision: str | Sequence[str] | None = "20260927_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspetor = inspect(
        op.get_bind()
    )

    if "sessoes" in (
        inspetor.get_table_names()
    ):
        return

    op.create_table(
        "sessoes",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "refresh_token_hash",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "expira_em",
            sa.String(40),
            nullable=False,
        ),
        sa.Column(
            "revogada",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.String(40),
            nullable=False,
        ),
        sa.Column(
            "ultimo_uso_em",
            sa.String(40),
            nullable=True,
        ),
        sa.Column(
            "revogada_em",
            sa.String(40),
            nullable=True,
        ),
        sa.CheckConstraint(
            "revogada IN (TRUE, FALSE)",
            name="ck_sessoes_revogada",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f(
                "fk_sessoes_usuario_id_usuarios"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_sessoes"),
        ),
        sa.UniqueConstraint(
            "refresh_token_hash",
            name=op.f(
                "uq_sessoes_refresh_token_hash"
            ),
        ),
    )

    op.create_index(
        "idx_sessoes_usuario",
        "sessoes",
        ["usuario_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_sessoes_usuario",
        table_name="sessoes",
    )
    op.drop_table("sessoes")
