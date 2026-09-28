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


def test_manutencao_aceita_dados_operacionais_avancados():
    manutencao = Manutencao(
        id_manutencao=1,
        veiculo_id=1,
        motivo="Revisão dos freios",
        quilometragem=10000,
        tipo="preventiva",
        prioridade="alta",
        fornecedor="Oficina Central",
        custo_estimado=900,
        data_inicio="2026-09-28",
        data_prevista="2026-09-30",
        observacoes="Verificar pastilhas.",
    )

    valido, _ = manutencao.validar_dados()

    assert valido is True
    assert manutencao.tipo == "preventiva"
    assert manutencao.prioridade == "alta"
    assert manutencao.custo_estimado == 900
    assert manutencao.fornecedor == "Oficina Central"


def test_editar_manutencao_ativa():
    manutencao = criar_manutencao()

    sucesso, _ = manutencao.atualizar_detalhes(
        prioridade="alta",
        fornecedor="Oficina Norte",
        custo_estimado=500,
    )

    assert sucesso is True
    assert manutencao.prioridade == "alta"
    assert manutencao.fornecedor == "Oficina Norte"
    assert manutencao.custo_estimado == 500


def test_manutencao_rejeita_previsao_anterior_ao_inicio():
    manutencao = Manutencao(
        id_manutencao=1,
        veiculo_id=1,
        motivo="Revisão",
        quilometragem=10000,
        data_inicio="2026-09-28",
        data_prevista="2026-09-27",
    )

    valido, mensagem = manutencao.validar_dados()

    assert valido is False
    assert "data prevista" in mensagem.lower()
