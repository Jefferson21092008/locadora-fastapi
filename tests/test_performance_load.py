from argparse import Namespace

from scripts.performance.load_test import (
    ResultadoRequisicao,
    avaliar_limites,
    percentil,
    resumir_resultados,
    url_eh_local,
)


def test_url_local_eh_permitida():
    assert url_eh_local(
        "http://127.0.0.1:8000"
    )
    assert url_eh_local(
        "http://localhost:8000"
    )
    assert not url_eh_local(
        "https://locadora.example.com"
    )


def test_percentis_com_amostra_ordenada():
    valores = [10, 20, 30, 40, 50]

    assert percentil(
        valores,
        0.50,
    ) == 30
    assert percentil(
        valores,
        0.95,
    ) == 50


def test_resumo_calcula_metricas_e_status():
    resultados = [
        ResultadoRequisicao(
            duracao_ms=10,
            status_code=200,
            sucesso=True,
        ),
        ResultadoRequisicao(
            duracao_ms=20,
            status_code=200,
            sucesso=True,
        ),
        ResultadoRequisicao(
            duracao_ms=30,
            status_code=500,
            sucesso=False,
        ),
        ResultadoRequisicao(
            duracao_ms=40,
            status_code=None,
            sucesso=False,
            erro="ReadTimeout",
        ),
    ]

    resumo = resumir_resultados(
        resultados,
        duracao_total_s=2,
    )

    assert resumo.requisicoes == 4
    assert resumo.sucessos == 2
    assert resumo.falhas == 2
    assert resumo.taxa_sucesso == 50.0
    assert resumo.throughput_rps == 2.0
    assert resumo.media_ms == 25.0
    assert resumo.status_codes == {
        "200": 2,
        "500": 1,
        "erro": 1,
    }


def test_limites_sinalizam_regressao():
    resumo = resumir_resultados(
        [
            ResultadoRequisicao(
                duracao_ms=900,
                status_code=200,
                sucesso=True,
            ),
            ResultadoRequisicao(
                duracao_ms=1200,
                status_code=500,
                sucesso=False,
            ),
        ],
        duracao_total_s=1,
    )
    args = Namespace(
        min_success_rate=99.0,
        max_p95_ms=1000.0,
    )

    falhas = avaliar_limites(
        args,
        resumo,
    )

    assert len(falhas) == 2
