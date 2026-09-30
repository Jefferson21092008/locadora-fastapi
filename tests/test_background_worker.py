from types import SimpleNamespace

from modulos.background_worker import (
    BackgroundWorker,
    background_jobs_habilitados_por_ambiente,
    criar_worker_do_container,
)


class BackgroundJobServiceFake:
    def __init__(self):
        self.chamadas = []

    def executar_ciclo(self, **kwargs):
        self.chamadas.append(kwargs)
        return {
            "executadas": 0,
            "concluidas": 0,
        }


def test_worker_executa_um_ciclo_com_configuracao():
    service = BackgroundJobServiceFake()
    worker = BackgroundWorker(
        service=service,
        intervalo_segundos=30,
        lote=7,
        timeout_bloqueio_segundos=120,
    )

    resultado = worker.executar_uma_vez()

    assert resultado["executadas"] == 0
    assert service.chamadas == [
        {
            "limite": 7,
            "timeout_bloqueio_segundos": 120,
        }
    ]


def test_worker_pode_ser_criado_a_partir_do_container():
    service = BackgroundJobServiceFake()
    container = SimpleNamespace(
        background_job_service=service,
        config=SimpleNamespace(
            background_jobs_intervalo_segundos=45,
            background_jobs_lote=9,
            background_jobs_timeout_bloqueio_segundos=300,
        ),
    )

    worker = criar_worker_do_container(container)

    assert worker.service is service
    assert worker.intervalo_segundos == 45
    assert worker.lote == 9
    assert worker.timeout_bloqueio_segundos == 300


def test_background_jobs_habilitados_por_variavel(monkeypatch):
    monkeypatch.setenv(
        "LOCADORA_BACKGROUND_JOBS_ENABLED",
        "true",
    )
    assert background_jobs_habilitados_por_ambiente() is True

    monkeypatch.setenv(
        "LOCADORA_BACKGROUND_JOBS_ENABLED",
        "false",
    )
    assert background_jobs_habilitados_por_ambiente() is False
