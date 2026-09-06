from html import escape
from urllib.parse import urlencode

import httpx


class EmailService:
    """
    Responsável pelo envio de e-mails
    transacionais da aplicação via Brevo.
    """

    BREVO_URL = (
        "https://api.brevo.com/v3/smtp/email"
    )

    def __init__(
        self,
        config,
    ):
        self.config = config

    def _criar_url_redefinicao(
        self,
        token,
    ):
        query = urlencode(
            {
                "token": str(token),
            }
        )

        return (
            f"{self.config.public_url}"
            "/app/redefinir-senha.html"
            f"?{query}"
        )

    def enviar_recuperacao_senha(
        self,
        destinatario,
        token,
    ):
        if not getattr(
            self.config,
            "email_configurado",
            False,
        ):
            raise RuntimeError(
                "O envio de e-mail "
                "não foi configurado."
            )

        url_redefinicao = (
            self._criar_url_redefinicao(
                token
            )
        )

        url_html = escape(
            url_redefinicao,
            quote=True,
        )

        payload = {
            "sender": {
                "name": "Locadora FastAPI",
                "email": (
                    self.config
                    .email_remetente
                ),
            },
            "to": [
                {
                    "email": destinatario,
                }
            ],
            "subject": (
                "Recuperação de senha "
                "- Locadora"
            ),
            "htmlContent": (
                "<html>"
                "<body>"
                "<h2>Recuperação de senha</h2>"
                "<p>Foi solicitada uma "
                "recuperação de senha para "
                "sua conta.</p>"
                "<p>"
                f'<a href="{url_html}">'
                "Redefinir minha senha"
                "</a>"
                "</p>"
                "<p>Este link é válido por "
                "15 minutos e só pode ser "
                "utilizado uma vez.</p>"
                "<p>Se você não solicitou "
                "a recuperação, ignore esta "
                "mensagem.</p>"
                "</body>"
                "</html>"
            ),
        }

        headers = {
            "accept": "application/json",
            "api-key": (
                self.config
                .brevo_api_key
            ),
            "content-type": (
                "application/json"
            ),
        }

        resposta = httpx.post(
            self.BREVO_URL,
            headers=headers,
            json=payload,
            timeout=15.0,
        )

        resposta.raise_for_status()