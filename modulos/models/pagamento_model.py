from sqlalchemy import (
    CheckConstraint,
    Float,
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


class PagamentoFinanceiroModel(Base):
    __tablename__ = "pagamentos_financeiros"

    __table_args__ = (
        CheckConstraint(
            "valor > 0",
            name="ck_pagamentos_financeiros_valor",
        ),
        CheckConstraint(
            (
                "forma IN ('dinheiro', 'pix', 'debito', "
                "'credito', 'boleto', 'transferencia')"
            ),
            name="ck_pagamentos_financeiros_forma",
        ),
        CheckConstraint(
            "parcelas >= 1 AND parcelas <= 12",
            name="ck_pagamentos_financeiros_parcelas",
        ),
        CheckConstraint(
            "forma = 'credito' OR parcelas = 1",
            name="ck_pagamentos_financeiros_parcelamento_forma",
        ),
        CheckConstraint(
            "status IN ('confirmado', 'estornado')",
            name="ck_pagamentos_financeiros_status",
        ),
        Index(
            "idx_pagamentos_financeiros_aluguel_status",
            "aluguel_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    aluguel_id: Mapped[int] = mapped_column(
        ForeignKey("alugueis.id"),
        nullable=False,
    )

    valor: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    forma: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    parcelas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    observacoes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="confirmado",
    )

    criado_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    estornado_em: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )
