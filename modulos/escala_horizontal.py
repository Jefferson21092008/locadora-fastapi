import hashlib
import os
import re
import socket

from functools import lru_cache


TRUE_VALUES = {
    "1",
    "true",
    "yes",
    "on",
    "sim",
}

IDENTIFICADOR_RE = re.compile(
    r"^[A-Za-z0-9._-]{1,64}$"
)

HEADER_INSTANCIA = "X-Locadora-Instance"


def _env_bool(nome, padrao=False):
    valor = os.getenv(nome)
    if valor is None:
        return padrao

    return valor.strip().lower() in TRUE_VALUES


def escala_horizontal_habilitada():
    return _env_bool(
        "LOCADORA_ESCALA_HORIZONTAL_ENABLED",
        False,
    )


def workers_embutidos_habilitados():
    return _env_bool(
        "LOCADORA_WORKERS_EMBUTIDOS",
        not escala_horizontal_habilitada(),
    )


@lru_cache(maxsize=1)
def identificador_instancia():
    explicito = (
        os.getenv("LOCADORA_INSTANCIA_ID")
        or ""
    ).strip()

    if explicito:
        if not IDENTIFICADOR_RE.fullmatch(explicito):
            raise RuntimeError(
                "LOCADORA_INSTANCIA_ID deve conter apenas letras, "
                "números, ponto, hífen ou underscore e ter até 64 caracteres."
            )
        return explicito

    hostname = socket.gethostname().strip() or "locadora"
    digest = hashlib.sha256(
        hostname.encode("utf-8")
    ).hexdigest()[:12]
    return f"api-{digest}"
