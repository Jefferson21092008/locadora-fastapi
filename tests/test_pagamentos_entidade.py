from modulos.pagamentos import (
    PagamentoFinanceiro,
)


def test_pagamento_financeiro_valida_e_estorna():
    pagamento = PagamentoFinanceiro(
        id_pagamento=1,
        aluguel_id=10,
        valor=150,
        forma="pix",
    )

    assert pagamento.validar_dados() == (
        True,
        "",
    )
    assert pagamento.confirmado is True

    sucesso, _ = pagamento.estornar()

    assert sucesso is True
    assert pagamento.confirmado is False
    assert pagamento.status == "estornado"
    assert pagamento.estornado_em is not None


def test_pagamento_financeiro_rejeita_parcelas_fora_do_credito():
    pagamento = PagamentoFinanceiro(
        id_pagamento=1,
        aluguel_id=10,
        valor=150,
        forma="pix",
        parcelas=2,
    )

    valido, mensagem = (
        pagamento.validar_dados()
    )

    assert valido is False
    assert "Parcelas" in mensagem
