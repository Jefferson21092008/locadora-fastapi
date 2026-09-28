from datetime import datetime, timezone


def _agora_iso():
    return datetime.now(
        timezone.utc
    ).isoformat()


def _texto_opcional(valor):
    if valor is None:
        return None

    texto = str(valor).strip()
    return texto or None


class InspecaoAluguel:
    TIPO_RETIRADA = "retirada"
    TIPO_DEVOLUCAO = "devolucao"

    def __init__(
        self,
        id_inspecao,
        aluguel_id,
        tipo,
        quilometragem,
        combustivel_percentual,
        observacoes=None,
        criada_em=None,
    ):
        self.id = id_inspecao
        self.aluguel_id = int(
            aluguel_id
        )
        self.tipo = str(
            tipo
        ).strip().lower()
        self.quilometragem = float(
            quilometragem
        )
        self.combustivel_percentual = int(
            combustivel_percentual
        )
        self.observacoes = _texto_opcional(
            observacoes
        )
        self.criada_em = (
            criada_em
            or _agora_iso()
        )

    def validar_dados(self):
        if self.aluguel_id <= 0:
            return (
                False,
                "Aluguel inválido.",
            )

        if self.tipo not in (
            self.TIPO_RETIRADA,
            self.TIPO_DEVOLUCAO,
        ):
            return (
                False,
                "Tipo de inspeção inválido.",
            )

        if self.quilometragem < 0:
            return (
                False,
                "A quilometragem não pode ser negativa.",
            )

        if not 0 <= self.combustivel_percentual <= 100:
            return (
                False,
                "O nível de combustível deve ficar "
                "entre 0 e 100%.",
            )

        return True, ""

    def to_dict(self):
        return {
            "id": self.id,
            "aluguel_id": self.aluguel_id,
            "tipo": self.tipo,
            "quilometragem": self.quilometragem,
            "combustivel_percentual": (
                self.combustivel_percentual
            ),
            "observacoes": self.observacoes,
            "criada_em": self.criada_em,
        }

    @classmethod
    def from_dict(
        cls,
        dados,
    ):
        return cls(
            id_inspecao=dados.get(
                "id",
                0,
            ),
            aluguel_id=dados.get(
                "aluguel_id"
            ),
            tipo=dados.get(
                "tipo",
                "",
            ),
            quilometragem=dados.get(
                "quilometragem",
                0,
            ),
            combustivel_percentual=dados.get(
                "combustivel_percentual",
                0,
            ),
            observacoes=dados.get(
                "observacoes"
            ),
            criada_em=dados.get(
                "criada_em"
            ),
        )


class DanoAluguel:
    STATUS_ATIVO = "ativo"
    STATUS_CANCELADO = "cancelado"

    def __init__(
        self,
        id_dano,
        aluguel_id,
        descricao,
        valor_estimado,
        status=STATUS_ATIVO,
        criada_em=None,
        cancelada_em=None,
    ):
        self.id = id_dano
        self.aluguel_id = int(
            aluguel_id
        )
        self.descricao = str(
            descricao
        ).strip()
        self.valor_estimado = float(
            valor_estimado
        )
        self.status = str(
            status
        ).strip().lower()
        self.criada_em = (
            criada_em
            or _agora_iso()
        )
        self.cancelada_em = (
            cancelada_em
        )

    @property
    def ativo(self):
        return (
            self.status
            == self.STATUS_ATIVO
        )

    def validar_dados(self):
        if self.aluguel_id <= 0:
            return (
                False,
                "Aluguel inválido.",
            )

        if len(self.descricao) < 3:
            return (
                False,
                "Descreva o dano com pelo menos 3 caracteres.",
            )

        if self.valor_estimado < 0:
            return (
                False,
                "O valor estimado do dano não pode ser negativo.",
            )

        if self.status not in (
            self.STATUS_ATIVO,
            self.STATUS_CANCELADO,
        ):
            return (
                False,
                "Status de dano inválido.",
            )

        return True, ""

    def cancelar(self):
        if not self.ativo:
            return (
                False,
                "O dano já está cancelado.",
            )

        self.status = (
            self.STATUS_CANCELADO
        )
        self.cancelada_em = (
            _agora_iso()
        )

        return (
            True,
            "Dano cancelado com sucesso.",
        )

    def to_dict(self):
        return {
            "id": self.id,
            "aluguel_id": self.aluguel_id,
            "descricao": self.descricao,
            "valor_estimado": self.valor_estimado,
            "status": self.status,
            "criada_em": self.criada_em,
            "cancelada_em": self.cancelada_em,
        }

    @classmethod
    def from_dict(
        cls,
        dados,
    ):
        return cls(
            id_dano=dados.get(
                "id",
                0,
            ),
            aluguel_id=dados.get(
                "aluguel_id"
            ),
            descricao=dados.get(
                "descricao",
                "",
            ),
            valor_estimado=dados.get(
                "valor_estimado",
                0,
            ),
            status=dados.get(
                "status",
                cls.STATUS_ATIVO,
            ),
            criada_em=dados.get(
                "criada_em"
            ),
            cancelada_em=dados.get(
                "cancelada_em"
            ),
        )


class MultaTransito:
    STATUS_ATIVA = "ativa"
    STATUS_CANCELADA = "cancelada"

    def __init__(
        self,
        id_multa,
        aluguel_id,
        descricao,
        valor,
        data_ocorrencia,
        status=STATUS_ATIVA,
        criada_em=None,
        cancelada_em=None,
    ):
        self.id = id_multa
        self.aluguel_id = int(
            aluguel_id
        )
        self.descricao = str(
            descricao
        ).strip()
        self.valor = float(
            valor
        )
        self.data_ocorrencia = str(
            data_ocorrencia
        ).strip()
        self.status = str(
            status
        ).strip().lower()
        self.criada_em = (
            criada_em
            or _agora_iso()
        )
        self.cancelada_em = (
            cancelada_em
        )

    @property
    def ativa(self):
        return (
            self.status
            == self.STATUS_ATIVA
        )

    def validar_dados(self):
        if self.aluguel_id <= 0:
            return (
                False,
                "Aluguel inválido.",
            )

        if len(self.descricao) < 3:
            return (
                False,
                "Descreva a multa com pelo menos 3 caracteres.",
            )

        if self.valor < 0:
            return (
                False,
                "O valor da multa não pode ser negativo.",
            )

        try:
            datetime.fromisoformat(
                self.data_ocorrencia
            )
        except ValueError:
            return (
                False,
                "Data da ocorrência inválida.",
            )

        if self.status not in (
            self.STATUS_ATIVA,
            self.STATUS_CANCELADA,
        ):
            return (
                False,
                "Status de multa inválido.",
            )

        return True, ""

    def cancelar(self):
        if not self.ativa:
            return (
                False,
                "A multa já está cancelada.",
            )

        self.status = (
            self.STATUS_CANCELADA
        )
        self.cancelada_em = (
            _agora_iso()
        )

        return (
            True,
            "Multa cancelada com sucesso.",
        )

    def to_dict(self):
        return {
            "id": self.id,
            "aluguel_id": self.aluguel_id,
            "descricao": self.descricao,
            "valor": self.valor,
            "data_ocorrencia": (
                self.data_ocorrencia
            ),
            "status": self.status,
            "criada_em": self.criada_em,
            "cancelada_em": self.cancelada_em,
        }

    @classmethod
    def from_dict(
        cls,
        dados,
    ):
        return cls(
            id_multa=dados.get(
                "id",
                0,
            ),
            aluguel_id=dados.get(
                "aluguel_id"
            ),
            descricao=dados.get(
                "descricao",
                "",
            ),
            valor=dados.get(
                "valor",
                0,
            ),
            data_ocorrencia=dados.get(
                "data_ocorrencia",
                "",
            ),
            status=dados.get(
                "status",
                cls.STATUS_ATIVA,
            ),
            criada_em=dados.get(
                "criada_em"
            ),
            cancelada_em=dados.get(
                "cancelada_em"
            ),
        )


class CaucaoAluguel:
    STATUS_RETIDA = "retida"
    STATUS_PARCIAL = "parcial"
    STATUS_LIBERADA = "liberada"

    def __init__(
        self,
        id_caucao,
        aluguel_id,
        valor,
        valor_liberado=0,
        status=None,
        observacoes=None,
        criada_em=None,
        atualizada_em=None,
    ):
        self.id = id_caucao
        self.aluguel_id = int(
            aluguel_id
        )
        self.valor = float(
            valor
        )
        self.valor_liberado = float(
            valor_liberado
        )
        self.status = (
            status
            or self._calcular_status()
        )
        self.observacoes = _texto_opcional(
            observacoes
        )
        self.criada_em = (
            criada_em
            or _agora_iso()
        )
        self.atualizada_em = (
            atualizada_em
            or self.criada_em
        )

    def _calcular_status(self):
        if self.valor_liberado <= 0:
            return self.STATUS_RETIDA

        if self.valor_liberado >= self.valor:
            return self.STATUS_LIBERADA

        return self.STATUS_PARCIAL

    @property
    def valor_retido(self):
        return max(
            self.valor
            - self.valor_liberado,
            0,
        )

    def validar_dados(self):
        if self.aluguel_id <= 0:
            return (
                False,
                "Aluguel inválido.",
            )

        if self.valor <= 0:
            return (
                False,
                "O valor da caução deve ser maior que zero.",
            )

        if self.valor_liberado < 0:
            return (
                False,
                "O valor liberado não pode ser negativo.",
            )

        if (
            self.valor_liberado
            > self.valor
        ):
            return (
                False,
                "O valor liberado não pode superar a caução.",
            )

        if self.status not in (
            self.STATUS_RETIDA,
            self.STATUS_PARCIAL,
            self.STATUS_LIBERADA,
        ):
            return (
                False,
                "Status de caução inválido.",
            )

        return True, ""

    def atualizar(
        self,
        valor,
        valor_liberado=0,
        observacoes=None,
    ):
        estado_anterior = vars(
            self
        ).copy()

        try:
            self.valor = float(
                valor
            )
            self.valor_liberado = float(
                valor_liberado
            )
            self.observacoes = (
                _texto_opcional(
                    observacoes
                )
            )
            self.status = (
                self._calcular_status()
            )
            self.atualizada_em = (
                _agora_iso()
            )
        except (
            TypeError,
            ValueError,
        ):
            self.__dict__.clear()
            self.__dict__.update(
                estado_anterior
            )
            return (
                False,
                "Dados da caução inválidos.",
            )

        valido, mensagem = (
            self.validar_dados()
        )

        if not valido:
            self.__dict__.clear()
            self.__dict__.update(
                estado_anterior
            )
            return False, mensagem

        return (
            True,
            "Caução atualizada com sucesso.",
        )

    def to_dict(self):
        return {
            "id": self.id,
            "aluguel_id": self.aluguel_id,
            "valor": self.valor,
            "valor_liberado": (
                self.valor_liberado
            ),
            "valor_retido": (
                self.valor_retido
            ),
            "status": self.status,
            "observacoes": self.observacoes,
            "criada_em": self.criada_em,
            "atualizada_em": self.atualizada_em,
        }

    @classmethod
    def from_dict(
        cls,
        dados,
    ):
        return cls(
            id_caucao=dados.get(
                "id",
                0,
            ),
            aluguel_id=dados.get(
                "aluguel_id"
            ),
            valor=dados.get(
                "valor",
                0,
            ),
            valor_liberado=dados.get(
                "valor_liberado",
                0,
            ),
            status=dados.get(
                "status"
            ),
            observacoes=dados.get(
                "observacoes"
            ),
            criada_em=dados.get(
                "criada_em"
            ),
            atualizada_em=dados.get(
                "atualizada_em"
            ),
        )
