from datetime import (
    datetime,
    timedelta,
    timezone,
)

import jwt

from api.seguranca import (
    ALGORITMO,
    decodificar_token,
)


SECRET = (
    "segredo-de-teste-para-hardening-jwt"
)


def test_decodificacao_exige_claims_basicas():
    agora = datetime.now(
        timezone.utc
    )

    token_sem_exp = jwt.encode(
        {
            "sub": "1",
            "iat": agora,
        },
        SECRET,
        algorithm=ALGORITMO,
    )

    assert (
        decodificar_token(
            token_sem_exp,
            SECRET,
        )
        is None
    )


def test_decodificacao_aceita_token_com_claims_obrigatorias():
    agora = datetime.now(
        timezone.utc
    )

    token = jwt.encode(
        {
            "sub": "1",
            "iat": agora,
            "exp": (
                agora
                + timedelta(
                    minutes=5
                )
            ),
        },
        SECRET,
        algorithm=ALGORITMO,
    )

    payload = decodificar_token(
        token,
        SECRET,
    )

    assert payload is not None
    assert payload["sub"] == "1"
