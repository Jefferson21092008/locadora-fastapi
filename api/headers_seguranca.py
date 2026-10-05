import os

from modulos.config import ambiente_atual


ENV_PUBLIC_URL = "LOCADORA_PUBLIC_URL"

CSP_FRONTEND = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'; "
    "form-action 'self'"
)


def _producao_https():
    ambiente = ambiente_atual()

    public_url = (
        os.getenv(
            ENV_PUBLIC_URL,
            "",
        )
        or ""
    ).strip().lower()

    return (
        ambiente == "production"
        and public_url.startswith(
            "https://"
        )
    )


def _rota_auth(caminho):
    return (
        caminho == "/auth"
        or caminho.startswith(
            "/auth/"
        )
        or caminho == "/api/v1/auth"
        or caminho.startswith(
            "/api/v1/auth/"
        )
    )


async def middleware_headers_seguranca(
    request,
    call_next,
):
    """
    Adiciona headers HTTP de hardening sem alterar o contrato da API.

    A CSP é aplicada apenas ao frontend próprio. A documentação Swagger
    permanece fora dela porque o FastAPI utiliza assets externos por padrão.
    """
    response = await call_next(
        request
    )

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"
    response.headers[
        "X-Frame-Options"
    ] = "DENY"
    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"
    response.headers[
        "Permissions-Policy"
    ] = (
        "geolocation=(), "
        "camera=(), "
        "microphone=()"
    )
    response.headers[
        "Cross-Origin-Opener-Policy"
    ] = "same-origin"

    caminho = request.url.path

    if caminho.startswith(
        "/app"
    ):
        response.headers[
            "Content-Security-Policy"
        ] = CSP_FRONTEND

    if _rota_auth(caminho):
        response.headers[
            "Cache-Control"
        ] = "no-store"
        response.headers[
            "Pragma"
        ] = "no-cache"

    if caminho == (
        "/app/redefinir-senha.html"
    ):
        response.headers[
            "Cache-Control"
        ] = "no-store"
        response.headers[
            "Referrer-Policy"
        ] = "no-referrer"

    if _producao_https():
        response.headers[
            "Strict-Transport-Security"
        ] = "max-age=31536000"

    return response
