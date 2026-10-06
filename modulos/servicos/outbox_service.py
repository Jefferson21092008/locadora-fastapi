from datetime import datetime, timedelta, timezone


class OutboxService:
    def __init__(
        self,
        outbox_repository,
        barramento,
        retry_base_segundos=5,
        retry_max_segundos=300,
    ):
        self.outbox_repository = outbox_repository
        self.barramento = barramento
        self.retry_base_segundos = max(int(retry_base_segundos), 1)
        self.retry_max_segundos = max(
            int(retry_max_segundos),
            self.retry_base_segundos,
        )

    @staticmethod
    def _agora():
        return datetime.now(timezone.utc)

    def _proxima_tentativa(self, mensagem, agora):
        expoente = max(int(mensagem.tentativas) - 1, 0)
        atraso = min(
            self.retry_base_segundos * (2**expoente),
            self.retry_max_segundos,
        )
        return agora + timedelta(seconds=atraso)

    def _despachar(self, mensagem):
        resultado = self.barramento.publicar(
            mensagem.evento,
            forcar=True,
        )
        if not resultado.sucesso:
            handlers = ", ".join(resultado.falhas)
            raise RuntimeError(
                "Falha ao processar handlers do evento "
                f"{mensagem.evento.nome}: {handlers}"
            )
        return resultado

    def executar_ciclo(
        self,
        limite=100,
        timeout_bloqueio_segundos=60,
        agora=None,
    ):
        agora_base = agora or self._agora()
        recuperadas = (
            self.outbox_repository
            .recuperar_bloqueios_expirados(
                agora=agora_base,
                timeout_segundos=timeout_bloqueio_segundos,
            )
        )

        executadas = 0
        processadas = 0
        reagendadas = 0
        falhas_definitivas = 0

        for _ in range(max(int(limite), 1)):
            mensagem = self.outbox_repository.reservar_proxima(
                agora=agora_base
            )
            if mensagem is None:
                break

            executadas += 1

            try:
                self._despachar(mensagem)
                self.outbox_repository.concluir(
                    mensagem,
                    agora=agora_base,
                )
                processadas += 1
            except Exception as erro:
                if mensagem.tentativas >= mensagem.max_tentativas:
                    self.outbox_repository.falhar_definitivamente(
                        mensagem,
                        erro=erro,
                        agora=agora_base,
                    )
                    falhas_definitivas += 1
                else:
                    self.outbox_repository.reagendar(
                        mensagem,
                        disponivel_em=self._proxima_tentativa(
                            mensagem,
                            agora_base,
                        ),
                        erro=erro,
                        agora=agora_base,
                    )
                    reagendadas += 1

        return {
            "recuperadas": recuperadas,
            "executadas": executadas,
            "processadas": processadas,
            "reagendadas": reagendadas,
            "falhas_definitivas": falhas_definitivas,
        }
