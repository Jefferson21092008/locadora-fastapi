import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from modulos.eventos import EventoAplicacao
from modulos.models.outbox_event_model import EventoOutboxModel


@dataclass
class MensagemOutbox:
    id: int
    evento: EventoAplicacao
    status: str
    tentativas: int
    max_tentativas: int
    disponivel_em: str
    bloqueado_em: str | None = None
    processado_em: str | None = None
    erro_ultimo: str | None = None


class OutboxRepository:
    STATUS_PENDENTE = "pendente"
    STATUS_PROCESSANDO = "processando"
    STATUS_PROCESSADO = "processado"
    STATUS_FALHOU = "falhou"

    def __init__(self, banco_sqlalchemy):
        if banco_sqlalchemy is None:
            raise ValueError("BancoSQLAlchemy é obrigatório.")
        self.banco_sqlalchemy = banco_sqlalchemy

    @staticmethod
    def _agora():
        return datetime.now(timezone.utc)

    @staticmethod
    def _iso(valor):
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.isoformat()

    @staticmethod
    def _evento_do_model(model):
        payload = json.loads(model.payload_json)
        agregado = payload.get("agregado") or {}
        ocorrido_em = datetime.fromisoformat(payload["ocorrido_em"])
        return EventoAplicacao(
            id_evento=payload["id_evento"],
            nome=payload["nome"],
            versao=int(payload.get("versao", 1)),
            ocorrido_em=ocorrido_em,
            agregado_tipo=agregado.get("tipo"),
            agregado_id=agregado.get("id"),
            dados=payload.get("dados") or {},
        )

    @classmethod
    def _para_entidade(cls, model):
        if model is None:
            return None
        return MensagemOutbox(
            id=model.id,
            evento=cls._evento_do_model(model),
            status=model.status,
            tentativas=model.tentativas,
            max_tentativas=model.max_tentativas,
            disponivel_em=model.disponivel_em,
            bloqueado_em=model.bloqueado_em,
            processado_em=model.processado_em,
            erro_ultimo=model.erro_ultimo,
        )

    def buscar_por_id_evento(self, id_evento):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.scalar(
                select(EventoOutboxModel).where(
                    EventoOutboxModel.id_evento == id_evento
                )
            )
        return self._para_entidade(model)

    def listar(self):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            models = sessao.scalars(
                select(EventoOutboxModel).order_by(EventoOutboxModel.id)
            ).all()
        return [self._para_entidade(model) for model in models]

    def reservar_proxima(self, agora=None):
        agora_dt = agora or self._agora()
        agora_iso = self._iso(agora_dt)

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            try:
                comando = (
                    select(EventoOutboxModel)
                    .where(
                        EventoOutboxModel.status == self.STATUS_PENDENTE,
                        EventoOutboxModel.tentativas
                        < EventoOutboxModel.max_tentativas,
                        EventoOutboxModel.disponivel_em <= agora_iso,
                    )
                    .order_by(
                        EventoOutboxModel.disponivel_em,
                        EventoOutboxModel.id,
                    )
                    .limit(1)
                )

                if self.banco_sqlalchemy.engine.dialect.name == "postgresql":
                    comando = comando.with_for_update(skip_locked=True)

                model = sessao.scalar(comando)
                if model is None:
                    return None

                model.status = self.STATUS_PROCESSANDO
                model.tentativas += 1
                model.bloqueado_em = agora_iso
                model.atualizado_em = agora_iso
                sessao.commit()
                sessao.refresh(model)
                return self._para_entidade(model)
            except Exception:
                sessao.rollback()
                raise

    def concluir(self, mensagem, agora=None):
        agora_iso = self._iso(agora or self._agora())
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.get(EventoOutboxModel, mensagem.id)
            if model is None:
                return None
            model.status = self.STATUS_PROCESSADO
            model.bloqueado_em = None
            model.processado_em = agora_iso
            model.erro_ultimo = None
            model.atualizado_em = agora_iso
            sessao.commit()
            sessao.refresh(model)
            return self._para_entidade(model)

    def reagendar(self, mensagem, disponivel_em, erro, agora=None):
        agora_iso = self._iso(agora or self._agora())
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.get(EventoOutboxModel, mensagem.id)
            if model is None:
                return None
            model.status = self.STATUS_PENDENTE
            model.disponivel_em = self._iso(disponivel_em)
            model.bloqueado_em = None
            model.erro_ultimo = str(erro)[:2000]
            model.atualizado_em = agora_iso
            sessao.commit()
            sessao.refresh(model)
            return self._para_entidade(model)

    def falhar_definitivamente(self, mensagem, erro, agora=None):
        agora_iso = self._iso(agora or self._agora())
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.get(EventoOutboxModel, mensagem.id)
            if model is None:
                return None
            model.status = self.STATUS_FALHOU
            model.bloqueado_em = None
            model.erro_ultimo = str(erro)[:2000]
            model.atualizado_em = agora_iso
            sessao.commit()
            sessao.refresh(model)
            return self._para_entidade(model)

    def recuperar_bloqueios_expirados(
        self,
        agora=None,
        timeout_segundos=60,
    ):
        agora_dt = agora or self._agora()
        limite = agora_dt - timedelta(seconds=int(timeout_segundos))
        agora_iso = self._iso(agora_dt)
        limite_iso = self._iso(limite)

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            recuperadas = sessao.execute(
                update(EventoOutboxModel)
                .where(
                    EventoOutboxModel.status == self.STATUS_PROCESSANDO,
                    EventoOutboxModel.bloqueado_em.is_not(None),
                    EventoOutboxModel.bloqueado_em <= limite_iso,
                    EventoOutboxModel.tentativas
                    < EventoOutboxModel.max_tentativas,
                )
                .values(
                    status=self.STATUS_PENDENTE,
                    bloqueado_em=None,
                    disponivel_em=agora_iso,
                    atualizado_em=agora_iso,
                    erro_ultimo=(
                        "Bloqueio expirado; evento devolvido à outbox."
                    ),
                )
            )

            esgotadas = sessao.execute(
                update(EventoOutboxModel)
                .where(
                    EventoOutboxModel.status == self.STATUS_PROCESSANDO,
                    EventoOutboxModel.bloqueado_em.is_not(None),
                    EventoOutboxModel.bloqueado_em <= limite_iso,
                    EventoOutboxModel.tentativas
                    >= EventoOutboxModel.max_tentativas,
                )
                .values(
                    status=self.STATUS_FALHOU,
                    bloqueado_em=None,
                    atualizado_em=agora_iso,
                    erro_ultimo=(
                        "Bloqueio expirado após atingir o limite de tentativas."
                    ),
                )
            )
            sessao.commit()
            return int(
                (recuperadas.rowcount or 0)
                + (esgotadas.rowcount or 0)
            )
