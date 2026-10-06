import json
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone

from modulos.eventos import EventoAplicacao
from modulos.models.outbox_event_model import EventoOutboxModel


_LOTE_ATUAL = ContextVar("locadora_lote_outbox", default=None)


def _agora():
    return datetime.now(timezone.utc)


def _iso(valor):
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.isoformat()


@dataclass
class LoteEventosOutbox:
    fabricas: tuple
    eventos: tuple[EventoAplicacao, ...] = field(default=())
    persistido: bool = False

    def materializar(self, contexto=None):
        if self.eventos:
            return self.eventos

        dados_contexto = dict(contexto or {})
        eventos = []

        for fabrica in self.fabricas:
            evento = (
                fabrica(dados_contexto)
                if callable(fabrica)
                else fabrica
            )
            if not isinstance(evento, EventoAplicacao):
                raise TypeError(
                    "Eventos da outbox precisam ser EventoAplicacao."
                )
            eventos.append(evento)

        self.eventos = tuple(eventos)
        return self.eventos


@contextmanager
def operacao_com_outbox(barramento, *fabricas):
    """
    Agrupa eventos que precisam acompanhar uma mutação transacional.

    O repository persiste o lote antes do mesmo commit da alteração de
    negócio. Só depois de a operação terminar sem erro o evento é entregue
    ao barramento. No Container o barramento adia o despacho para o worker;
    em testes unitários o modo imediato continua disponível.
    """

    lote = LoteEventosOutbox(tuple(fabricas))
    token = _LOTE_ATUAL.set(lote)

    try:
        yield lote
    except Exception:
        raise
    else:
        for evento in lote.eventos:
            if barramento is not None:
                barramento.publicar(evento)
    finally:
        _LOTE_ATUAL.reset(token)


def persistir_eventos_outbox(sessao, contexto=None):
    lote = _LOTE_ATUAL.get()
    if lote is None or lote.persistido:
        return ()

    eventos = lote.materializar(contexto)
    agora_iso = _iso(_agora())

    for evento in eventos:
        payload_json = json.dumps(
            evento.para_dict(),
            ensure_ascii=False,
            sort_keys=True,
        )
        sessao.add(
            EventoOutboxModel(
                id_evento=evento.id_evento,
                nome=evento.nome,
                versao=evento.versao,
                payload_json=payload_json,
                status="pendente",
                tentativas=0,
                max_tentativas=5,
                disponivel_em=_iso(evento.ocorrido_em),
                bloqueado_em=None,
                processado_em=None,
                erro_ultimo=None,
                criado_em=agora_iso,
                atualizado_em=agora_iso,
            )
        )

    lote.persistido = True
    return eventos
