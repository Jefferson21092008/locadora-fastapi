from datetime import date, timedelta

from modulos.reservas import Reserva


def criar_reserva(**alteracoes):
    amanha = date.today() + timedelta(days=1)
    dados = {
        "id_reserva": 1,
        "cliente_id": 10,
        "cliente_usuario": "ana123",
        "cliente_nome": "Ana",
        "veiculo_id": 20,
        "veiculo_tipo": "Carro",
        "veiculo_modelo": "Civic",
        "data_inicio": amanha.isoformat(),
        "data_fim": (
            amanha
            + timedelta(days=3)
        ).isoformat(),
    }
    dados.update(alteracoes)
    return Reserva(**dados)


def test_reserva_valida_periodo_e_serializacao():
    reserva = criar_reserva()

    valido, mensagem = reserva.validar_dados()

    assert valido is True
    assert mensagem == ""
    assert reserva.ativa is True
    assert reserva.expirada is False
    assert reserva.situacao == "ativa"
    assert reserva.to_dict()["veiculo_modelo"] == "Civic"


def test_reserva_rejeita_periodo_invertido():
    amanha = date.today() + timedelta(days=1)
    reserva = criar_reserva(
        data_inicio=amanha.isoformat(),
        data_fim=amanha.isoformat(),
    )

    valido, mensagem = reserva.validar_dados()

    assert valido is False
    assert "posterior" in mensagem


def test_reserva_pode_ser_cancelada():
    reserva = criar_reserva()

    sucesso, mensagem = reserva.cancelar()

    assert sucesso is True
    assert mensagem == ""
    assert reserva.status == "cancelada"
    assert reserva.cancelada_em is not None


def test_reserva_convertida_pode_ser_restaurada():
    reserva = criar_reserva()

    sucesso, _ = reserva.converter()

    assert sucesso is True
    assert reserva.status == "convertida"
    assert reserva.convertida_em is not None

    assert reserva.restaurar_ativa() is True
    assert reserva.status == "ativa"
    assert reserva.convertida_em is None


def test_reserva_expirada_tem_situacao_derivada():
    ontem = date.today() - timedelta(days=2)
    reserva = criar_reserva(
        data_inicio=ontem.isoformat(),
        data_fim=(
            ontem
            + timedelta(days=1)
        ).isoformat(),
    )

    assert reserva.expirada is True
    assert reserva.situacao == "expirada"
