"""Adiciona fila persistente para tarefas background.

Revision ID: 20260930_0009
Revises: 20260928_0008
Create Date: 2026-09-30
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa


revision: str = "20260930_0009"
down_revision: str | Sequence[str] | None = "20260928_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    tabelas = set(
        inspect(op.get_bind()).get_table_names()
    )

    if "tarefas_background" in tabelas:
        return

    op.create_table(
        "tarefas_background",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "tipo",
            sa.String(60),
            nullable=False,
        ),
        sa.Column(
            "chave_deduplicacao",
            sa.String(180),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "payload_json",
            sa.Text(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pendente",
        ),
        sa.Column(
            "tentativas",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "max_tentativas",
            sa.Integer(),
            nullable=False,
            server_default="3",
        ),
        sa.Column(
            "disponivel_em",
            sa.String(40),
            nullable=False,
        ),
        sa.Column(
            "bloqueado_em",
            sa.String(40),
            nullable=True,
        ),
        sa.Column(
            "concluido_em",
            sa.String(40),
            nullable=True,
        ),
        sa.Column(
            "erro_ultimo",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "criado_em",
            sa.String(40),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.String(40),
            nullable=False,
        ),
        sa.CheckConstraint(
            "tipo IN ('sincronizar_notificacoes_usuario')",
            name="ck_tarefas_background_tipo",
        ),
        sa.CheckConstraint(
            (
                "status IN "
                "('pendente', 'processando', 'concluida', 'falhou')"
            ),
            name="ck_tarefas_background_status",
        ),
        sa.CheckConstraint(
            "tentativas >= 0",
            name="ck_tarefas_background_tentativas",
        ),
        sa.CheckConstraint(
            "max_tentativas >= 1",
            name="ck_tarefas_background_max_tentativas",
        ),
    )

    op.create_index(
        "idx_tarefas_background_status_disponivel",
        "tarefas_background",
        [
            "status",
            "disponivel_em",
            "id",
        ],
        unique=False,
    )


def downgrade() -> None:
    tabelas = set(
        inspect(op.get_bind()).get_table_names()
    )

    if "tarefas_background" not in tabelas:
        return

    op.drop_index(
        "idx_tarefas_background_status_disponivel",
        table_name="tarefas_background",
    )
    op.drop_table("tarefas_background")
