import os

from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DATABASE_PATH = (
    BASE_DIR
    / "dados"
    / "locadora.db"
)

DATABASE_URL_PADRAO = (
    f"sqlite:///{DATABASE_PATH.as_posix()}"
)


class Configuracao:
    """
    Centraliza configurações da aplicação
    vindas de variáveis de ambiente.
    """

    def __init__(self):
        # ============================================================
        # ADMIN
        # ============================================================

        self.admin_usuario = os.getenv(
            "LOCADORA_ADMIN_USUARIO",
            "admin",
        )

        self.admin_senha = os.getenv(
            "LOCADORA_ADMIN_SENHA"
        )

        # ============================================================
        # JWT
        # ============================================================

        self.jwt_secret = os.getenv(
            "LOCADORA_JWT_SECRET"
        )

        # ============================================================
        # BANCO DE DADOS
        # ============================================================

        self.database_url = (
            os.getenv(
                "LOCADORA_DATABASE_URL"
            )
            or DATABASE_URL_PADRAO
        )

        # ============================================================
        # E-MAIL / SMTP
        # ============================================================

        self.email_smtp_host = os.getenv(
            "LOCADORA_EMAIL_SMTP_HOST"
        )

        self.email_smtp_port = int(
            os.getenv(
                "LOCADORA_EMAIL_SMTP_PORT",
                "587",
            )
        )

        self.email_usuario = os.getenv(
            "LOCADORA_EMAIL_USUARIO"
        )

        self.email_senha = os.getenv(
            "LOCADORA_EMAIL_SENHA"
        )

        self.email_remetente = os.getenv(
            "LOCADORA_EMAIL_REMETENTE"
        ) or self.email_usuario

        # ============================================================
        # VALIDAÇÕES OBRIGATÓRIAS
        # ============================================================

        if not self.admin_senha:
            raise RuntimeError(
                "A variável "
                "LOCADORA_ADMIN_SENHA "
                "não foi configurada."
            )

        if not self.jwt_secret:
            raise RuntimeError(
                "A variável "
                "LOCADORA_JWT_SECRET "
                "não foi configurada."
            )

    # ================================================================
    # E-MAIL
    # ================================================================

    @property
    def email_configurado(
        self,
    ):
        return all(
            (
                self.email_smtp_host,
                self.email_smtp_port,
                self.email_usuario,
                self.email_senha,
                self.email_remetente,
            )
        )
