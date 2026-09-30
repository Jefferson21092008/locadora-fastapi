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


def _env_bool(nome, padrao=False):
    valor = os.getenv(nome)
    if valor is None:
        return padrao

    return valor.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "sim",
    }


def _env_int(nome, padrao, minimo=1):
    valor = os.getenv(nome)
    if valor is None:
        return padrao

    try:
        convertido = int(valor)
    except ValueError:
        return padrao

    return max(convertido, minimo)


def normalizar_database_url(
    database_url,
):
    """
    Adapta URLs PostgreSQL comuns para o driver
    psycopg 3 usado pelo projeto.

    Provedores como o Neon normalmente entregam
    a conexão como ``postgresql://...``. O SQLAlchemy
    precisa de ``postgresql+psycopg://...`` para usar
    o pacote ``psycopg`` instalado em requirements.txt.
    """
    database_url = str(
        database_url
    ).strip()

    if database_url.startswith(
        "postgres://"
    ):
        return (
            "postgresql+psycopg://"
            + database_url[len("postgres://") :]
        )

    if database_url.startswith(
        "postgresql://"
    ):
        return (
            "postgresql+psycopg://"
            + database_url[len("postgresql://") :]
        )

    return database_url


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
            normalizar_database_url(
                os.getenv(
                    "LOCADORA_DATABASE_URL"
                )
                or DATABASE_URL_PADRAO
            )
        )

        # ============================================================
        # E-MAIL / BREVO
        # ============================================================

        self.brevo_api_key = os.getenv(
            "LOCADORA_BREVO_API_KEY"
        )

        self.email_remetente = os.getenv(
            "LOCADORA_EMAIL_REMETENTE"
        )

        self.public_url = (
            os.getenv(
                "LOCADORA_PUBLIC_URL"
            )
            or "http://127.0.0.1:8000"
        ).strip().rstrip("/")

        # ============================================================
        # BACKGROUND JOBS
        # ============================================================

        self.background_jobs_enabled = _env_bool(
            "LOCADORA_BACKGROUND_JOBS_ENABLED",
            False,
        )

        self.background_jobs_intervalo_segundos = _env_int(
            "LOCADORA_BACKGROUND_JOBS_INTERVALO_SEGUNDOS",
            60,
            minimo=5,
        )

        self.background_jobs_lote = _env_int(
            "LOCADORA_BACKGROUND_JOBS_LOTE",
            50,
            minimo=1,
        )

        self.background_jobs_timeout_bloqueio_segundos = _env_int(
            "LOCADORA_BACKGROUND_JOBS_TIMEOUT_BLOQUEIO_SEGUNDOS",
            900,
            minimo=30,
        )

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
                self.brevo_api_key,
                self.email_remetente,
                self.public_url,
            )
        )
