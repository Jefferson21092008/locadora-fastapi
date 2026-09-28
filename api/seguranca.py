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
    sessao_id=None,
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

    if sessao_id is not None:
        payload["sid"] = str(
            sessao_id
        )

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
            options={
                "require": [
                    "sub",
                    "iat",
                    "exp",
                ]
            },
        )

    except jwt.PyJWTError:
        return None
