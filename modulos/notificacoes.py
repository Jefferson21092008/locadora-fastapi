from datetime import datetime, timezone


class Notificacao:
    TIPOS_VALIDOS = {
        "reserva_proxima",
        "aluguel_vencendo",
        "aluguel_atrasado",
        "manutencao_vencendo",
        "manutencao_atrasada",
        "financeiro_pendente",
    }

    STATUS_EMAIL_VALIDOS = {
        "nao_aplicavel",
        "nao_configurado",
        "pendente",
        "enviado",
        "falhou",
    }

    def __init__(
        self,
        id_notificacao,
        usuario_id,
        tipo,
        titulo,
        mensagem,
        chave_deduplicacao,
        referencia_tipo=None,
        referencia_id=None,
        lida=False,
        criada_em=None,
        lida_em=None,
        email_destinatario=None,
        email_status="nao_aplicavel",
        email_enviado_em=None,
    ):
        self.id = int(id_notificacao)
        self.usuario_id = int(usuario_id)
        self.tipo = str(tipo).strip().lower()
        self.titulo = str(titulo).strip()
        self.mensagem = str(mensagem).strip()
        self.chave_deduplicacao = str(chave_deduplicacao).strip()
        self.referencia_tipo = self._normalizar_texto_opcional(
            referencia_tipo
        )
        self.referencia_id = (
            int(referencia_id)
            if referencia_id is not None
            else None
        )
        self.lida = bool(lida)
        self.criada_em = criada_em or self._agora()
        self.lida_em = lida_em
        self.email_destinatario = self._normalizar_texto_opcional(
            email_destinatario
        )
        self.email_status = str(email_status).strip().lower()
        self.email_enviado_em = email_enviado_em

    @staticmethod
    def _agora():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalizar_texto_opcional(valor):
        if valor is None:
            return None

        texto = str(valor).strip()
        return texto or None

    @property
    def nao_lida(self):
        return not self.lida

    def validar_dados(self):
        if self.usuario_id <= 0:
            return False, "Usuário da notificação inválido."

        if self.tipo not in self.TIPOS_VALIDOS:
            return False, "Tipo de notificação inválido."

        if not self.titulo:
            return False, "Título da notificação é obrigatório."

        if not self.mensagem:
            return False, "Mensagem da notificação é obrigatória."

        if not self.chave_deduplicacao:
            return False, "Chave de deduplicação é obrigatória."

        if self.email_status not in self.STATUS_EMAIL_VALIDOS:
            return False, "Status de e-mail inválido."

        return True, ""

    def marcar_como_lida(self):
        if self.lida:
            return False

        self.lida = True
        self.lida_em = self._agora()
        return True

    def atualizar_status_email(self, status):
        status = str(status).strip().lower()

        if status not in self.STATUS_EMAIL_VALIDOS:
            raise ValueError("Status de e-mail inválido.")

        self.email_status = status
        self.email_enviado_em = (
            self._agora()
            if status == "enviado"
            else None
        )

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "mensagem": self.mensagem,
            "chave_deduplicacao": self.chave_deduplicacao,
            "referencia_tipo": self.referencia_tipo,
            "referencia_id": self.referencia_id,
            "lida": self.lida,
            "criada_em": self.criada_em,
            "lida_em": self.lida_em,
            "email_destinatario": self.email_destinatario,
            "email_status": self.email_status,
            "email_enviado_em": self.email_enviado_em,
        }

    @classmethod
    def from_dict(cls, dados):
        return cls(
            id_notificacao=dados.get("id", 0),
            usuario_id=dados["usuario_id"],
            tipo=dados["tipo"],
            titulo=dados["titulo"],
            mensagem=dados["mensagem"],
            chave_deduplicacao=dados["chave_deduplicacao"],
            referencia_tipo=dados.get("referencia_tipo"),
            referencia_id=dados.get("referencia_id"),
            lida=dados.get("lida", False),
            criada_em=dados.get("criada_em"),
            lida_em=dados.get("lida_em"),
            email_destinatario=dados.get("email_destinatario"),
            email_status=dados.get(
                "email_status",
                "nao_aplicavel",
            ),
            email_enviado_em=dados.get("email_enviado_em"),
        )
