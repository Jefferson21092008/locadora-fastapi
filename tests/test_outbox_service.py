from datetime import datetime, timezone

import pytest

from modulos.database import BancoSQLAlchemy
from modulos.eventos import BarramentoEventos, EventoAplicacao
from modulos.models import Base
from modulos.outbox import operacao_com_outbox, persistir_eventos_outbox
from modulos.repositories.outbox_repository import OutboxRepository
from modulos.servicos.outbox_service import OutboxService


@pytest.fixture
def ambiente(tmp_path):
    banco = BancoSQLAlchemy(
        f"sqlite:///{(tmp_path / 'service.db').as_posix()}"
    )
    Base.metadata.create_all(banco.engine)
    repository = OutboxRepository(banco)
    barramento = BarramentoEventos(despacho_imediato=False)
    service = OutboxService(
        outbox_repository=repository,
        barramento=barramento,
        retry_base_segundos=5,
        retry_max_segundos=30,
    )

    try:
        yield banco, repository, barramento, service
    finally:
        banco.fechar()


def persistir(banco, evento):
    with operacao_com_outbox(None, evento) as lote:
        with banco.criar_sessao() as sessao:
            persistir_eventos_outbox(sessao)
            sessao.commit()
        lote.materializar()


def test_service_despacha_evento_e_marca_processado(ambiente):
    banco, repository, barramento, service = ambiente
    agora = datetime(2026, 10, 6, 12, tzinfo=timezone.utc)
    evento = EventoAplicacao(
        nome="aluguel.finalizado",
        ocorrido_em=agora,
    )
    recebidos = []
    barramento.assinar(evento.nome, recebidos.append)
    persistir(banco, evento)

    resultado = service.executar_ciclo(
        limite=10,
        timeout_bloqueio_segundos=60,
        agora=agora,
    )

    assert resultado["processadas"] == 1
    assert recebidos[0].id_evento == evento.id_evento
    assert (
        repository.buscar_por_id_evento(evento.id_evento).status
        == "processado"
    )


def test_service_reagenda_quando_handler_falha(ambiente):
    banco, repository, barramento, service = ambiente
    agora = datetime(2026, 10, 6, 12, tzinfo=timezone.utc)
    evento = EventoAplicacao(
        nome="manutencao.atualizada",
        ocorrido_em=agora,
    )

    def falhar(_evento):
        raise RuntimeError("falha controlada")

    barramento.assinar(evento.nome, falhar)
    persistir(banco, evento)

    resultado = service.executar_ciclo(
        limite=1,
        timeout_bloqueio_segundos=60,
        agora=agora,
    )

    assert resultado["reagendadas"] == 1
    persistida = repository.buscar_por_id_evento(evento.id_evento)
    assert persistida.status == "pendente"
    assert persistida.tentativas == 1
    assert "Falha ao processar handlers" in persistida.erro_ultimo
