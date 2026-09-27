import sentry_sdk

from api.monitoramento import (
    associar_request_id,
    configurar_monitoramento_erros,
    filtrar_evento_sensivel,
)


def test_monitoramento_fica_desativado_sem_dsn(
    monkeypatch,
):
    monkeypatch.delenv(
        "LOCADORA_SENTRY_DSN",
        raising=False,
    )

    chamado = False

    def init_falso(
        **kwargs,
    ):
        nonlocal chamado
        chamado = True

    monkeypatch.setattr(
        sentry_sdk,
        "init",
        init_falso,
    )

    assert (
        configurar_monitoramento_erros()
        is False
    )
    assert chamado is False


def test_monitoramento_configura_sentry_sem_pii(
    monkeypatch,
):
    configuracao = {}

    monkeypatch.setenv(
        "LOCADORA_SENTRY_DSN",
        "https://public@example.ingest.sentry.io/1",
    )
    monkeypatch.setenv(
        "LOCADORA_AMBIENTE",
        "test",
    )

    def init_falso(
        **kwargs,
    ):
        configuracao.update(
            kwargs
        )

    monkeypatch.setattr(
        sentry_sdk,
        "init",
        init_falso,
    )

    assert (
        configurar_monitoramento_erros()
        is True
    )
    assert (
        configuracao["environment"]
        == "test"
    )
    assert (
        configuracao["send_default_pii"]
        is False
    )
    assert (
        configuracao["traces_sample_rate"]
        == 0.0
    )
    assert callable(
        configuracao["before_send"]
    )
    assert len(
        configuracao["integrations"]
    ) == 1


def test_filtro_remove_dados_sensiveis_da_requisicao():
    evento = {
        "request": {
            "url": (
                "https://exemplo.test/"
                "redefinir?token=segredo"
            ),
            "method": "POST",
            "query_string": "token=segredo",
            "headers": {
                "Authorization": (
                    "Bearer segredo"
                )
            },
            "cookies": {
                "sessao": "segredo"
            },
            "data": {
                "senha": "segredo"
            },
            "env": {
                "REMOTE_ADDR": "127.0.0.1"
            },
        },
        "user": {
            "email": "pessoa@example.com"
        },
    }

    resultado = filtrar_evento_sensivel(
        evento,
        {},
    )

    request = resultado["request"]

    assert request == {
        "url": (
            "https://exemplo.test/"
            "redefinir"
        ),
        "method": "POST",
    }
    assert "user" not in resultado
    assert "segredo" not in repr(
        resultado
    )


def test_filtro_preserva_evento_sem_request():
    evento = {
        "message": "falha interna",
        "tags": {
            "request_id": "abc-123"
        },
    }

    resultado = filtrar_evento_sensivel(
        evento,
        {},
    )

    assert resultado == evento


def test_request_id_nao_e_associado_sem_sentry(
    monkeypatch,
):
    monkeypatch.setattr(
        sentry_sdk,
        "is_initialized",
        lambda: False,
    )

    assert (
        associar_request_id(
            "request-123"
        )
        is False
    )


def test_request_id_vira_tag_do_sentry(
    monkeypatch,
):
    tags = {}

    class ScopeFalso:
        def set_tag(
            self,
            chave,
            valor,
        ):
            tags[chave] = valor

    monkeypatch.setattr(
        sentry_sdk,
        "is_initialized",
        lambda: True,
    )
    monkeypatch.setattr(
        sentry_sdk,
        "get_isolation_scope",
        lambda: ScopeFalso(),
    )

    assert (
        associar_request_id(
            "request-456"
        )
        is True
    )
    assert tags == {
        "request_id": "request-456"
    }
