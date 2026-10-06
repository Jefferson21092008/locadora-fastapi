from collections import Counter

import pytest

from scripts.horizontal.check_replicas import (
    alvo_local,
    coletar_instancias,
    formatar_contagem,
    validar_alvo,
)


class RespostaFake:
    def __init__(self, instancia):
        self.headers = {
            "X-Locadora-Instance": instancia,
        }

    def raise_for_status(self):
        return None


class ClienteFake:
    def __init__(self, instancias):
        self.instancias = iter(instancias)

    def get(self, *_args, **_kwargs):
        return RespostaFake(next(self.instancias))


def test_alvo_local_e_permitido_sem_flag():
    assert alvo_local("http://127.0.0.1:8000") is True
    validar_alvo("http://localhost:8000")


def test_alvo_remoto_e_bloqueado_por_padrao():
    with pytest.raises(RuntimeError, match="alvos remotos"):
        validar_alvo("https://example.com")


def test_coleta_e_resume_replicas():
    cliente = ClienteFake([
        "api-a",
        "api-b",
        "api-a",
        "api-b",
    ])

    resultado = coletar_instancias(
        cliente,
        "http://127.0.0.1:8000",
        4,
    )

    assert resultado == Counter({
        "api-a": 2,
        "api-b": 2,
    })
    assert formatar_contagem(resultado) == "api-a=2, api-b=2"
