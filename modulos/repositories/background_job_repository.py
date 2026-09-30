import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from modulos.background_jobs import TarefaBackground
from modulos.models.background_job_model import TarefaBackgroundModel


class BackgroundJobRepository:
    def __init__(self, banco_sqlalchemy):
        self.banco_sqlalchemy = banco_sqlalchemy

    @staticmethod
    def _agora():
        return datetime.now(timezone.utc)

    @staticmethod
    def _iso(valor):
        if isinstance(valor, str):
            return valor
        return valor.isoformat()

    @staticmethod
    def _payload(model):
        try:
            return json.loads(model.payload_json or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}

    @classmethod
    def _para_entidade(cls, model):
        if model is None:
            return None

        return TarefaBackground(
            id_tarefa=model.id,
            tipo=model.tipo,
            chave_deduplicacao=model.chave_deduplicacao,
            payload=cls._payload(model),
            status=model.status,
            tentativas=model.tentativas,
            max_tentativas=model.max_tentativas,
            disponivel_em=model.disponivel_em,
            bloqueado_em=model.bloqueado_em,
            concluido_em=model.concluido_em,
            erro_ultimo=model.erro_ultimo,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
        )

    def inserir_se_ausente(self, tarefa):
        valida, mensagem = tarefa.validar_dados()
        if not valida:
            raise ValueError(mensagem)

        dados = tarefa.to_dict()
        model = TarefaBackgroundModel(
            tipo=dados["tipo"],
            chave_deduplicacao=dados["chave_deduplicacao"],
            payload_json=json.dumps(
                dados["payload"],
                ensure_ascii=False,
                sort_keys=True,
            ),
            status=dados["status"],
            tentativas=dados["tentativas"],
            max_tentativas=dados["max_tentativas"],
            disponivel_em=dados["disponivel_em"],
            bloqueado_em=dados["bloqueado_em"],
            concluido_em=dados["concluido_em"],
            erro_ultimo=dados["erro_ultimo"],
            criado_em=dados["criado_em"],
            atualizado_em=dados["atualizado_em"],
        )

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            try:
                sessao.add(model)
                sessao.commit()
                sessao.refresh(model)
                return self._para_entidade(model), True
            except IntegrityError:
                sessao.rollback()
                existente = sessao.scalar(
                    select(TarefaBackgroundModel).where(
                        TarefaBackgroundModel.chave_deduplicacao
                        == tarefa.chave_deduplicacao
                    )
                )
                return self._para_entidade(existente), False

    def buscar_por_chave(self, chave):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.scalar(
                select(TarefaBackgroundModel).where(
                    TarefaBackgroundModel.chave_deduplicacao
                    == chave
                )
            )
        return self._para_entidade(model)

    def listar(self):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            models = sessao.scalars(
                select(TarefaBackgroundModel).order_by(
                    TarefaBackgroundModel.id
                )
            ).all()

        return [
            self._para_entidade(model)
            for model in models
        ]

    def reservar_proxima(self, agora=None):
        agora_dt = agora or self._agora()
        agora_iso = self._iso(agora_dt)

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            try:
                comando = (
                    select(TarefaBackgroundModel)
                    .where(
                        TarefaBackgroundModel.status
                        == TarefaBackground.STATUS_PENDENTE,
                        TarefaBackgroundModel.tentativas
                        < TarefaBackgroundModel.max_tentativas,
                        TarefaBackgroundModel.disponivel_em
                        <= agora_iso,
                    )
                    .order_by(
                        TarefaBackgroundModel.disponivel_em,
                        TarefaBackgroundModel.id,
                    )
                    .limit(1)
                )

                if self.banco_sqlalchemy.engine.dialect.name == "postgresql":
                    comando = comando.with_for_update(skip_locked=True)

                model = sessao.scalar(comando)
                if model is None:
                    return None

                model.status = TarefaBackground.STATUS_PROCESSANDO
                model.tentativas += 1
                model.bloqueado_em = agora_iso
                model.atualizado_em = agora_iso

                sessao.commit()
                sessao.refresh(model)
                return self._para_entidade(model)
            except Exception:
                sessao.rollback()
                raise

    def concluir(self, tarefa, agora=None):
        agora_iso = self._iso(agora or self._agora())

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.get(TarefaBackgroundModel, tarefa.id)
            if model is None:
                return None

            model.status = TarefaBackground.STATUS_CONCLUIDA
            model.bloqueado_em = None
            model.concluido_em = agora_iso
            model.erro_ultimo = None
            model.atualizado_em = agora_iso
            sessao.commit()
            sessao.refresh(model)
            return self._para_entidade(model)

    def reagendar(self, tarefa, disponivel_em, erro, agora=None):
        agora_iso = self._iso(agora or self._agora())

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.get(TarefaBackgroundModel, tarefa.id)
            if model is None:
                return None

            model.status = TarefaBackground.STATUS_PENDENTE
            model.disponivel_em = self._iso(disponivel_em)
            model.bloqueado_em = None
            model.erro_ultimo = str(erro)[:2000]
            model.atualizado_em = agora_iso
            sessao.commit()
            sessao.refresh(model)
            return self._para_entidade(model)

    def falhar_definitivamente(self, tarefa, erro, agora=None):
        agora_iso = self._iso(agora or self._agora())

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.get(TarefaBackgroundModel, tarefa.id)
            if model is None:
                return None

            model.status = TarefaBackground.STATUS_FALHOU
            model.bloqueado_em = None
            model.erro_ultimo = str(erro)[:2000]
            model.atualizado_em = agora_iso
            sessao.commit()
            sessao.refresh(model)
            return self._para_entidade(model)

    def recuperar_bloqueios_expirados(
        self,
        agora=None,
        timeout_segundos=900,
    ):
        agora_dt = agora or self._agora()
        limite = agora_dt - timedelta(seconds=int(timeout_segundos))
        agora_iso = self._iso(agora_dt)
        limite_iso = self._iso(limite)

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            recuperadas = sessao.execute(
                update(TarefaBackgroundModel)
                .where(
                    TarefaBackgroundModel.status
                    == TarefaBackground.STATUS_PROCESSANDO,
                    TarefaBackgroundModel.bloqueado_em.is_not(None),
                    TarefaBackgroundModel.bloqueado_em <= limite_iso,
                    TarefaBackgroundModel.tentativas
                    < TarefaBackgroundModel.max_tentativas,
                )
                .values(
                    status=TarefaBackground.STATUS_PENDENTE,
                    bloqueado_em=None,
                    disponivel_em=agora_iso,
                    atualizado_em=agora_iso,
                    erro_ultimo="Bloqueio expirado; tarefa devolvida à fila.",
                )
            )

            esgotadas = sessao.execute(
                update(TarefaBackgroundModel)
                .where(
                    TarefaBackgroundModel.status
                    == TarefaBackground.STATUS_PROCESSANDO,
                    TarefaBackgroundModel.bloqueado_em.is_not(None),
                    TarefaBackgroundModel.bloqueado_em <= limite_iso,
                    TarefaBackgroundModel.tentativas
                    >= TarefaBackgroundModel.max_tentativas,
                )
                .values(
                    status=TarefaBackground.STATUS_FALHOU,
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
