import pytest

from modulos.vistorias import (
    CaucaoAluguel,
    DanoAluguel,
    InspecaoAluguel,
    MultaTransito,
)


def test_inspecao_valida_combustivel_e_quilometragem():
    inspecao = InspecaoAluguel(
        id_inspecao=1,
        aluguel_id=10,
        tipo="retirada",
        quilometragem=15000,
        combustivel_percentual=80,
    )

    assert inspecao.validar_dados() == (
        True,
        "",
    )
    assert inspecao.to_dict()[
        "combustivel_percentual"
    ] == 80


@pytest.mark.parametrize(
    "combustivel",
    [-1, 101],
)
def test_inspecao_rejeita_combustivel_fora_da_faixa(
    combustivel,
):
    inspecao = InspecaoAluguel(
        id_inspecao=1,
        aluguel_id=10,
        tipo="retirada",
        quilometragem=15000,
        combustivel_percentual=combustivel,
    )

    valido, mensagem = (
        inspecao.validar_dados()
    )

    assert valido is False
    assert "combustível" in mensagem


def test_dano_pode_ser_cancelado_sem_ser_apagado():
    dano = DanoAluguel(
        id_dano=2,
        aluguel_id=10,
        descricao="Risco na porta traseira",
        valor_estimado=350,
    )

    sucesso, _ = dano.cancelar()

    assert sucesso is True
    assert dano.status == "cancelado"
    assert dano.cancelada_em is not None


def test_multa_transito_valida_data_iso():
    multa = MultaTransito(
        id_multa=3,
        aluguel_id=10,
        descricao="Excesso de velocidade",
        valor=195.23,
        data_ocorrencia="data-invalida",
    )

    valido, mensagem = (
        multa.validar_dados()
    )

    assert valido is False
    assert "Data" in mensagem


def test_caucao_deriva_status_e_valor_retido():
    caucao = CaucaoAluguel(
        id_caucao=1,
        aluguel_id=10,
        valor=1000,
        valor_liberado=250,
    )

    assert caucao.status == "parcial"
    assert caucao.valor_retido == 750
    assert caucao.validar_dados() == (
        True,
        "",
    )


def test_caucao_rejeita_liberacao_maior_que_valor():
    caucao = CaucaoAluguel(
        id_caucao=1,
        aluguel_id=10,
        valor=500,
        valor_liberado=600,
    )

    valido, mensagem = (
        caucao.validar_dados()
    )

    assert valido is False
    assert "superar" in mensagem
