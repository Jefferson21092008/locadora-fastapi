from typing import (
    TYPE_CHECKING,
)

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Integer,
    String,
    Text,
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
    from modulos.models.token_recuperacao_model import (
        TokenRecuperacaoModel,
    )


class UsuarioModel(Base):
    """
    Representação ORM da tabela usuarios.

    Esta classe representa persistência.
    Ela não substitui a entidade de domínio
    modulos.usuarios.Usuario.
    """

    __tablename__ = "usuarios"

    __table_args__ = (
        CheckConstraint(
            "role IN ('cliente', 'admin')",
            name="ck_usuarios_role",
        ),
        CheckConstraint(
            "ativo IN (0, 1)",
            name="ck_usuarios_ativo",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    usuario: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    senha_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    criado_em: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    tokens_recuperacao: Mapped[
        list["TokenRecuperacaoModel"]
    ] = relationship(
        back_populates="usuario",
    )
