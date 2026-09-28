"""Adiciona reservas futuras de veículos.

Revision ID: 20260928_0005
Revises: 20260928_0004
Create Date: 2026-09-28
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa


revision: str = "20260928_0005"
down_revision: str | Sequence[str] | None = "20260928_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspetor = inspect(
        op.get_bind()
    )

    if "reservas" in (
        inspetor.get_table_names()
    ):
        return

    op.create_table(
        "reservas",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "cliente_id",
            sa.Integer(),
            sa.ForeignKey("clientes.id"),
            nullable=False,
        ),
        sa.Column(
            "cliente_usuario",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "cliente_nome",
            sa.String(150),
            nullable=False,
        ),
        sa.Column(
            "veiculo_id",
            sa.Integer(),
            sa.ForeignKey("veiculos.id"),
            nullable=False,
        ),
        sa.Column(
            "veiculo_tipo",
            sa.String(50),
            nullable=False,
        ),
        sa.Column(
            "veiculo_modelo",
            sa.String(150),
            nullable=False,
        ),
        sa.Column(
            "data_inicio",
            sa.String(10),
            nullable=False,
        ),
        sa.Column(
            "data_fim",
            sa.String(10),
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
        sa.Column(
            "convertida_em",
            sa.String(40),
            nullable=True,
        ),
        sa.CheckConstraint(
            "status IN ('ativa', 'cancelada', 'convertida')",
            name="ck_reservas_status",
        ),
        sa.CheckConstraint(
            "data_fim > data_inicio",
            name="ck_reservas_periodo",
        ),
    )

    op.create_index(
        "idx_reservas_veiculo_periodo",
        "reservas",
        [
            "veiculo_id",
            "status",
            "data_inicio",
            "data_fim",
        ],
        unique=False,
    )

    op.create_index(
        "idx_reservas_cliente_status",
        "reservas",
        [
            "cliente_id",
            "status",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_reservas_cliente_status",
        table_name="reservas",
    )
    op.drop_index(
        "idx_reservas_veiculo_periodo",
        table_name="reservas",
    )
    op.drop_table("reservas")
