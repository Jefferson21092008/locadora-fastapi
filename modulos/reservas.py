from datetime import date, datetime, timezone


class Reserva:
    """Representa a intenção de uso futuro de um veículo."""

    STATUS_VALIDOS = {
        "ativa",
        "cancelada",
        "convertida",
    }

    def __init__(
        self,
        id_reserva,
        cliente_id,
        cliente_usuario,
        cliente_nome,
        veiculo_id,
        veiculo_tipo,
        veiculo_modelo,
        data_inicio,
        data_fim,
        status="ativa",
        criada_em=None,
        cancelada_em=None,
        convertida_em=None,
    ):
        self.id = id_reserva
        self.cliente_id = int(cliente_id)
        self.cliente_usuario = str(cliente_usuario).strip()
        self.cliente_nome = str(cliente_nome).strip()
        self.veiculo_id = int(veiculo_id)
        self.veiculo_tipo = str(veiculo_tipo).strip()
        self.veiculo_modelo = str(veiculo_modelo).strip()
        self.data_inicio = str(data_inicio).strip()
        self.data_fim = str(data_fim).strip()
        self.status = str(status).strip().lower()
        self.criada_em = (
            criada_em
            or datetime.now(
                timezone.utc
            ).isoformat()
        )
        self.cancelada_em = cancelada_em
        self.convertida_em = convertida_em

    @property
    def ativa(self):
        return self.status == "ativa"

    @property
    def expirada(self):
        if not self.ativa:
            return False

        try:
            return (
                date.fromisoformat(
                    self.data_fim
                )
                <= date.today()
            )
        except ValueError:
            return False

    @property
    def situacao(self):
        if self.expirada:
            return "expirada"

        return self.status

    def validar_dados(self):
        if self.cliente_id <= 0:
            return False, "Cliente inválido."

        if self.veiculo_id <= 0:
            return False, "Veículo inválido."

        if not self.cliente_usuario:
            return False, "Usuário do cliente é obrigatório."

        if not self.cliente_nome:
            return False, "Nome do cliente é obrigatório."

        if not self.veiculo_modelo:
            return False, "Modelo do veículo é obrigatório."

        if self.status not in self.STATUS_VALIDOS:
            return False, "Status de reserva inválido."

        try:
            inicio = date.fromisoformat(
                self.data_inicio
            )
            fim = date.fromisoformat(
                self.data_fim
            )
        except ValueError:
            return False, "Datas da reserva inválidas."

        if fim <= inicio:
            return (
                False,
                "A data final deve ser posterior à data inicial.",
            )

        return True, ""

    def pertence_ao_cliente(
        self,
        cliente,
    ):
        return (
            self.cliente_id
            == cliente.id
        )

    def cancelar(self):
        if not self.ativa:
            return (
                False,
                "Apenas reservas ativas podem ser canceladas.",
            )

        if self.expirada:
            return (
                False,
                "Uma reserva expirada não pode ser cancelada.",
            )

        self.status = "cancelada"
        self.cancelada_em = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        return True, ""

    def converter(self):
        if not self.ativa:
            return (
                False,
                "Apenas reservas ativas podem ser convertidas em aluguel.",
            )

        self.status = "convertida"
        self.convertida_em = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        return True, ""

    def restaurar_ativa(self):
        if self.status != "convertida":
            return False

        self.status = "ativa"
        self.convertida_em = None
        return True

    def to_dict(self):
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "cliente_usuario": self.cliente_usuario,
            "cliente_nome": self.cliente_nome,
            "veiculo_id": self.veiculo_id,
            "veiculo_tipo": self.veiculo_tipo,
            "veiculo_modelo": self.veiculo_modelo,
            "data_inicio": self.data_inicio,
            "data_fim": self.data_fim,
            "status": self.status,
            "criada_em": self.criada_em,
            "cancelada_em": self.cancelada_em,
            "convertida_em": self.convertida_em,
        }

    @classmethod
    def from_dict(cls, dados):
        return cls(
            id_reserva=dados.get("id", 0),
            cliente_id=dados["cliente_id"],
            cliente_usuario=dados["cliente_usuario"],
            cliente_nome=dados["cliente_nome"],
            veiculo_id=dados["veiculo_id"],
            veiculo_tipo=dados["veiculo_tipo"],
            veiculo_modelo=dados["veiculo_modelo"],
            data_inicio=dados["data_inicio"],
            data_fim=dados["data_fim"],
            status=dados.get("status", "ativa"),
            criada_em=dados.get("criada_em"),
            cancelada_em=dados.get("cancelada_em"),
            convertida_em=dados.get("convertida_em"),
        )
