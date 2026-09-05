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
