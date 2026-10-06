from types import SimpleNamespace

from modulos.outbox_worker import (
    OutboxWorker,
    criar_worker_outbox_do_container,
    mensageria_habilitada_por_ambiente,
)


class OutboxServiceFake:
    def __init__(self):
        self.chamadas = []

    def executar_ciclo(self, **kwargs):
        self.chamadas.append(kwargs)
        return {
            "executadas": 0,
            "processadas": 0,
        }


def test_worker_executa_ciclo_com_configuracao():
    service = OutboxServiceFake()
    worker = OutboxWorker(
        service=service,
        intervalo_segundos=2,
        lote=17,
        timeout_bloqueio_segundos=45,
    )

    resultado = worker.executar_uma_vez()

    assert resultado["executadas"] == 0
    assert service.chamadas == [
        {
            "limite": 17,
            "timeout_bloqueio_segundos": 45,
        }
    ]


def test_worker_pode_ser_criado_do_container():
    service = OutboxServiceFake()
    container = SimpleNamespace(
        outbox_service=service,
        config=SimpleNamespace(
            mensageria_intervalo_segundos=3,
            mensageria_lote=25,
            mensageria_timeout_bloqueio_segundos=70,
        ),
    )

    worker = criar_worker_outbox_do_container(container)

    assert worker.service is service
    assert worker.intervalo_segundos == 3
    assert worker.lote == 25
    assert worker.timeout_bloqueio_segundos == 70


def test_mensageria_habilitada_por_variavel(monkeypatch):
    monkeypatch.setenv("LOCADORA_MENSAGERIA_ENABLED", "true")
    assert mensageria_habilitada_por_ambiente() is True

    monkeypatch.setenv("LOCADORA_MENSAGERIA_ENABLED", "false")
    assert mensageria_habilitada_por_ambiente() is False
