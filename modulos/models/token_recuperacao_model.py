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


class TokenRecuperacaoModel(Base):
    """
    Representação ORM da tabela
    tokens_recuperacao_senha.
    """

    __tablename__ = (
        "tokens_recuperacao_senha"
    )

    __table_args__ = (
        CheckConstraint(
            "usado IN (TRUE, FALSE)",
            name="ck_tokens_recuperacao_usado",
        ),
        Index(
            "idx_tokens_recuperacao_usuario",
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

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )

    expira_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    usado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    criado_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    usado_em: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    usuario: Mapped["UsuarioModel"] = relationship(
        back_populates="tokens_recuperacao",
    )
