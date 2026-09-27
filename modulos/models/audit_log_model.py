from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from modulos.models.base import (
    Base,
)


class AuditLogModel(Base):
    """Representação ORM da tabela audit_logs."""

    __tablename__ = "audit_logs"

    __table_args__ = (
        CheckConstraint(
            "role IN ('cliente', 'admin')",
            name="ck_audit_logs_role",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey(
            "usuarios.id",
        ),
        nullable=False,
        index=True,
    )

    usuario: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    acao: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    recurso: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    recurso_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    campos_alterados: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    request_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    criado_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True,
    )
