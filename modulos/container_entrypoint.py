import os
import subprocess
import sys


VALORES_TRUE = {"1", "true", "yes", "on"}
VALORES_FALSE = {"0", "false", "no", "off"}


def ler_booleano_ambiente(nome, padrao):
    valor = os.environ.get(nome)
    if valor is None:
        return padrao

    normalizado = valor.strip().lower()
    if normalizado in VALORES_TRUE:
        return True
    if normalizado in VALORES_FALSE:
        return False

    raise RuntimeError(
        f"{nome} deve ser true/false, 1/0, yes/no ou on/off."
    )


def obter_porta():
    valor = os.environ.get("PORT", "10000").strip()

    try:
        porta = int(valor)
    except ValueError as exc:
        raise RuntimeError("PORT deve ser um número inteiro.") from exc

    if not 1 <= porta <= 65535:
        raise RuntimeError("PORT deve estar entre 1 e 65535.")

    return porta


def executar_migrations():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "upgrade",
            "head",
        ],
        check=True,
    )


def comando_uvicorn(porta):
    return [
        sys.executable,
        "-m",
        "uvicorn",
        "api.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(porta),
        "--no-server-header",
    ]


def main():
    if ler_booleano_ambiente(
        "LOCADORA_EXECUTAR_MIGRATIONS",
        True,
    ):
        executar_migrations()

    comando = comando_uvicorn(obter_porta())
    os.execv(sys.executable, comando)


if __name__ == "__main__":
    main()
