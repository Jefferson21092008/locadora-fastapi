from sqlalchemy import (
    MetaData,
)

from sqlalchemy.orm import (
    DeclarativeBase,
)


CONVENCAO_NOMES = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": (
        "fk_%(table_name)s_%(column_0_name)s_"
        "%(referred_table_name)s"
    ),
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """
    Base declarativa usada pelos Models
    do SQLAlchemy.

    As entidades de domínio continuam
    separadas em modulos/*.py.
    """

    metadata = MetaData(
        naming_convention=CONVENCAO_NOMES
    )
