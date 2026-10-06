import asyncio
import json

from api.erros import tratar_conflito_concorrencia
from modulos.excecoes import (
    ConflitoConcorrencia,
    RegraDeNegocio,
)


def test_conflito_concorrencia_e_regra_de_negocio():
    erro = ConflitoConcorrencia(
        "Estado alterado por outra requisição."
    )

    assert isinstance(
        erro,
        RegraDeNegocio,
    )
    assert erro.mensagem == (
        "Estado alterado por outra requisição."
    )


def test_handler_concorrencia_retorna_http_409():
    resposta = asyncio.run(
        tratar_conflito_concorrencia(
            None,
            ConflitoConcorrencia(
                "Conflito concorrente."
            ),
        )
    )

    assert resposta.status_code == 409
    assert json.loads(
        resposta.body.decode("utf-8")
    ) == {
        "detail": "Conflito concorrente."
    }
