from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from modulos.models.base import Base


class NotificacaoModel(Base):
    __tablename__ = "notificacoes"

    __table_args__ = (
        CheckConstraint(
            (
                "tipo IN ('reserva_proxima', 'aluguel_vencendo', "
                "'aluguel_atrasado', 'manutencao_vencendo', "
                "'manutencao_atrasada', 'financeiro_pendente')"
            ),
            name="ck_notificacoes_tipo",
        ),
        CheckConstraint(
            (
                "email_status IN ('nao_aplicavel', 'nao_configurado', "
                "'pendente', 'enviado', 'falhou')"
            ),
            name="ck_notificacoes_email_status",
        ),
        Index(
            "idx_notificacoes_usuario_lida_criada",
            "usuario_id",
            "lida",
            "criada_em",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
    )

    tipo: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    titulo: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    mensagem: Mapped[str] = mapped_column(
        String(600),
        nullable=False,
    )

    chave_deduplicacao: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
        unique=True,
    )

    referencia_tipo: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    referencia_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    lida: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    criada_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    lida_em: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    email_destinatario: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    email_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="nao_aplicavel",
    )

    email_enviado_em: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )
