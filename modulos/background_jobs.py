import json
from datetime import datetime, timezone


class TarefaBackground:
    TIPOS_VALIDOS = {
        "sincronizar_notificacoes_usuario",
    }

    STATUS_PENDENTE = "pendente"
    STATUS_PROCESSANDO = "processando"
    STATUS_CONCLUIDA = "concluida"
    STATUS_FALHOU = "falhou"

    STATUS_VALIDOS = {
        STATUS_PENDENTE,
        STATUS_PROCESSANDO,
        STATUS_CONCLUIDA,
        STATUS_FALHOU,
    }

    def __init__(
        self,
        id_tarefa,
        tipo,
        chave_deduplicacao,
        payload=None,
        status=STATUS_PENDENTE,
        tentativas=0,
        max_tentativas=3,
        disponivel_em=None,
        bloqueado_em=None,
        concluido_em=None,
        erro_ultimo=None,
        criado_em=None,
        atualizado_em=None,
    ):
        agora = self._agora()

        self.id = int(id_tarefa)
        self.tipo = str(tipo).strip().lower()
        self.chave_deduplicacao = str(chave_deduplicacao).strip()
        self.payload = dict(payload or {})
        self.status = str(status).strip().lower()
        self.tentativas = int(tentativas)
        self.max_tentativas = int(max_tentativas)
        self.disponivel_em = disponivel_em or agora
        self.bloqueado_em = bloqueado_em
        self.concluido_em = concluido_em
        self.erro_ultimo = self._texto_opcional(erro_ultimo)
        self.criado_em = criado_em or agora
        self.atualizado_em = atualizado_em or agora

    @staticmethod
    def _agora():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _texto_opcional(valor):
        if valor is None:
            return None

        texto = str(valor).strip()
        return texto or None

    def validar_dados(self):
        if self.tipo not in self.TIPOS_VALIDOS:
            return False, "Tipo de tarefa background inválido."

        if not self.chave_deduplicacao:
            return False, "Chave de deduplicação é obrigatória."

        if self.status not in self.STATUS_VALIDOS:
            return False, "Status de tarefa background inválido."

        if self.tentativas < 0:
            return False, "Tentativas não podem ser negativas."

        if self.max_tentativas < 1:
            return False, "Máximo de tentativas deve ser positivo."

        if self.tentativas > self.max_tentativas:
            return False, "Tentativas excederam o limite configurado."

        if not self.disponivel_em:
            return False, "Data de disponibilidade é obrigatória."

        try:
            json.dumps(self.payload)
        except (TypeError, ValueError):
            return False, "Payload da tarefa não é serializável em JSON."

        return True, ""

    @property
    def pode_tentar_novamente(self):
        return self.tentativas < self.max_tentativas

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "chave_deduplicacao": self.chave_deduplicacao,
            "payload": self.payload,
            "status": self.status,
            "tentativas": self.tentativas,
            "max_tentativas": self.max_tentativas,
            "disponivel_em": self.disponivel_em,
            "bloqueado_em": self.bloqueado_em,
            "concluido_em": self.concluido_em,
            "erro_ultimo": self.erro_ultimo,
            "criado_em": self.criado_em,
            "atualizado_em": self.atualizado_em,
        }
