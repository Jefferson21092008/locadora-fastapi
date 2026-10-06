"""Teste de carga leve e reproduzível para a API da Locadora.

A ferramenta foi pensada para baseline local/staging controlado. Por segurança,
recusa destinos remotos por padrão. Use ``--allow-remote`` somente em ambiente
que você controla e nunca contra produção sem autorização explícita.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from urllib.parse import urlparse

import httpx


CENARIOS = {
    "health": (
        ("GET", "/health"),
    ),
    "veiculos": (
        (
            "GET",
            "/api/v1/veiculos/consulta?pagina=1&por_pagina=12",
        ),
    ),
    "dashboard-cache": (
        ("GET", "/api/v1/relatorios/dashboard"),
    ),
    "dashboard-db": (
        (
            "GET",
            "/api/v1/relatorios/dashboard?atualizar=true",
        ),
    ),
    "misto": (
        ("GET", "/health"),
        (
            "GET",
            "/api/v1/veiculos/consulta?pagina=1&por_pagina=12",
        ),
        ("GET", "/api/v1/relatorios/dashboard"),
    ),
}

CENARIOS_AUTENTICADOS = {
    "dashboard-cache",
    "dashboard-db",
    "misto",
}


@dataclass(frozen=True)
class ResultadoRequisicao:
    duracao_ms: float
    status_code: int | None
    sucesso: bool
    erro: str | None = None


@dataclass(frozen=True)
class ResumoCarga:
    requisicoes: int
    sucessos: int
    falhas: int
    taxa_sucesso: float
    duracao_total_s: float
    throughput_rps: float
    media_ms: float
    mediana_ms: float
    p95_ms: float
    p99_ms: float
    minimo_ms: float
    maximo_ms: float
    status_codes: dict[str, int]


def url_eh_local(base_url: str) -> bool:
    hostname = (
        urlparse(base_url).hostname
        or ""
    ).strip().lower()
    return hostname in {
        "localhost",
        "127.0.0.1",
        "::1",
    }


def percentil(valores: list[float], percentual: float) -> float:
    if not valores:
        return 0.0

    ordenados = sorted(valores)
    posicao = max(
        0,
        min(
            len(ordenados) - 1,
            int(
                round(
                    (len(ordenados) - 1)
                    * percentual
                )
            ),
        ),
    )
    return float(ordenados[posicao])


def resumir_resultados(
    resultados: list[ResultadoRequisicao],
    duracao_total_s: float,
) -> ResumoCarga:
    duracoes = [
        item.duracao_ms
        for item in resultados
    ]
    sucessos = sum(
        1
        for item in resultados
        if item.sucesso
    )
    total = len(resultados)
    falhas = total - sucessos
    status = Counter(
        str(item.status_code)
        if item.status_code is not None
        else "erro"
        for item in resultados
    )

    return ResumoCarga(
        requisicoes=total,
        sucessos=sucessos,
        falhas=falhas,
        taxa_sucesso=(
            round(sucessos / total * 100, 2)
            if total
            else 0.0
        ),
        duracao_total_s=round(
            duracao_total_s,
            3,
        ),
        throughput_rps=(
            round(total / duracao_total_s, 2)
            if duracao_total_s > 0
            else 0.0
        ),
        media_ms=(
            round(statistics.fmean(duracoes), 2)
            if duracoes
            else 0.0
        ),
        mediana_ms=(
            round(statistics.median(duracoes), 2)
            if duracoes
            else 0.0
        ),
        p95_ms=round(
            percentil(duracoes, 0.95),
            2,
        ),
        p99_ms=round(
            percentil(duracoes, 0.99),
            2,
        ),
        minimo_ms=(
            round(min(duracoes), 2)
            if duracoes
            else 0.0
        ),
        maximo_ms=(
            round(max(duracoes), 2)
            if duracoes
            else 0.0
        ),
        status_codes=dict(
            sorted(status.items())
        ),
    )


def _credenciais() -> tuple[str, str]:
    usuario = os.getenv(
        "LOCADORA_LOAD_USUARIO",
        "",
    ).strip()
    senha = os.getenv(
        "LOCADORA_LOAD_SENHA",
        "",
    )

    if not usuario or not senha:
        raise RuntimeError(
            "Cenário autenticado exige "
            "LOCADORA_LOAD_USUARIO e LOCADORA_LOAD_SENHA."
        )

    return usuario, senha


async def obter_token(
    client: httpx.AsyncClient,
) -> str:
    usuario, senha = _credenciais()
    resposta = await client.post(
        "/api/v1/auth/login",
        json={
            "usuario": usuario,
            "senha": senha,
        },
    )
    resposta.raise_for_status()
    token = str(
        resposta.json().get(
            "access_token",
            "",
        )
    ).strip()

    if not token:
        raise RuntimeError(
            "Login não retornou access_token."
        )

    return token


async def executar_requisicao(
    client: httpx.AsyncClient,
    metodo: str,
    caminho: str,
    headers: dict[str, str],
) -> ResultadoRequisicao:
    inicio = perf_counter()
    try:
        resposta = await client.request(
            metodo,
            caminho,
            headers=headers,
        )
        duracao_ms = (
            perf_counter() - inicio
        ) * 1000
        return ResultadoRequisicao(
            duracao_ms=duracao_ms,
            status_code=(
                resposta.status_code
            ),
            sucesso=(
                200
                <= resposta.status_code
                < 400
            ),
        )
    except httpx.HTTPError as erro:
        duracao_ms = (
            perf_counter() - inicio
        ) * 1000
        return ResultadoRequisicao(
            duracao_ms=duracao_ms,
            status_code=None,
            sucesso=False,
            erro=type(erro).__name__,
        )


async def executar_carga(
    *,
    base_url: str,
    cenario: str,
    usuarios: int,
    requisicoes_por_usuario: int,
    timeout_s: float,
    aquecimento: int,
) -> tuple[ResumoCarga, list[ResultadoRequisicao]]:
    rotas = CENARIOS[cenario]
    limites = httpx.Limits(
        max_connections=max(
            usuarios,
            1,
        ),
        max_keepalive_connections=max(
            usuarios,
            1,
        ),
    )

    async with httpx.AsyncClient(
        base_url=base_url.rstrip("/"),
        timeout=timeout_s,
        limits=limites,
        follow_redirects=False,
    ) as client:
        headers: dict[str, str] = {}
        if cenario in CENARIOS_AUTENTICADOS:
            token = await obter_token(client)
            headers["Authorization"] = (
                f"Bearer {token}"
            )

        for indice in range(aquecimento):
            metodo, caminho = rotas[
                indice % len(rotas)
            ]
            await executar_requisicao(
                client,
                metodo,
                caminho,
                headers,
            )

        resultados: list[ResultadoRequisicao] = []
        lock = asyncio.Lock()

        async def usuario_virtual(
            numero: int,
        ) -> None:
            locais = []
            for indice in range(
                requisicoes_por_usuario
            ):
                metodo, caminho = rotas[
                    (
                        numero
                        + indice
                    )
                    % len(rotas)
                ]
                locais.append(
                    await executar_requisicao(
                        client,
                        metodo,
                        caminho,
                        headers,
                    )
                )

            async with lock:
                resultados.extend(locais)

        inicio = perf_counter()
        await asyncio.gather(
            *(
                usuario_virtual(numero)
                for numero in range(usuarios)
            )
        )
        duracao_total_s = (
            perf_counter() - inicio
        )

    return (
        resumir_resultados(
            resultados,
            duracao_total_s,
        ),
        resultados,
    )


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Executa uma carga controlada contra a API da Locadora."
        )
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
    )
    parser.add_argument(
        "--cenario",
        choices=sorted(CENARIOS),
        default="health",
    )
    parser.add_argument(
        "--usuarios",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--requisicoes-por-usuario",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
    )
    parser.add_argument(
        "--aquecimento",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--output",
        type=Path,
    )
    parser.add_argument(
        "--min-success-rate",
        type=float,
    )
    parser.add_argument(
        "--max-p95-ms",
        type=float,
    )
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help=(
            "Permite alvo não local. Use apenas em staging controlado."
        ),
    )
    return parser


def validar_argumentos(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    if args.usuarios < 1:
        parser.error(
            "--usuarios deve ser >= 1"
        )
    if args.requisicoes_por_usuario < 1:
        parser.error(
            "--requisicoes-por-usuario deve ser >= 1"
        )
    if args.timeout <= 0:
        parser.error(
            "--timeout deve ser > 0"
        )
    if args.aquecimento < 0:
        parser.error(
            "--aquecimento deve ser >= 0"
        )
    if (
        not args.allow_remote
        and not url_eh_local(args.base_url)
    ):
        parser.error(
            "Destino remoto bloqueado por segurança. "
            "Use --allow-remote somente em staging controlado."
        )


def imprimir_resumo(
    resumo: ResumoCarga,
) -> None:
    print(
        f"Requisições: {resumo.requisicoes}"
    )
    print(
        f"Sucesso: {resumo.taxa_sucesso:.2f}% "
        f"({resumo.sucessos}/{resumo.requisicoes})"
    )
    print(
        f"Throughput: {resumo.throughput_rps:.2f} req/s"
    )
    print(
        "Latência (ms): "
        f"média={resumo.media_ms:.2f} "
        f"p50={resumo.mediana_ms:.2f} "
        f"p95={resumo.p95_ms:.2f} "
        f"p99={resumo.p99_ms:.2f} "
        f"máx={resumo.maximo_ms:.2f}"
    )
    print(
        f"Status: {resumo.status_codes}"
    )


def salvar_resultado(
    caminho: Path,
    *,
    args: argparse.Namespace,
    resumo: ResumoCarga,
) -> None:
    caminho.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    payload = {
        "gerado_em": datetime.now(
            timezone.utc
        ).isoformat(),
        "configuracao": {
            "base_url": args.base_url,
            "cenario": args.cenario,
            "usuarios": args.usuarios,
            "requisicoes_por_usuario": (
                args.requisicoes_por_usuario
            ),
            "aquecimento": args.aquecimento,
        },
        "resultado": asdict(resumo),
    }
    caminho.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def avaliar_limites(
    args: argparse.Namespace,
    resumo: ResumoCarga,
) -> list[str]:
    falhas = []
    if (
        args.min_success_rate is not None
        and resumo.taxa_sucesso
        < args.min_success_rate
    ):
        falhas.append(
            "taxa de sucesso "
            f"{resumo.taxa_sucesso:.2f}% "
            f"< {args.min_success_rate:.2f}%"
        )
    if (
        args.max_p95_ms is not None
        and resumo.p95_ms
        > args.max_p95_ms
    ):
        falhas.append(
            f"p95 {resumo.p95_ms:.2f} ms "
            f"> {args.max_p95_ms:.2f} ms"
        )
    return falhas


async def _main_async(
    args: argparse.Namespace,
) -> int:
    try:
        resumo, _ = await executar_carga(
            base_url=args.base_url,
            cenario=args.cenario,
            usuarios=args.usuarios,
            requisicoes_por_usuario=(
                args.requisicoes_por_usuario
            ),
            timeout_s=args.timeout,
            aquecimento=args.aquecimento,
        )
    except (
        httpx.HTTPError,
        RuntimeError,
    ) as erro:
        print(
            f"Erro: {erro}",
            file=sys.stderr,
        )
        return 2

    imprimir_resumo(resumo)

    if args.output:
        salvar_resultado(
            args.output,
            args=args,
            resumo=resumo,
        )
        print(
            f"Resultado salvo em: {args.output}"
        )

    falhas = avaliar_limites(
        args,
        resumo,
    )
    if falhas:
        for falha in falhas:
            print(
                f"LIMITE NÃO ATINGIDO: {falha}",
                file=sys.stderr,
            )
        return 3

    return 0


def main() -> int:
    parser = construir_parser()
    args = parser.parse_args()
    validar_argumentos(
        parser,
        args,
    )
    return asyncio.run(
        _main_async(args)
    )


if __name__ == "__main__":
    raise SystemExit(main())
