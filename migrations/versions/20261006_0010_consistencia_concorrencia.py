"""Reforça consistência transacional em operações concorrentes.

Revision ID: 20261006_0010
Revises: 20260930_0009
Create Date: 2026-10-06
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect, text


revision: str = "20261006_0010"
down_revision: str | Sequence[str] | None = "20260930_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


INDICE_ALUGUEL_ATIVO = "idx_aluguel_ativo_veiculo"


def _indices_alugueis() -> set[str]:
    inspetor = inspect(op.get_bind())
    tabelas = set(inspetor.get_table_names())

    if "alugueis" not in tabelas:
        return set()

    return {
        indice["name"]
        for indice in inspetor.get_indexes("alugueis")
        if indice.get("name")
    }


def upgrade() -> None:
    if INDICE_ALUGUEL_ATIVO in _indices_alugueis():
        return

    conexao = op.get_bind()
    duplicados = conexao.execute(
        text(
            """
            SELECT veiculo_id
            FROM alugueis
            WHERE status = 'ativo'
            GROUP BY veiculo_id
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    if duplicados:
        ids = ", ".join(
            str(linha[0])
            for linha in duplicados
        )
        raise RuntimeError(
            "Não é possível criar o índice de consistência: "
            "há mais de um aluguel ativo para os veículos "
            f"{ids}. Corrija os dados antes de reaplicar a migration."
        )

    op.create_index(
        INDICE_ALUGUEL_ATIVO,
        "alugueis",
        ["veiculo_id"],
        unique=True,
        sqlite_where=text("status = 'ativo'"),
        postgresql_where=text("status = 'ativo'"),
    )


def downgrade() -> None:
    if INDICE_ALUGUEL_ATIVO not in _indices_alugueis():
        return

    op.drop_index(
        INDICE_ALUGUEL_ATIVO,
        table_name="alugueis",
    )
