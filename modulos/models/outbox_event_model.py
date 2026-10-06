from sqlalchemy import (
    CheckConstraint,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from modulos.models.base import Base


class EventoOutboxModel(Base):
    __tablename__ = "eventos_outbox"

    __table_args__ = (
        CheckConstraint(
            (
                "status IN "
                "('pendente', 'processando', 'processado', 'falhou')"
            ),
            name="ck_eventos_outbox_status",
        ),
        CheckConstraint(
            "tentativas >= 0",
            name="ck_eventos_outbox_tentativas",
        ),
        CheckConstraint(
            "max_tentativas >= 1",
            name="ck_eventos_outbox_max_tentativas",
        ),
        Index(
            "idx_eventos_outbox_status_disponivel",
            "status",
            "disponivel_em",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    id_evento: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
    )

    nome: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    versao: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    payload_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pendente",
    )

    tentativas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    max_tentativas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )

    disponivel_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    bloqueado_em: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    processado_em: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    erro_ultimo: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    criado_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    atualizado_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
