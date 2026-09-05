import smtplib

from email.message import (
    EmailMessage,
)


class EmailService:
    """
    Responsável pelo envio de e-mails
    da aplicação.
    """

    def __init__(
        self,
        config,
    ):
        self.config = config

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

        mensagem = EmailMessage()

        mensagem["Subject"] = (
            "Recuperação de senha - Locadora"
        )

        mensagem["From"] = (
            self.config.email_remetente
        )

        mensagem["To"] = (
            destinatario
        )

        mensagem.set_content(
            (
                "Foi solicitada uma recuperação "
                "de senha para sua conta.\n\n"
                "Use o token abaixo para criar "
                "uma nova senha:\n\n"
                f"{token}\n\n"
                "Esse token é válido por 15 minutos "
                "e só pode ser utilizado uma vez.\n\n"
                "Se você não solicitou a recuperação, "
                "ignore esta mensagem."
            )
        )

        with smtplib.SMTP(
            self.config.email_smtp_host,
            self.config.email_smtp_port,
            timeout=15,
        ) as servidor:
            servidor.ehlo()

            servidor.starttls()

            servidor.ehlo()

            servidor.login(
                self.config.email_usuario,
                self.config.email_senha,
            )

            servidor.send_message(
                mensagem
            )
