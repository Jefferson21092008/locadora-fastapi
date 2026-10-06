"""Adiciona transactional outbox para eventos da aplicação.

Revision ID: 20261006_0011
Revises: 20261006_0010
Create Date: 2026-10-06
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa


revision: str = "20261006_0011"
down_revision: str | Sequence[str] | None = "20261006_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    tabelas = set(inspect(op.get_bind()).get_table_names())

    if "eventos_outbox" in tabelas:
        return

    op.create_table(
        "eventos_outbox",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "id_evento",
            sa.String(36),
            nullable=False,
            unique=True,
        ),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column(
            "versao",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        sa.Column("payload_json", sa.Text(), nullable=False),
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
            server_default="5",
        ),
        sa.Column("disponivel_em", sa.String(40), nullable=False),
        sa.Column("bloqueado_em", sa.String(40), nullable=True),
        sa.Column("processado_em", sa.String(40), nullable=True),
        sa.Column("erro_ultimo", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.String(40), nullable=False),
        sa.Column("atualizado_em", sa.String(40), nullable=False),
        sa.CheckConstraint(
            (
                "status IN "
                "('pendente', 'processando', 'processado', 'falhou')"
            ),
            name="ck_eventos_outbox_status",
        ),
        sa.CheckConstraint(
            "tentativas >= 0",
            name="ck_eventos_outbox_tentativas",
        ),
        sa.CheckConstraint(
            "max_tentativas >= 1",
            name="ck_eventos_outbox_max_tentativas",
        ),
    )

    op.create_index(
        "idx_eventos_outbox_status_disponivel",
        "eventos_outbox",
        ["status", "disponivel_em", "id"],
        unique=False,
    )


def downgrade() -> None:
    tabelas = set(inspect(op.get_bind()).get_table_names())
    if "eventos_outbox" not in tabelas:
        return

    op.drop_index(
        "idx_eventos_outbox_status_disponivel",
        table_name="eventos_outbox",
    )
    op.drop_table("eventos_outbox")
