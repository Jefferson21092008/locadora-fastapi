from datetime import datetime, timezone

import pytest

from modulos.eventos import (
    BarramentoEventos,
    EventoAplicacao,
    publicar_evento,
)


def test_evento_gera_envelope_versionado_e_serializavel():
    ocorrido_em = datetime(
        2026,
        10,
        6,
        3,
        0,
        tzinfo=timezone.utc,
    )
    evento = EventoAplicacao(
        nome="aluguel.criado",
        agregado_tipo="aluguel",
        agregado_id=42,
        dados={"veiculo_id": 7},
        ocorrido_em=ocorrido_em,
    )

    payload = evento.para_dict()

    assert payload["id_evento"]
    assert payload["nome"] == "aluguel.criado"
    assert payload["versao"] == 1
    assert payload["ocorrido_em"] == ocorrido_em.isoformat()
    assert payload["agregado"] == {
        "tipo": "aluguel",
        "id": 42,
    }
    assert payload["dados"] == {"veiculo_id": 7}


def test_evento_rejeita_nome_vazio():
    with pytest.raises(ValueError):
        EventoAplicacao(nome="   ")


def test_barramento_despacha_handler_exato_e_coringa():
    barramento = BarramentoEventos()
    recebidos = []

    barramento.assinar(
        "aluguel.criado",
        lambda evento: recebidos.append(("exato", evento.nome)),
    )
    barramento.assinar(
        "*",
        lambda evento: recebidos.append(("coringa", evento.nome)),
    )

    resultado = barramento.publicar(
        EventoAplicacao(nome="aluguel.criado")
    )

    assert recebidos == [
        ("exato", "aluguel.criado"),
        ("coringa", "aluguel.criado"),
    ]
    assert resultado.handlers_encontrados == 2
    assert resultado.handlers_executados == 2
    assert resultado.sucesso is True


def test_barramento_isola_falha_de_handler_e_continua_despacho():
    barramento = BarramentoEventos()
    recebidos = []

    def falhar(_evento):
        raise RuntimeError("falha controlada")

    def concluir(evento):
        recebidos.append(evento.nome)

    barramento.assinar("pagamento.registrado", falhar)
    barramento.assinar("pagamento.registrado", concluir)

    resultado = barramento.publicar(
        EventoAplicacao(nome="pagamento.registrado")
    )

    assert recebidos == ["pagamento.registrado"]
    assert resultado.handlers_encontrados == 2
    assert resultado.handlers_executados == 1
    assert len(resultado.falhas) == 1
    assert resultado.sucesso is False


def test_assinatura_nao_duplica_mesmo_handler():
    barramento = BarramentoEventos()
    recebidos = []

    def handler(evento):
        recebidos.append(evento.nome)

    barramento.assinar("reserva.criada", handler)
    barramento.assinar("reserva.criada", handler)

    barramento.publicar(
        EventoAplicacao(nome="reserva.criada")
    )

    assert recebidos == ["reserva.criada"]


def test_desassinar_remove_handler():
    barramento = BarramentoEventos()
    recebidos = []

    def handler(evento):
        recebidos.append(evento.nome)

    barramento.assinar("reserva.cancelada", handler)

    assert barramento.desassinar("reserva.cancelada", handler) is True
    assert barramento.desassinar("reserva.cancelada", handler) is False

    barramento.publicar(
        EventoAplicacao(nome="reserva.cancelada")
    )

    assert recebidos == []


def test_publicar_evento_sem_barramento_e_noop():
    assert (
        publicar_evento(
            None,
            "aluguel.criado",
            agregado_id=1,
        )
        is None
    )
