from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from modulos.models.base import (
    Base,
)


class VeiculoModel(Base):
    """
    Representação ORM da tabela veiculos.

    Esta classe representa persistência.
    Ela não substitui a entidade de domínio
    modulos.veiculos.Veiculo.
    """

    __tablename__ = "veiculos"

    __table_args__ = (
        CheckConstraint(
            "ano >= 1900",
            name="ck_veiculos_ano",
        ),
        CheckConstraint(
            "diaria > 0",
            name="ck_veiculos_diaria",
        ),
        CheckConstraint(
            "preco_km >= 0",
            name="ck_veiculos_preco_km",
        ),
        CheckConstraint(
            "status IN ("
            "'disponivel', "
            "'alugado', "
            "'manutencao', "
            "'desativado'"
            ")",
            name="ck_veiculos_status",
        ),
        CheckConstraint(
            "disponivel IN (TRUE, FALSE)",
            name="ck_veiculos_disponivel",
        ),
        CheckConstraint(
            "ativo IN (TRUE, FALSE)",
            name="ck_veiculos_ativo",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    tipo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    modelo: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    ano: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    diaria: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    preco_km: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    quilometragem: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="disponivel",
    )

    # Colunas legadas mantidas durante a migração.
    # A fonte de verdade do domínio já é ``status``.
    disponivel: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    alugado_por: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
