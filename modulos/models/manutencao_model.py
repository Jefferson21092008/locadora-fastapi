from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from modulos.models.base import (
    Base,
)


class ManutencaoModel(Base):
    """
    Representação ORM da tabela manutencoes.

    Esta classe representa persistência.
    Ela não substitui a entidade de domínio
    modulos.manutencoes.Manutencao.
    """

    __tablename__ = "manutencoes"

    __table_args__ = (
        CheckConstraint(
            "quilometragem >= 0",
            name="ck_manutencoes_quilometragem",
        ),
        CheckConstraint(
            "custo >= 0",
            name="ck_manutencoes_custo",
        ),
        CheckConstraint(
            "status IN ('ativa', 'finalizada')",
            name="ck_manutencoes_status",
        ),
        Index(
            "idx_manutencao_ativa_veiculo",
            "veiculo_id",
            unique=True,
            sqlite_where=text(
                "status = 'ativa'"
            ),
            postgresql_where=text(
                "status = 'ativa'"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    veiculo_id: Mapped[int] = mapped_column(
        ForeignKey(
            "veiculos.id"
        ),
        nullable=False,
    )

    motivo: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    quilometragem: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    custo: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    # As datas continuam em texto ISO durante a
    # migração para preservar o domínio atual.
    data_inicio: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    data_fim: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ativa",
    )
