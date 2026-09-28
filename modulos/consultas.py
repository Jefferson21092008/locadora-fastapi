from dataclasses import dataclass
from typing import Any, Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ResultadoPaginado(Generic[T]):
    """Resultado de uma consulta paginada executada no repositório."""

    items: list[T]
    total: int
    resumo: dict[str, Any]
