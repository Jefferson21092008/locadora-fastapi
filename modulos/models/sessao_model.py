from typing import (
    TYPE_CHECKING,
)

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from modulos.models.base import (
    Base,
)


if TYPE_CHECKING:
    from modulos.models.usuario_model import (
        UsuarioModel,
    )


class SessaoModel(Base):
    """
    Sessão persistente usada para refresh tokens.

    O refresh token puro nunca é salvo no banco. A tabela guarda
    apenas seu hash SHA-256 e os metadados necessários para rotação,
    expiração e revogação da sessão.
    """

    __tablename__ = "sessoes"

    __table_args__ = (
        CheckConstraint(
            "revogada IN (TRUE, FALSE)",
            name="ck_sessoes_revogada",
        ),
        Index(
            "idx_sessoes_usuario",
            "usuario_id",
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

    refresh_token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )

    expira_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    revogada: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    criado_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    ultimo_uso_em: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    revogada_em: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    usuario: Mapped["UsuarioModel"] = relationship(
        back_populates="sessoes",
    )
