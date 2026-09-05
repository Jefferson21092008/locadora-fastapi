from modulos.manutencoes import (
    Manutencao,
)


def criar_manutencao():
    return Manutencao(
        id_manutencao=1,
        veiculo_id=1,
        motivo="Troca de óleo",
        quilometragem=10000,
    )


def test_manutencao_comeca_ativa():
    manutencao = criar_manutencao()

    assert manutencao.ativa is True
    assert manutencao.status == "ativa"

    assert manutencao.custo == 0

    assert manutencao.data_fim is None


def test_finalizar_manutencao():
    manutencao = criar_manutencao()

    sucesso, mensagem = (
        manutencao.finalizar(
            custo=350,
        )
    )

    assert sucesso is True

    assert manutencao.ativa is False

    assert (
        manutencao.status
        == "finalizada"
    )

    assert manutencao.custo == 350

    assert manutencao.data_fim is not None


def test_nao_finalizar_manutencao_duas_vezes():
    manutencao = criar_manutencao()

    manutencao.finalizar(
        custo=350
    )

    sucesso, mensagem = (
        manutencao.finalizar(
            custo=400
        )
    )

    assert sucesso is False

    assert manutencao.custo == 350


def test_manutencao_nao_aceita_custo_negativo():
    manutencao = criar_manutencao()

    sucesso, mensagem = (
        manutencao.finalizar(
            custo=-100
        )
    )

    assert sucesso is False
    assert manutencao.ativa is True