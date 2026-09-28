from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from modulos.models.base import Base


class ReservaModel(Base):
    """Representação ORM das reservas futuras."""

    __tablename__ = "reservas"

    __table_args__ = (
        CheckConstraint(
            "status IN ('ativa', 'cancelada', 'convertida')",
            name="ck_reservas_status",
        ),
        CheckConstraint(
            "data_fim > data_inicio",
            name="ck_reservas_periodo",
        ),
        Index(
            "idx_reservas_veiculo_periodo",
            "veiculo_id",
            "status",
            "data_inicio",
            "data_fim",
        ),
        Index(
            "idx_reservas_cliente_status",
            "cliente_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"),
        nullable=False,
    )

    cliente_usuario: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    cliente_nome: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    veiculo_id: Mapped[int] = mapped_column(
        ForeignKey("veiculos.id"),
        nullable=False,
    )

    veiculo_tipo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    veiculo_modelo: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    data_inicio: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    data_fim: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ativa",
    )

    criada_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    cancelada_em: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    convertida_em: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )
