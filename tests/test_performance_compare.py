import pytest

from scripts.performance.compare_results import (
    resumir_comparacao,
    validar_comparabilidade,
    variacao_percentual,
)


def resultado(
    *,
    cenario="veiculos",
    throughput=20.0,
    p95=500.0,
):
    return {
        "configuracao": {
            "cenario": cenario,
            "usuarios": 10,
            "requisicoes_por_usuario": 30,
            "aquecimento": 5,
        },
        "resultado": {
            "throughput_rps": throughput,
            "media_ms": 200.0,
            "mediana_ms": 180.0,
            "p95_ms": p95,
            "p99_ms": 700.0,
            "maximo_ms": 900.0,
            "taxa_sucesso": 100.0,
        },
    }


def test_variacao_percentual():
    assert variacao_percentual(20, 25) == 25.0
    assert variacao_percentual(100, 80) == -20.0
    assert variacao_percentual(0, 10) == 0.0


def test_comparacao_mostra_ganho_de_throughput_e_p95():
    linhas = resumir_comparacao(
        resultado(),
        resultado(
            throughput=25.0,
            p95=400.0,
        ),
    )

    assert "(+25.00%)" in linhas[0]
    assert any(
        "p95_ms" in linha
        and "(-20.00%)" in linha
        for linha in linhas
    )


def test_comparacao_recusa_cenarios_diferentes():
    with pytest.raises(
        RuntimeError,
        match="configurações diferentes",
    ):
        validar_comparabilidade(
            resultado(cenario="health"),
            resultado(cenario="veiculos"),
        )
