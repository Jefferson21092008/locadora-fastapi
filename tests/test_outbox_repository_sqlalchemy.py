from datetime import datetime, timedelta, timezone

import pytest

from modulos.database import BancoSQLAlchemy
from modulos.eventos import EventoAplicacao
from modulos.models import Base
from modulos.outbox import (
    operacao_com_outbox,
    persistir_eventos_outbox,
)
from modulos.repositories.outbox_repository import OutboxRepository


@pytest.fixture
def ambiente(tmp_path):
    banco = BancoSQLAlchemy(
        f"sqlite:///{(tmp_path / 'outbox.db').as_posix()}"
    )
    Base.metadata.create_all(banco.engine)
    repository = OutboxRepository(banco)

    try:
        yield banco, repository
    finally:
        banco.fechar()


def persistir_evento(banco, evento):
    with operacao_com_outbox(None, evento) as lote:
        with banco.criar_sessao() as sessao:
            persistir_eventos_outbox(sessao)
            sessao.commit()
        lote.materializar()


def test_repository_reserva_reagenda_e_conclui_evento(ambiente):
    banco, repository = ambiente
    agora = datetime(2026, 10, 6, 12, tzinfo=timezone.utc)
    evento = EventoAplicacao(
        nome="aluguel.finalizado",
        agregado_tipo="aluguel",
        agregado_id=10,
        dados={"veiculo_id": 7},
        ocorrido_em=agora,
    )
    persistir_evento(banco, evento)

    mensagem = repository.reservar_proxima(agora=agora)
    assert mensagem is not None
    assert mensagem.evento.id_evento == evento.id_evento
    assert mensagem.evento.agregado_id == 10
    assert mensagem.status == "processando"
    assert mensagem.tentativas == 1

    proxima = agora + timedelta(seconds=5)
    repository.reagendar(
        mensagem,
        disponivel_em=proxima,
        erro="falha temporária",
        agora=agora,
    )

    assert repository.reservar_proxima(agora=agora) is None

    mensagem = repository.reservar_proxima(agora=proxima)
    assert mensagem.tentativas == 2

    concluida = repository.concluir(mensagem, agora=proxima)
    assert concluida.status == "processado"
    assert concluida.processado_em is not None


def test_repository_recupera_lock_expirado(ambiente):
    banco, repository = ambiente
    inicio = datetime(2026, 10, 6, 10, tzinfo=timezone.utc)
    agora = datetime(2026, 10, 6, 12, tzinfo=timezone.utc)
    persistir_evento(
        banco,
        EventoAplicacao(
            nome="reserva.criada",
            ocorrido_em=inicio,
        ),
    )

    repository.reservar_proxima(agora=inicio)
    recuperadas = repository.recuperar_bloqueios_expirados(
        agora=agora,
        timeout_segundos=60,
    )

    assert recuperadas == 1
    mensagem = repository.reservar_proxima(agora=agora)
    assert mensagem is not None
    assert mensagem.tentativas == 2


def test_id_evento_e_unico(ambiente):
    banco, repository = ambiente
    evento = EventoAplicacao(nome="pagamento.registrado")
    persistir_evento(banco, evento)

    with pytest.raises(Exception):
        persistir_evento(banco, evento)

    assert len(repository.listar()) == 1
