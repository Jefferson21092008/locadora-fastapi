from datetime import date


class Manutencao:
    STATUS_ATIVA = "ativa"
    STATUS_FINALIZADA = "finalizada"

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
    ):
        self.id = id_manutencao
        self.veiculo_id = veiculo_id

        self.motivo = str(
            motivo
        ).strip()

        self.quilometragem = float(
            quilometragem
        )

        self.custo = float(
            custo
        )

        self.data_inicio = (
            data_inicio
            or date.today().isoformat()
        )

        self.data_fim = data_fim

        self.status = status

    # ================================================================
    # PROPRIEDADES
    # ================================================================

    @property
    def ativa(self):
        return (
            self.status
            == self.STATUS_ATIVA
        )

    # ================================================================
    # VALIDAÇÃO
    # ================================================================

    def validar_dados(self):
        if not self.motivo:
            return (
                False,
                "O motivo da manutenção "
                "não pode ficar vazio.",
            )

        if self.quilometragem < 0:
            return (
                False,
                "A quilometragem não pode "
                "ser negativa.",
            )

        if self.custo < 0:
            return (
                False,
                "O custo não pode ser negativo.",
            )

        if self.status not in (
            self.STATUS_ATIVA,
            self.STATUS_FINALIZADA,
        ):
            return (
                False,
                "Status de manutenção inválido.",
            )

        return True, ""

    # ================================================================
    # FINALIZAÇÃO
    # ================================================================

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
            custo = float(
                custo
            )

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

        self.data_fim = (
            data_fim
            or date.today().isoformat()
        )

        self.status = (
            self.STATUS_FINALIZADA
        )

        return (
            True,
            "Manutenção finalizada com sucesso.",
        )

    # ================================================================
    # SERIALIZAÇÃO
    # ================================================================

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
        )