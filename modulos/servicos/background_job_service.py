import logging
from datetime import date, datetime, timedelta, timezone

from modulos.background_jobs import TarefaBackground


logger = logging.getLogger(__name__)


class BackgroundJobService:
    TIPO_NOTIFICACOES = "sincronizar_notificacoes_usuario"

    def __init__(
        self,
        background_job_repository,
        usuario_repository,
        notificacao_service,
        retry_base_segundos=60,
    ):
        self.background_job_repository = background_job_repository
        self.usuario_repository = usuario_repository
        self.notificacao_service = notificacao_service
        self.retry_base_segundos = max(int(retry_base_segundos), 1)

    @staticmethod
    def _agora():
        return datetime.now(timezone.utc)

    def agendar_notificacoes_do_dia(
        self,
        data_referencia=None,
        agora=None,
    ):
        data_referencia = data_referencia or date.today()
        agora = agora or self._agora()
        enfileiradas = 0
        existentes = 0

        for usuario in self.usuario_repository.listar():
            if not usuario.ativo:
                continue

            tarefa = TarefaBackground(
                id_tarefa=0,
                tipo=self.TIPO_NOTIFICACOES,
                chave_deduplicacao=(
                    "notificacoes:"
                    f"{data_referencia.isoformat()}:"
                    f"usuario:{usuario.id}"
                ),
                payload={
                    "usuario_id": usuario.id,
                    "data_referencia": data_referencia.isoformat(),
                },
                max_tentativas=3,
                disponivel_em=agora.isoformat(),
            )

            _, criada = self.background_job_repository.inserir_se_ausente(
                tarefa
            )
            if criada:
                enfileiradas += 1
            else:
                existentes += 1

        return {
            "enfileiradas": enfileiradas,
            "existentes": existentes,
        }

    def _executar_tarefa_notificacoes(self, tarefa):
        usuario_id = int(tarefa.payload["usuario_id"])
        usuario = self.usuario_repository.buscar_por_id(usuario_id)

        if usuario is None or not usuario.ativo:
            return {
                "ignorada": True,
                "motivo": "usuario_inativo_ou_inexistente",
            }

        data_referencia = date.fromisoformat(
            str(tarefa.payload["data_referencia"])
        )

        return self.notificacao_service.processar_usuario(
            usuario,
            data_referencia=data_referencia,
        )

    def _despachar(self, tarefa):
        if tarefa.tipo == self.TIPO_NOTIFICACOES:
            return self._executar_tarefa_notificacoes(tarefa)

        raise ValueError(
            f"Tipo de tarefa não suportado: {tarefa.tipo}"
        )

    def executar_proxima(self, agora=None):
        agora = agora or self._agora()
        tarefa = self.background_job_repository.reservar_proxima(
            agora=agora
        )
        if tarefa is None:
            return None

        try:
            resultado = self._despachar(tarefa)
        except Exception as erro:
            logger.exception(
                "Falha ao executar tarefa background id=%s tipo=%s.",
                tarefa.id,
                tarefa.tipo,
            )

            if tarefa.pode_tentar_novamente:
                atraso = min(
                    self.retry_base_segundos
                    * (2 ** max(tarefa.tentativas - 1, 0)),
                    3600,
                )
                proxima = agora + timedelta(seconds=atraso)
                self.background_job_repository.reagendar(
                    tarefa,
                    disponivel_em=proxima,
                    erro=erro,
                    agora=agora,
                )
                status = "reagendada"
            else:
                self.background_job_repository.falhar_definitivamente(
                    tarefa,
                    erro=erro,
                    agora=agora,
                )
                status = "falhou"

            return {
                "id": tarefa.id,
                "status": status,
                "tentativas": tarefa.tentativas,
            }

        self.background_job_repository.concluir(
            tarefa,
            agora=agora,
        )
        return {
            "id": tarefa.id,
            "status": "concluida",
            "tentativas": tarefa.tentativas,
            "resultado": resultado,
        }

    def executar_lote(self, limite=50, agora=None):
        limite = max(int(limite), 1)
        executadas = 0
        concluidas = 0
        reagendadas = 0
        falhas = 0

        for _ in range(limite):
            resultado = self.executar_proxima(agora=agora)
            if resultado is None:
                break

            executadas += 1
            status = resultado["status"]
            if status == "concluida":
                concluidas += 1
            elif status == "reagendada":
                reagendadas += 1
            elif status == "falhou":
                falhas += 1

        return {
            "executadas": executadas,
            "concluidas": concluidas,
            "reagendadas": reagendadas,
            "falhas": falhas,
        }

    def executar_ciclo(
        self,
        *,
        limite=50,
        timeout_bloqueio_segundos=900,
        data_referencia=None,
        agora=None,
    ):
        agora = agora or self._agora()
        data_referencia = data_referencia or agora.date()

        recuperadas = (
            self.background_job_repository.recuperar_bloqueios_expirados(
                agora=agora,
                timeout_segundos=timeout_bloqueio_segundos,
            )
        )
        agendamento = self.agendar_notificacoes_do_dia(
            data_referencia=data_referencia,
            agora=agora,
        )
        execucao = self.executar_lote(
            limite=limite,
            agora=agora,
        )

        return {
            "recuperadas": recuperadas,
            **agendamento,
            **execucao,
        }
