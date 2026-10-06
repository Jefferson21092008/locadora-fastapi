import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EventoAplicacao:
    """Envelope estável para eventos internos da aplicação."""

    nome: str
    dados: dict = field(default_factory=dict)
    agregado_tipo: str | None = None
    agregado_id: int | str | None = None
    versao: int = 1
    id_evento: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )
    ocorrido_em: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self):
        nome = str(self.nome or "").strip()
        if not nome:
            raise ValueError("O nome do evento é obrigatório.")
        if int(self.versao) < 1:
            raise ValueError("A versão do evento deve ser maior que zero.")

        object.__setattr__(self, "nome", nome)
        object.__setattr__(self, "dados", dict(self.dados or {}))
        object.__setattr__(self, "versao", int(self.versao))

        ocorrido_em = self.ocorrido_em
        if ocorrido_em.tzinfo is None:
            ocorrido_em = ocorrido_em.replace(tzinfo=timezone.utc)
        object.__setattr__(self, "ocorrido_em", ocorrido_em)

    def para_dict(self):
        return {
            "id_evento": self.id_evento,
            "nome": self.nome,
            "versao": self.versao,
            "ocorrido_em": self.ocorrido_em.isoformat(),
            "agregado": {
                "tipo": self.agregado_tipo,
                "id": self.agregado_id,
            },
            "dados": dict(self.dados),
        }


@dataclass(frozen=True)
class ResultadoPublicacao:
    handlers_encontrados: int
    handlers_executados: int
    falhas: tuple[str, ...] = ()

    @property
    def sucesso(self):
        return not self.falhas


class BarramentoEventos:
    """
    Barramento síncrono e em memória para eventos de aplicação.

    Os repositories já concluíram a transação quando um service publica um
    evento. Por isso falhas de handlers são isoladas e registradas, evitando
    responder erro ao cliente depois de a mutação principal ter sido commitada.
    """

    CORINGA = "*"

    def __init__(self):
        self._handlers = {}
        self._lock = threading.RLock()

    def assinar(self, nome_evento, handler):
        nome_evento = str(nome_evento or "").strip()
        if not nome_evento:
            raise ValueError("O nome do evento é obrigatório.")
        if not callable(handler):
            raise TypeError("O handler do evento precisa ser chamável.")

        with self._lock:
            handlers = self._handlers.setdefault(nome_evento, [])
            if handler not in handlers:
                handlers.append(handler)

        return handler

    def desassinar(self, nome_evento, handler):
        with self._lock:
            handlers = self._handlers.get(nome_evento, [])
            if handler not in handlers:
                return False
            handlers.remove(handler)
            if not handlers:
                self._handlers.pop(nome_evento, None)
        return True

    def _handlers_para(self, nome_evento):
        with self._lock:
            exatos = list(self._handlers.get(nome_evento, ()))
            coringa = list(self._handlers.get(self.CORINGA, ()))
        return exatos + coringa

    def publicar(self, evento):
        if not isinstance(evento, EventoAplicacao):
            raise TypeError("O barramento aceita apenas EventoAplicacao.")

        handlers = self._handlers_para(evento.nome)
        executados = 0
        falhas = []

        for handler in handlers:
            try:
                handler(evento)
                executados += 1
            except Exception:
                nome_handler = getattr(
                    handler,
                    "__qualname__",
                    getattr(handler, "__name__", repr(handler)),
                )
                falhas.append(nome_handler)
                logger.exception(
                    "Falha em handler do evento %s id=%s handler=%s.",
                    evento.nome,
                    evento.id_evento,
                    nome_handler,
                )

        return ResultadoPublicacao(
            handlers_encontrados=len(handlers),
            handlers_executados=executados,
            falhas=tuple(falhas),
        )


def publicar_evento(
    barramento,
    nome,
    *,
    agregado_tipo=None,
    agregado_id=None,
    dados=None,
):
    """Publica somente quando um barramento foi injetado no service."""
    if barramento is None:
        return None

    evento = EventoAplicacao(
        nome=nome,
        agregado_tipo=agregado_tipo,
        agregado_id=agregado_id,
        dados=dados or {},
    )
    return barramento.publicar(evento)
