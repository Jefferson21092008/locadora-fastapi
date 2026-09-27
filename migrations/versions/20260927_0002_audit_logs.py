"""Adiciona registros persistentes de auditoria.

Revision ID: 20260927_0002
Revises: 20260903_0001
Create Date: 2026-09-27
"""

from collections.abc import (
    Sequence,
)

from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa


revision: str = "20260927_0002"
down_revision: str | Sequence[str] | None = "20260903_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspetor = inspect(
        op.get_bind()
    )

    if "audit_logs" in (
        inspetor.get_table_names()
    ):
        return

    op.create_table(
        "audit_logs",
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
            "usuario",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "acao",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "recurso",
            sa.String(50),
            nullable=False,
        ),
        sa.Column(
            "recurso_id",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "campos_alterados",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "request_id",
            sa.String(64),
            nullable=True,
        ),
        sa.Column(
            "criado_em",
            sa.String(40),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('cliente', 'admin')",
            name="ck_audit_logs_role",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f(
                "fk_audit_logs_usuario_id_usuarios"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_audit_logs"),
        ),
    )

    op.create_index(
        op.f(
            "ix_audit_logs_usuario_id"
        ),
        "audit_logs",
        ["usuario_id"],
        unique=False,
    )
    op.create_index(
        op.f(
            "ix_audit_logs_acao"
        ),
        "audit_logs",
        ["acao"],
        unique=False,
    )
    op.create_index(
        op.f(
            "ix_audit_logs_request_id"
        ),
        "audit_logs",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        op.f(
            "ix_audit_logs_criado_em"
        ),
        "audit_logs",
        ["criado_em"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_audit_logs_criado_em"
        ),
        table_name="audit_logs",
    )
    op.drop_index(
        op.f(
            "ix_audit_logs_request_id"
        ),
        table_name="audit_logs",
    )
    op.drop_index(
        op.f(
            "ix_audit_logs_acao"
        ),
        table_name="audit_logs",
    )
    op.drop_index(
        op.f(
            "ix_audit_logs_usuario_id"
        ),
        table_name="audit_logs",
    )
    op.drop_table(
        "audit_logs"
    )
