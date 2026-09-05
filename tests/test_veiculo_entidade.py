from modulos.veiculos import (
    Carro,
    StatusVeiculo,
)


def criar_carro():
    return Carro(
        id_veiculo=1,
        modelo="Civic",
        ano=2025,
        diaria=100,
        preco_km=0.50,
    )


# ================================================================
# STATUS INICIAL
# ================================================================

def test_veiculo_novo_comeca_disponivel():
    carro = criar_carro()

    assert (
        carro.status
        == StatusVeiculo.DISPONIVEL
    )

    assert carro.disponivel is True
    assert carro.ativo is True


# ================================================================
# ALUGUEL
# ================================================================

def test_alugar_muda_status_para_alugado():
    carro = criar_carro()

    sucesso = carro.alugar(
        "lucas"
    )

    assert sucesso is True

    assert (
        carro.status
        == StatusVeiculo.ALUGADO
    )

    assert carro.disponivel is False
    assert carro.ativo is True
    assert carro.alugado_por == "lucas"


# ================================================================
# MANUTENÇÃO
# ================================================================

def test_enviar_veiculo_para_manutencao():
    carro = criar_carro()

    sucesso = (
        carro.enviar_para_manutencao()
    )

    assert sucesso is True

    assert (
        carro.status
        == StatusVeiculo.MANUTENCAO
    )

    assert carro.disponivel is False
    assert carro.ativo is True


def test_finalizar_manutencao():
    carro = criar_carro()

    carro.enviar_para_manutencao()

    sucesso = (
        carro.finalizar_manutencao()
    )

    assert sucesso is True

    assert (
        carro.status
        == StatusVeiculo.DISPONIVEL
    )

    assert carro.disponivel is True


def test_veiculo_alugado_nao_pode_entrar_em_manutencao():
    carro = criar_carro()

    carro.alugar(
        "lucas"
    )

    sucesso = (
        carro.enviar_para_manutencao()
    )

    assert sucesso is False

    assert (
        carro.status
        == StatusVeiculo.ALUGADO
    )

    assert carro.alugado_por == "lucas"


# ================================================================
# DESATIVAÇÃO
# ================================================================

def test_veiculo_desativado_tem_status_correspondente():
    carro = criar_carro()

    sucesso, mensagem = (
        carro.desativar()
    )

    assert sucesso is True

    assert (
        carro.status
        == StatusVeiculo.DESATIVADO
    )

    assert carro.ativo is False
    assert carro.disponivel is False
