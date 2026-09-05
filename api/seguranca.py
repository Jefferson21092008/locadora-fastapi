from datetime import (
    datetime,
    timedelta,
    timezone,
)

import jwt


ALGORITMO = "HS256"
EXPIRACAO_MINUTOS = 30


def criar_token_acesso(
    usuario,
    secret,
):
    if not secret:
        raise RuntimeError(
            "LOCADORA_JWT_SECRET "
            "não foi configurada."
        )

    agora = datetime.now(
        timezone.utc
    )

    payload = {
        "sub": str(usuario.id),
        "role": usuario.role.value,
        "iat": agora,
        "exp": (
            agora
            + timedelta(
                minutes=EXPIRACAO_MINUTOS
            )
        ),
    }

    return jwt.encode(
        payload,
        secret,
        algorithm=ALGORITMO,
    )


def decodificar_token(
    token,
    secret,
):
    if not secret:
        return None

    try:
        return jwt.decode(
            token,
            secret,
            algorithms=[ALGORITMO],
        )

    except jwt.PyJWTError:
        return None