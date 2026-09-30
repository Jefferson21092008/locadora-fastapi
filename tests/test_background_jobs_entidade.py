from modulos.background_jobs import TarefaBackground


def test_tarefa_background_valida_dados_basicos():
    tarefa = TarefaBackground(
        id_tarefa=0,
        tipo="sincronizar_notificacoes_usuario",
        chave_deduplicacao="notificacoes:2026-09-30:usuario:1",
        payload={"usuario_id": 1},
    )

    valido, mensagem = tarefa.validar_dados()

    assert valido is True
    assert mensagem == ""
    assert tarefa.status == "pendente"
    assert tarefa.pode_tentar_novamente is True


def test_tarefa_background_rejeita_tipo_desconhecido():
    tarefa = TarefaBackground(
        id_tarefa=0,
        tipo="desconhecida",
        chave_deduplicacao="x",
    )

    valido, mensagem = tarefa.validar_dados()

    assert valido is False
    assert mensagem == "Tipo de tarefa background inválido."


def test_tarefa_background_rejeita_payload_nao_serializavel():
    tarefa = TarefaBackground(
        id_tarefa=0,
        tipo="sincronizar_notificacoes_usuario",
        chave_deduplicacao="x",
        payload={"valor": object()},
    )

    valido, mensagem = tarefa.validar_dados()

    assert valido is False
    assert mensagem == "Payload da tarefa não é serializável em JSON."
