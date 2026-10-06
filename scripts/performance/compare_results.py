"""Compara duas execuções produzidas por scripts.performance.load_test."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


METRICAS_MENORES_MELHORES = (
    "media_ms",
    "mediana_ms",
    "p95_ms",
    "p99_ms",
    "maximo_ms",
)


def carregar_resultado(caminho: Path) -> dict:
    try:
        return json.loads(
            caminho.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as erro:
        raise RuntimeError(
            f"Não foi possível ler {caminho}: {erro}"
        ) from erro


def validar_comparabilidade(
    baseline: dict,
    atual: dict,
) -> None:
    campos = (
        "cenario",
        "usuarios",
        "requisicoes_por_usuario",
        "aquecimento",
    )
    config_base = baseline.get("configuracao", {})
    config_atual = atual.get("configuracao", {})

    diferentes = [
        campo
        for campo in campos
        if config_base.get(campo) != config_atual.get(campo)
    ]
    if diferentes:
        raise RuntimeError(
            "Resultados não são diretamente comparáveis; "
            "configurações diferentes em: "
            + ", ".join(diferentes)
        )


def variacao_percentual(
    anterior: float,
    atual: float,
) -> float:
    if anterior == 0:
        return 0.0
    return (atual - anterior) / anterior * 100


def resumir_comparacao(
    baseline: dict,
    atual: dict,
) -> list[str]:
    validar_comparabilidade(
        baseline,
        atual,
    )
    base = baseline["resultado"]
    novo = atual["resultado"]

    linhas = []
    throughput = variacao_percentual(
        float(base["throughput_rps"]),
        float(novo["throughput_rps"]),
    )
    linhas.append(
        "throughput: "
        f"{base['throughput_rps']:.2f} -> "
        f"{novo['throughput_rps']:.2f} req/s "
        f"({throughput:+.2f}%)"
    )

    for metrica in METRICAS_MENORES_MELHORES:
        variacao = variacao_percentual(
            float(base[metrica]),
            float(novo[metrica]),
        )
        linhas.append(
            f"{metrica}: "
            f"{base[metrica]:.2f} -> "
            f"{novo[metrica]:.2f} ms "
            f"({variacao:+.2f}%)"
        )

    linhas.append(
        "sucesso: "
        f"{base['taxa_sucesso']:.2f}% -> "
        f"{novo['taxa_sucesso']:.2f}%"
    )
    return linhas


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compara baseline e resultado pós-otimização "
            "com a mesma configuração de carga."
        )
    )
    parser.add_argument("baseline", type=Path)
    parser.add_argument("atual", type=Path)
    return parser


def main() -> int:
    parser = construir_parser()
    args = parser.parse_args()
    try:
        baseline = carregar_resultado(args.baseline)
        atual = carregar_resultado(args.atual)
        linhas = resumir_comparacao(
            baseline,
            atual,
        )
    except (RuntimeError, KeyError, TypeError, ValueError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2

    for linha in linhas:
        print(linha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
