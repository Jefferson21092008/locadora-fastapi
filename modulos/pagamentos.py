from datetime import datetime, timezone


class Pagamento:
    """Responsável apenas pelas regras de cálculo dos pagamentos."""

    FORMAS = {
        1: ("Dinheiro", -0.10),
        2: ("Pix", -0.15),
        3: ("Débito", -0.05),
        4: ("Crédito à vista", 0.0),
        6: ("Boleto", -0.05),
        7: ("Transferência", -0.05),
    }

    @classmethod
    def calcular(cls, total, opcao, parcelas=None):
        if opcao == 5:
            return cls._calcular_credito_parcelado(total, parcelas)

        if opcao not in cls.FORMAS:
            return None

        forma, taxa = cls.FORMAS[opcao]
        valor_final = total * (1 + taxa)

        return {
            "valor_final": valor_final,
            "forma": forma,
            "parcelas": 1,
            "valor_parcela": valor_final,
        }

    @staticmethod
    def _calcular_credito_parcelado(total, parcelas):
        if parcelas is None or not 2 <= parcelas <= 12:
            return None

        if parcelas <= 2:
            juros = 0.0
        elif parcelas <= 6:
            juros = 0.10
        else:
            juros = 0.20

        valor_final = total * (1 + juros)

        return {
            "valor_final": valor_final,
            "forma": f"Crédito {parcelas}x",
            "parcelas": parcelas,
            "valor_parcela": valor_final / parcelas,
        }

class PagamentoFinanceiro:
    """Representa uma liquidação financeira adicional de um aluguel."""

    FORMAS = {
        "dinheiro",
        "pix",
        "debito",
        "credito",
        "boleto",
        "transferencia",
    }

    STATUS_CONFIRMADO = "confirmado"
    STATUS_ESTORNADO = "estornado"

    def __init__(
        self,
        id_pagamento,
        aluguel_id,
        valor,
        forma,
        parcelas=1,
        observacoes=None,
        status=STATUS_CONFIRMADO,
        criado_em=None,
        estornado_em=None,
    ):
        self.id = id_pagamento
        self.aluguel_id = int(aluguel_id)
        self.valor = float(valor)
        self.forma = str(forma).strip().lower()
        self.parcelas = int(parcelas)
        self.observacoes = (
            str(observacoes).strip()
            if observacoes not in (None, "")
            else None
        )
        self.status = str(status).strip().lower()
        self.criado_em = (
            criado_em
            or datetime.now(timezone.utc).isoformat()
        )
        self.estornado_em = estornado_em

    @property
    def confirmado(self):
        return self.status == self.STATUS_CONFIRMADO

    def validar_dados(self):
        if self.aluguel_id <= 0:
            return False, "Aluguel inválido."

        if self.valor <= 0:
            return (
                False,
                "O valor do pagamento deve ser maior que zero.",
            )

        if self.forma not in self.FORMAS:
            return False, "Forma de pagamento inválida."

        if not 1 <= self.parcelas <= 12:
            return (
                False,
                "A quantidade de parcelas deve estar entre 1 e 12.",
            )

        if (
            self.forma != "credito"
            and self.parcelas != 1
        ):
            return (
                False,
                "Parcelas só podem ser usadas em pagamento por crédito.",
            )

        if self.status not in {
            self.STATUS_CONFIRMADO,
            self.STATUS_ESTORNADO,
        }:
            return False, "Status de pagamento inválido."

        return True, ""

    def estornar(self):
        if self.status == self.STATUS_ESTORNADO:
            return False, "Pagamento já estornado."

        self.status = self.STATUS_ESTORNADO
        self.estornado_em = (
            datetime.now(timezone.utc).isoformat()
        )
        return True, "Pagamento estornado com sucesso."

    def to_dict(self):
        return {
            "id": self.id,
            "aluguel_id": self.aluguel_id,
            "valor": self.valor,
            "forma": self.forma,
            "parcelas": self.parcelas,
            "observacoes": self.observacoes,
            "status": self.status,
            "criado_em": self.criado_em,
            "estornado_em": self.estornado_em,
        }

