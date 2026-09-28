from datetime import date


class Manutencao:
    STATUS_ATIVA = "ativa"
    STATUS_FINALIZADA = "finalizada"

    TIPO_PREVENTIVA = "preventiva"
    TIPO_CORRETIVA = "corretiva"

    PRIORIDADE_BAIXA = "baixa"
    PRIORIDADE_MEDIA = "media"
    PRIORIDADE_ALTA = "alta"

    def __init__(
        self,
        id_manutencao,
        veiculo_id,
        motivo,
        quilometragem,
        custo=0,
        data_inicio=None,
        data_fim=None,
        status=STATUS_ATIVA,
        tipo=TIPO_CORRETIVA,
        prioridade=PRIORIDADE_MEDIA,
        fornecedor=None,
        custo_estimado=0,
        data_prevista=None,
        observacoes=None,
    ):
        self.id = id_manutencao
        self.veiculo_id = veiculo_id
        self.motivo = str(motivo).strip()
        self.quilometragem = float(quilometragem)
        self.custo = float(custo)
        self.data_inicio = data_inicio or date.today().isoformat()
        self.data_fim = data_fim
        self.status = status
        self.tipo = str(tipo).strip().lower()
        self.prioridade = str(prioridade).strip().lower()
        self.fornecedor = self._normalizar_texto_opcional(
            fornecedor
        )
        self.custo_estimado = float(custo_estimado)
        self.data_prevista = self._normalizar_texto_opcional(
            data_prevista
        )
        self.observacoes = self._normalizar_texto_opcional(
            observacoes
        )

    @staticmethod
    def _normalizar_texto_opcional(valor):
        if valor is None:
            return None

        texto = str(valor).strip()
        return texto or None

    @property
    def ativa(self):
        return self.status == self.STATUS_ATIVA

    @property
    def atrasada(self):
        if not self.ativa or not self.data_prevista:
            return False

        try:
            prevista = date.fromisoformat(
                self.data_prevista
            )
        except ValueError:
            return False

        return prevista < date.today()

    def validar_dados(self):
        if not self.motivo:
            return (
                False,
                "O motivo da manutenção não pode ficar vazio.",
            )

        if self.quilometragem < 0:
            return (
                False,
                "A quilometragem não pode ser negativa.",
            )

        if self.custo < 0:
            return (
                False,
                "O custo não pode ser negativo.",
            )

        if self.custo_estimado < 0:
            return (
                False,
                "O custo estimado não pode ser negativo.",
            )

        if self.status not in (
            self.STATUS_ATIVA,
            self.STATUS_FINALIZADA,
        ):
            return (
                False,
                "Status de manutenção inválido.",
            )

        if self.tipo not in (
            self.TIPO_PREVENTIVA,
            self.TIPO_CORRETIVA,
        ):
            return (
                False,
                "Tipo de manutenção inválido.",
            )

        if self.prioridade not in (
            self.PRIORIDADE_BAIXA,
            self.PRIORIDADE_MEDIA,
            self.PRIORIDADE_ALTA,
        ):
            return (
                False,
                "Prioridade de manutenção inválida.",
            )

        if self.data_prevista:
            try:
                prevista = date.fromisoformat(
                    self.data_prevista
                )
                inicio = date.fromisoformat(
                    self.data_inicio
                )
            except ValueError:
                return (
                    False,
                    "Data prevista inválida.",
                )

            if prevista < inicio:
                return (
                    False,
                    "A data prevista não pode ser anterior "
                    "à data de início.",
                )

        return True, ""

    def atualizar_detalhes(
        self,
        **alteracoes,
    ):
        if not self.ativa:
            return (
                False,
                "Apenas manutenções ativas podem ser editadas.",
            )

        campos_permitidos = {
            "motivo",
            "tipo",
            "prioridade",
            "fornecedor",
            "custo_estimado",
            "data_prevista",
            "observacoes",
        }

        desconhecidos = (
            set(alteracoes)
            - campos_permitidos
        )

        if desconhecidos:
            return (
                False,
                "Há campos de manutenção que não podem ser editados.",
            )

        if not alteracoes:
            return (
                False,
                "Informe pelo menos um campo para atualizar.",
            )

        for campo in (
            "motivo",
            "tipo",
            "prioridade",
        ):
            if (
                campo in alteracoes
                and alteracoes[campo] is None
            ):
                return (
                    False,
                    f"O campo {campo} não pode ser nulo.",
                )

        estado_anterior = vars(self).copy()

        try:
            if "motivo" in alteracoes:
                self.motivo = str(
                    alteracoes["motivo"]
                ).strip()

            if "tipo" in alteracoes:
                self.tipo = str(
                    alteracoes["tipo"]
                ).strip().lower()

            if "prioridade" in alteracoes:
                self.prioridade = str(
                    alteracoes["prioridade"]
                ).strip().lower()

            if "fornecedor" in alteracoes:
                self.fornecedor = (
                    self._normalizar_texto_opcional(
                        alteracoes["fornecedor"]
                    )
                )

            if "custo_estimado" in alteracoes:
                self.custo_estimado = float(
                    alteracoes["custo_estimado"]
                )

            if "data_prevista" in alteracoes:
                self.data_prevista = (
                    self._normalizar_texto_opcional(
                        alteracoes["data_prevista"]
                    )
                )

            if "observacoes" in alteracoes:
                self.observacoes = (
                    self._normalizar_texto_opcional(
                        alteracoes["observacoes"]
                    )
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
                "Dados de manutenção inválidos.",
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
            "Manutenção atualizada com sucesso.",
        )

    def finalizar(
        self,
        custo,
        data_fim=None,
    ):
        if not self.ativa:
            return (
                False,
                "A manutenção já foi finalizada.",
            )

        try:
            custo = float(custo)
        except (
            TypeError,
            ValueError,
        ):
            return (
                False,
                "Custo inválido.",
            )

        if custo < 0:
            return (
                False,
                "O custo não pode ser negativo.",
            )

        self.custo = custo
        self.data_fim = data_fim or date.today().isoformat()
        self.status = self.STATUS_FINALIZADA

        return (
            True,
            "Manutenção finalizada com sucesso.",
        )

    def to_dict(self):
        return {
            "id": self.id,
            "veiculo_id": self.veiculo_id,
            "motivo": self.motivo,
            "quilometragem": self.quilometragem,
            "custo": self.custo,
            "data_inicio": self.data_inicio,
            "data_fim": self.data_fim,
            "status": self.status,
            "tipo": self.tipo,
            "prioridade": self.prioridade,
            "fornecedor": self.fornecedor,
            "custo_estimado": self.custo_estimado,
            "data_prevista": self.data_prevista,
            "observacoes": self.observacoes,
            "atrasada": self.atrasada,
        }

    @classmethod
    def from_dict(
        cls,
        dados,
    ):
        return cls(
            id_manutencao=dados.get(
                "id",
                0,
            ),
            veiculo_id=dados.get(
                "veiculo_id"
            ),
            motivo=dados.get(
                "motivo",
                "",
            ),
            quilometragem=dados.get(
                "quilometragem",
                0,
            ),
            custo=dados.get(
                "custo",
                0,
            ),
            data_inicio=dados.get(
                "data_inicio"
            ),
            data_fim=dados.get(
                "data_fim"
            ),
            status=dados.get(
                "status",
                cls.STATUS_ATIVA,
            ),
            tipo=dados.get(
                "tipo",
                cls.TIPO_CORRETIVA,
            ),
            prioridade=dados.get(
                "prioridade",
                cls.PRIORIDADE_MEDIA,
            ),
            fornecedor=dados.get(
                "fornecedor"
            ),
            custo_estimado=dados.get(
                "custo_estimado",
                0,
            ),
            data_prevista=dados.get(
                "data_prevista"
            ),
            observacoes=dados.get(
                "observacoes"
            ),
        )
