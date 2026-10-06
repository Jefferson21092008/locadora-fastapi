from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from modulos.database import BancoSQLAlchemy
from modulos.eventos import EventoAplicacao
from modulos.models import Base
from modulos.models.background_job_model import TarefaBackgroundModel
from modulos.models.outbox_event_model import EventoOutboxModel
from modulos.outbox import (
    operacao_com_outbox,
    persistir_eventos_outbox,
)


def criar_tarefa(chave):
    agora = "2026-10-06T12:00:00+00:00"
    return TarefaBackgroundModel(
        tipo="sincronizar_notificacoes_usuario",
        chave_deduplicacao=chave,
        payload_json="{}",
        status="pendente",
        tentativas=0,
        max_tentativas=3,
        disponivel_em=agora,
        criado_em=agora,
        atualizado_em=agora,
    )


def test_evento_e_mutacao_sao_confirmados_na_mesma_transacao(tmp_path):
    banco = BancoSQLAlchemy(
        f"sqlite:///{(tmp_path / 'atomic.db').as_posix()}"
    )
    Base.metadata.create_all(banco.engine)
    evento = EventoAplicacao(
        nome="reserva.criada",
        agregado_tipo="reserva",
        agregado_id=8,
        ocorrido_em=datetime(2026, 10, 6, 12, tzinfo=timezone.utc),
    )

    try:
        with operacao_com_outbox(None, evento) as lote:
            with banco.criar_sessao() as sessao:
                sessao.add(criar_tarefa("atomic:ok"))
                persistir_eventos_outbox(sessao)
                sessao.commit()
            lote.materializar()

        with banco.criar_sessao() as sessao:
            assert sessao.scalar(
                select(TarefaBackgroundModel.id).where(
                    TarefaBackgroundModel.chave_deduplicacao
                    == "atomic:ok"
                )
            ) is not None
            assert sessao.scalar(
                select(EventoOutboxModel.id).where(
                    EventoOutboxModel.id_evento == evento.id_evento
                )
            ) is not None
    finally:
        banco.fechar()


def test_falha_ao_persistir_evento_faz_rollback_da_mutacao(tmp_path):
    banco = BancoSQLAlchemy(
        f"sqlite:///{(tmp_path / 'rollback.db').as_posix()}"
    )
    Base.metadata.create_all(banco.engine)
    evento = EventoAplicacao(
        nome="reserva.criada",
        dados={"nao_serializavel": object()},
    )

    try:
        with pytest.raises(TypeError):
            with operacao_com_outbox(None, evento):
                with banco.criar_sessao() as sessao:
                    try:
                        sessao.add(criar_tarefa("atomic:rollback"))
                        sessao.flush()
                        persistir_eventos_outbox(sessao)
                        sessao.commit()
                    except Exception:
                        sessao.rollback()
                        raise

        with banco.criar_sessao() as sessao:
            assert sessao.scalar(
                select(TarefaBackgroundModel.id).where(
                    TarefaBackgroundModel.chave_deduplicacao
                    == "atomic:rollback"
                )
            ) is None
            assert sessao.scalar(select(EventoOutboxModel.id)) is None
    finally:
        banco.fechar()
