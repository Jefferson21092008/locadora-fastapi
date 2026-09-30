from sqlalchemy import (
    CheckConstraint,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from modulos.models.base import Base


class TarefaBackgroundModel(Base):
    __tablename__ = "tarefas_background"

    __table_args__ = (
        CheckConstraint(
            (
                "tipo IN "
                "('sincronizar_notificacoes_usuario')"
            ),
            name="ck_tarefas_background_tipo",
        ),
        CheckConstraint(
            (
                "status IN "
                "('pendente', 'processando', 'concluida', 'falhou')"
            ),
            name="ck_tarefas_background_status",
        ),
        CheckConstraint(
            "tentativas >= 0",
            name="ck_tarefas_background_tentativas",
        ),
        CheckConstraint(
            "max_tentativas >= 1",
            name="ck_tarefas_background_max_tentativas",
        ),
        Index(
            "idx_tarefas_background_status_disponivel",
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

    tipo: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )

    chave_deduplicacao: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
        unique=True,
    )

    payload_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="{}",
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
        default=3,
    )

    disponivel_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    bloqueado_em: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    concluido_em: Mapped[str | None] = mapped_column(
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
