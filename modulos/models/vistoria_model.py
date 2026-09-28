from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Index,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from modulos.models.base import (
    Base,
)


class InspecaoAluguelModel(Base):
    __tablename__ = "inspecoes"

    __table_args__ = (
        UniqueConstraint(
            "aluguel_id",
            "tipo",
            name="uq_inspecoes_aluguel_tipo",
        ),
        CheckConstraint(
            "tipo IN ('retirada', 'devolucao')",
            name="ck_inspecoes_tipo",
        ),
        CheckConstraint(
            "quilometragem >= 0",
            name="ck_inspecoes_quilometragem",
        ),
        CheckConstraint(
            (
                "combustivel_percentual >= 0 "
                "AND combustivel_percentual <= 100"
            ),
            name="ck_inspecoes_combustivel",
        ),
        Index(
            "idx_inspecoes_aluguel",
            "aluguel_id",
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

    tipo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    quilometragem: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    combustivel_percentual: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    observacoes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    criada_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )


class DanoAluguelModel(Base):
    __tablename__ = "danos"

    __table_args__ = (
        CheckConstraint(
            "valor_estimado >= 0",
            name="ck_danos_valor_estimado",
        ),
        CheckConstraint(
            "status IN ('ativo', 'cancelado')",
            name="ck_danos_status",
        ),
        Index(
            "idx_danos_aluguel_status",
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

    descricao: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    valor_estimado: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ativo",
    )

    criada_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    cancelada_em: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )


class MultaTransitoModel(Base):
    __tablename__ = "multas_transito"

    __table_args__ = (
        CheckConstraint(
            "valor >= 0",
            name="ck_multas_transito_valor",
        ),
        CheckConstraint(
            "status IN ('ativa', 'cancelada')",
            name="ck_multas_transito_status",
        ),
        Index(
            "idx_multas_transito_aluguel_status",
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

    descricao: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    valor: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    data_ocorrencia: Mapped[str] = mapped_column(
        String(30),
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


class CaucaoAluguelModel(Base):
    __tablename__ = "caucoes"

    __table_args__ = (
        UniqueConstraint(
            "aluguel_id",
            name="uq_caucoes_aluguel",
        ),
        CheckConstraint(
            "valor > 0",
            name="ck_caucoes_valor",
        ),
        CheckConstraint(
            "valor_liberado >= 0",
            name="ck_caucoes_valor_liberado",
        ),
        CheckConstraint(
            "valor_liberado <= valor",
            name="ck_caucoes_liberado_limite",
        ),
        CheckConstraint(
            "status IN ('retida', 'parcial', 'liberada')",
            name="ck_caucoes_status",
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

    valor_liberado: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="retida",
    )

    observacoes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    criada_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    atualizada_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
