from modulos.notificacoes import Notificacao


def criar_notificacao(**alteracoes):
    dados = {
        "id_notificacao": 1,
        "usuario_id": 2,
        "tipo": "reserva_proxima",
        "titulo": "Reserva amanhã",
        "mensagem": "Seu veículo está reservado.",
        "chave_deduplicacao": "usuario:2:reserva:10:d1",
        "referencia_tipo": "reserva",
        "referencia_id": 10,
        "email_destinatario": "cliente@example.com",
        "email_status": "pendente",
    }
    dados.update(alteracoes)
    return Notificacao(**dados)


def test_notificacao_valida_e_marca_como_lida():
    notificacao = criar_notificacao()

    assert notificacao.validar_dados() == (True, "")
    assert notificacao.nao_lida is True
    assert notificacao.marcar_como_lida() is True
    assert notificacao.lida is True
    assert notificacao.lida_em is not None
    assert notificacao.marcar_como_lida() is False


def test_notificacao_atualiza_status_de_email():
    notificacao = criar_notificacao()

    notificacao.atualizar_status_email("enviado")

    assert notificacao.email_status == "enviado"
    assert notificacao.email_enviado_em is not None


def test_notificacao_rejeita_tipo_invalido():
    notificacao = criar_notificacao(tipo="outro")

    valido, mensagem = notificacao.validar_dados()

    assert valido is False
    assert "Tipo" in mensagem
