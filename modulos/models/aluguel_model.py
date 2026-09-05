from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from modulos.models.base import (
    Base,
)


class AluguelModel(Base):
    """
    Representação ORM da tabela alugueis.

    Esta classe representa persistência.
    Ela não substitui a entidade de domínio
    modulos.alugueis.Aluguel.
    """

    __tablename__ = "alugueis"

    __table_args__ = (
        CheckConstraint(
            "dias > 0",
            name="ck_alugueis_dias",
        ),
        CheckConstraint(
            "km >= 0",
            name="ck_alugueis_km",
        ),
        CheckConstraint(
            "valor >= 0",
            name="ck_alugueis_valor",
        ),
        CheckConstraint(
            "dias_atraso >= 0",
            name="ck_alugueis_dias_atraso",
        ),
        CheckConstraint(
            "multa >= 0",
            name="ck_alugueis_multa",
        ),
        CheckConstraint(
            "status IN ('ativo', 'finalizado')",
            name="ck_alugueis_status",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    cliente_id: Mapped[int] = mapped_column(
        ForeignKey(
            "clientes.id"
        ),
        nullable=False,
    )

    veiculo_id: Mapped[int] = mapped_column(
        ForeignKey(
            "veiculos.id"
        ),
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

    veiculo_tipo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    veiculo_modelo: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    dias: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ativo",
    )

    km: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    pagamento: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    valor: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    # As datas continuam como texto ISO durante a
    # migração para preservar o formato do domínio atual.
    data_inicio: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    data_prevista: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    data_fim: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    dias_atraso: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    multa: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )
