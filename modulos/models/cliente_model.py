from sqlalchemy import (
    Boolean,
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


class ClienteModel(Base):
    """
    Representação ORM da tabela clientes.

    Esta classe representa persistência.
    Ela não substitui a entidade de domínio
    modulos.clientes.Cliente.
    """

    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    nome: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    usuario: Mapped[str] = mapped_column(
        String(100).with_variant(
            String(
                100,
                collation="NOCASE",
            ),
            "sqlite",
        ),
        nullable=False,
        unique=True,
    )

    email: Mapped[str] = mapped_column(
        String(255).with_variant(
            String(
                255,
                collation="NOCASE",
            ),
            "sqlite",
        ),
        nullable=False,
        unique=True,
    )

    # Coluna mantida somente por compatibilidade
    # com a estrutura SQLite legada. A senha real
    # pertence à tabela usuarios.
    senha_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "usuarios.id"
        ),
        nullable=True,
        unique=True,
    )
