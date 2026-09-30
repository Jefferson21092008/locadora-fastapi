from datetime import datetime, timedelta, timezone

import pytest

from modulos.background_jobs import TarefaBackground
from modulos.database import BancoSQLAlchemy
from modulos.models import Base
from modulos.repositories.background_job_repository import (
    BackgroundJobRepository,
)


@pytest.fixture
def ambiente(tmp_path):
    banco = BancoSQLAlchemy(
        f"sqlite:///{(tmp_path / 'jobs.db').as_posix()}"
    )
    Base.metadata.create_all(banco.engine)
    repository = BackgroundJobRepository(banco)

    try:
        yield banco, repository
    finally:
        banco.fechar()


def criar_tarefa(
    chave="job:1",
    disponivel_em="2026-09-30T00:00:00+00:00",
):
    return TarefaBackground(
        id_tarefa=0,
        tipo="sincronizar_notificacoes_usuario",
        chave_deduplicacao=chave,
        payload={
            "usuario_id": 1,
            "data_referencia": "2026-09-30",
        },
        disponivel_em=disponivel_em,
    )


def test_repository_insere_e_deduplica_tarefa(ambiente):
    _, repository = ambiente

    primeira, criada = repository.inserir_se_ausente(criar_tarefa())
    segunda, criada_novamente = repository.inserir_se_ausente(
        criar_tarefa()
    )

    assert criada is True
    assert criada_novamente is False
    assert primeira.id == segunda.id
    assert len(repository.listar()) == 1


def test_repository_reserva_reagenda_e_conclui(ambiente):
    _, repository = ambiente
    agora = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)

    repository.inserir_se_ausente(criar_tarefa())

    reservada = repository.reservar_proxima(agora=agora)
    assert reservada.status == "processando"
    assert reservada.tentativas == 1

    proxima = agora + timedelta(minutes=1)
    repository.reagendar(
        reservada,
        disponivel_em=proxima,
        erro="falha temporária",
        agora=agora,
    )

    assert repository.reservar_proxima(agora=agora) is None

    reservada = repository.reservar_proxima(agora=proxima)
    assert reservada.tentativas == 2

    concluida = repository.concluir(reservada, agora=proxima)
    assert concluida.status == "concluida"
    assert concluida.concluido_em is not None


def test_repository_recupera_lock_expirado(ambiente):
    _, repository = ambiente
    agora = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)

    repository.inserir_se_ausente(criar_tarefa())
    repository.reservar_proxima(agora=agora - timedelta(minutes=20))

    recuperadas = repository.recuperar_bloqueios_expirados(
        agora=agora,
        timeout_segundos=900,
    )

    assert recuperadas == 1
    reservada = repository.reservar_proxima(agora=agora)
    assert reservada is not None
    assert reservada.tentativas == 2


def test_repository_falha_lock_expirado_apos_limite(ambiente):
    _, repository = ambiente
    inicio = datetime(2026, 9, 30, 11, tzinfo=timezone.utc)
    agora = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)

    tarefa = criar_tarefa(chave="job:limite")
    tarefa.max_tentativas = 1
    repository.inserir_se_ausente(tarefa)
    reservada = repository.reservar_proxima(agora=inicio)

    assert reservada.tentativas == 1

    alteradas = repository.recuperar_bloqueios_expirados(
        agora=agora,
        timeout_segundos=900,
    )

    assert alteradas == 1
    persistida = repository.buscar_por_chave("job:limite")
    assert persistida.status == "falhou"
    assert repository.reservar_proxima(agora=agora) is None
