"""Adiciona notificações persistentes da aplicação.

Revision ID: 20260928_0008
Revises: 20260928_0007
Create Date: 2026-09-28
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa


revision: str = "20260928_0008"
down_revision: str | Sequence[str] | None = "20260928_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    tabelas = set(
        inspect(
            op.get_bind()
        ).get_table_names()
    )

    if "notificacoes" in tabelas:
        return

    op.create_table(
        "notificacoes",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=False,
        ),
        sa.Column(
            "tipo",
            sa.String(40),
            nullable=False,
        ),
        sa.Column(
            "titulo",
            sa.String(160),
            nullable=False,
        ),
        sa.Column(
            "mensagem",
            sa.String(600),
            nullable=False,
        ),
        sa.Column(
            "chave_deduplicacao",
            sa.String(180),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "referencia_tipo",
            sa.String(40),
            nullable=True,
        ),
        sa.Column(
            "referencia_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "lida",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "criada_em",
            sa.String(40),
            nullable=False,
        ),
        sa.Column(
            "lida_em",
            sa.String(40),
            nullable=True,
        ),
        sa.Column(
            "email_destinatario",
            sa.String(255),
            nullable=True,
        ),
        sa.Column(
            "email_status",
            sa.String(20),
            nullable=False,
            server_default="nao_aplicavel",
        ),
        sa.Column(
            "email_enviado_em",
            sa.String(40),
            nullable=True,
        ),
        sa.CheckConstraint(
            (
                "tipo IN ('reserva_proxima', 'aluguel_vencendo', "
                "'aluguel_atrasado', 'manutencao_vencendo', "
                "'manutencao_atrasada', 'financeiro_pendente')"
            ),
            name="ck_notificacoes_tipo",
        ),
        sa.CheckConstraint(
            (
                "email_status IN ('nao_aplicavel', 'nao_configurado', "
                "'pendente', 'enviado', 'falhou')"
            ),
            name="ck_notificacoes_email_status",
        ),
    )

    op.create_index(
        "idx_notificacoes_usuario_lida_criada",
        "notificacoes",
        [
            "usuario_id",
            "lida",
            "criada_em",
        ],
        unique=False,
    )


def downgrade() -> None:
    tabelas = set(
        inspect(
            op.get_bind()
        ).get_table_names()
    )

    if "notificacoes" not in tabelas:
        return

    op.drop_index(
        "idx_notificacoes_usuario_lida_criada",
        table_name="notificacoes",
    )
    op.drop_table("notificacoes")
