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


def mensageria_habilitada_por_ambiente():
    return (
        os.getenv(
            "LOCADORA_MENSAGERIA_ENABLED",
            "false",
        )
        .strip()
        .lower()
        in TRUE_VALUES
    )


class OutboxWorker:
    def __init__(
        self,
        service,
        intervalo_segundos=5,
        lote=100,
        timeout_bloqueio_segundos=60,
    ):
        self.service = service
        self.intervalo_segundos = max(int(intervalo_segundos), 1)
        self.lote = max(int(lote), 1)
        self.timeout_bloqueio_segundos = max(
            int(timeout_bloqueio_segundos),
            10,
        )
        self._parar = threading.Event()
        self._thread = None

    def executar_uma_vez(self):
        resultado = self.service.executar_ciclo(
            limite=self.lote,
            timeout_bloqueio_segundos=self.timeout_bloqueio_segundos,
        )
        logger.info("Ciclo outbox concluído: %s", resultado)
        return resultado

    def executar_continuamente(self):
        while not self._parar.is_set():
            try:
                self.executar_uma_vez()
            except Exception:
                logger.exception("Falha no ciclo do worker da outbox.")

            self._parar.wait(self.intervalo_segundos)

    def iniciar(self):
        if self._thread is not None and self._thread.is_alive():
            return False

        self._parar.clear()
        self._thread = threading.Thread(
            target=self.executar_continuamente,
            name="locadora-outbox-worker",
            daemon=True,
        )
        self._thread.start()
        return True

    def parar(self, timeout=5):
        self._parar.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        return True


def criar_worker_outbox_do_container(container):
    return OutboxWorker(
        service=container.outbox_service,
        intervalo_segundos=getattr(
            container.config,
            "mensageria_intervalo_segundos",
            5,
        ),
        lote=getattr(
            container.config,
            "mensageria_lote",
            100,
        ),
        timeout_bloqueio_segundos=getattr(
            container.config,
            "mensageria_timeout_bloqueio_segundos",
            60,
        ),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Worker da transactional outbox da Locadora."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Executa apenas um ciclo e encerra.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    container = Container()
    worker = criar_worker_outbox_do_container(container)

    if args.once:
        worker.executar_uma_vez()
        return

    try:
        worker.executar_continuamente()
    except KeyboardInterrupt:
        worker.parar()


if __name__ == "__main__":
    main()
