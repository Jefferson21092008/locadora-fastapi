import argparse
import logging
import os
import threading

from modulos.container import Container


logger = logging.getLogger(__name__)


TRUE_VALUES = {
    "1",
    "true",
    "yes",
    "on",
    "sim",
}


def background_jobs_habilitados_por_ambiente():
    return (
        os.getenv(
            "LOCADORA_BACKGROUND_JOBS_ENABLED",
            "false",
        )
        .strip()
        .lower()
        in TRUE_VALUES
    )


class BackgroundWorker:
    def __init__(
        self,
        service,
        intervalo_segundos=60,
        lote=50,
        timeout_bloqueio_segundos=900,
    ):
        self.service = service
        self.intervalo_segundos = max(int(intervalo_segundos), 5)
        self.lote = max(int(lote), 1)
        self.timeout_bloqueio_segundos = max(
            int(timeout_bloqueio_segundos),
            30,
        )
        self._parar = threading.Event()
        self._thread = None

    def executar_uma_vez(self):
        resultado = self.service.executar_ciclo(
            limite=self.lote,
            timeout_bloqueio_segundos=(
                self.timeout_bloqueio_segundos
            ),
        )
        logger.info(
            "Ciclo background concluído: %s",
            resultado,
        )
        return resultado

    def executar_continuamente(self):
        while not self._parar.is_set():
            try:
                self.executar_uma_vez()
            except Exception:
                logger.exception(
                    "Falha no ciclo do worker background."
                )

            self._parar.wait(self.intervalo_segundos)

    def iniciar(self):
        if self._thread is not None and self._thread.is_alive():
            return False

        self._parar.clear()
        self._thread = threading.Thread(
            target=self.executar_continuamente,
            name="locadora-background-worker",
            daemon=True,
        )
        self._thread.start()
        return True

    def parar(self, timeout=5):
        self._parar.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        return True


def criar_worker_do_container(container):
    return BackgroundWorker(
        service=container.background_job_service,
        intervalo_segundos=getattr(
            container.config,
            "background_jobs_intervalo_segundos",
            60,
        ),
        lote=getattr(
            container.config,
            "background_jobs_lote",
            50,
        ),
        timeout_bloqueio_segundos=getattr(
            container.config,
            "background_jobs_timeout_bloqueio_segundos",
            900,
        ),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Worker de tarefas background da Locadora."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Executa apenas um ciclo e encerra.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    container = Container()
    worker = criar_worker_do_container(container)

    if args.once:
        worker.executar_uma_vez()
        return

    try:
        worker.executar_continuamente()
    except KeyboardInterrupt:
        worker.parar()


if __name__ == "__main__":
    main()
