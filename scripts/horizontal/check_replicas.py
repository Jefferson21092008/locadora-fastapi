import argparse
import os
from collections import Counter
from urllib.parse import urlparse

import httpx


HEADER_INSTANCIA = "X-Locadora-Instance"


def alvo_local(url):
    host = (urlparse(url).hostname or "").lower()
    return host in {
        "127.0.0.1",
        "localhost",
        "::1",
    }


def validar_alvo(url, allow_remote=False):
    if allow_remote or alvo_local(url):
        return

    raise RuntimeError(
        "O verificador bloqueia alvos remotos por padrão. "
        "Use --allow-remote somente de forma consciente."
    )


def coletar_instancias(client, url, quantidade, path="/ready", headers=None):
    contagem = Counter()

    for _ in range(max(int(quantidade), 1)):
        resposta = client.get(
            f"{url.rstrip('/')}{path}",
            headers=headers,
        )
        resposta.raise_for_status()
        instancia = resposta.headers.get(
            HEADER_INSTANCIA,
            "",
        ).strip()
        if not instancia:
            raise RuntimeError(
                f"Resposta sem o header {HEADER_INSTANCIA}."
            )
        contagem[instancia] += 1

    return contagem


def autenticar(client, url):
    usuario = os.getenv("LOCADORA_SCALE_USUARIO")
    senha = os.getenv("LOCADORA_SCALE_SENHA")

    if not usuario or not senha:
        raise RuntimeError(
            "Defina LOCADORA_SCALE_USUARIO e LOCADORA_SCALE_SENHA "
            "para executar --verificar-auth."
        )

    resposta = client.post(
        f"{url.rstrip('/')}/api/v1/auth/login",
        json={
            "usuario": usuario,
            "senha": senha,
        },
    )
    resposta.raise_for_status()
    token = resposta.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
    }


def formatar_contagem(contagem):
    return ", ".join(
        f"{instancia}={total}"
        for instancia, total in sorted(contagem.items())
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Valida se o gateway distribui requisições entre "
            "múltiplas réplicas da API."
        )
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--min-instances",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--verificar-auth",
        action="store_true",
        help=(
            "Faz login e valida a mesma sessão em requisições "
            "que podem cair em réplicas diferentes."
        ),
    )
    parser.add_argument(
        "--allow-remote",
        action="store_true",
    )
    args = parser.parse_args()

    validar_alvo(
        args.url,
        allow_remote=args.allow_remote,
    )

    with httpx.Client(timeout=10.0) as client:
        readiness = coletar_instancias(
            client,
            args.url,
            args.requests,
        )
        print(
            "Réplicas observadas no /ready: "
            + formatar_contagem(readiness)
        )

        if len(readiness) < max(args.min_instances, 1):
            raise SystemExit(
                "Falha: o gateway não demonstrou o número mínimo "
                "de réplicas esperado."
            )

        if args.verificar_auth:
            headers = autenticar(client, args.url)
            autenticadas = coletar_instancias(
                client,
                args.url,
                args.requests,
                path="/api/v1/auth/me",
                headers=headers,
            )
            print(
                "Réplicas observadas com sessão autenticada: "
                + formatar_contagem(autenticadas)
            )

            if len(autenticadas) < max(args.min_instances, 1):
                raise SystemExit(
                    "Falha: a sessão não foi validada através do "
                    "número mínimo de réplicas esperado."
                )

    print("Escala horizontal validada com sucesso.")


if __name__ == "__main__":
    main()
