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

AMBIENTE_PADRAO = "development"
AMBIENTES_VALIDOS = {
    "development",
    "test",
    "staging",
    "production",
}
AMBIENTES_ALIASES = {
    "dev": "development",
    "testing": "test",
    "stage": "staging",
    "prod": "production",
}


def normalizar_ambiente(valor):
    ambiente = str(
        valor or AMBIENTE_PADRAO
    ).strip().lower()

    ambiente = AMBIENTES_ALIASES.get(
        ambiente,
        ambiente,
    )

    if ambiente not in AMBIENTES_VALIDOS:
        opcoes = ", ".join(
            sorted(AMBIENTES_VALIDOS)
        )
        raise RuntimeError(
            "LOCADORA_AMBIENTE inválido. "
            f"Use um destes valores: {opcoes}."
        )

    return ambiente


def ambiente_atual():
    return normalizar_ambiente(
        os.getenv(
            "LOCADORA_AMBIENTE",
            AMBIENTE_PADRAO,
        )
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
        # AMBIENTE
        # ============================================================

        self.ambiente = ambiente_atual()

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

        database_url_env = os.getenv(
            "LOCADORA_DATABASE_URL"
        )

        self.database_url = (
            normalizar_database_url(
                database_url_env
                or DATABASE_URL_PADRAO
            )
        )

        # ============================================================
        # REDIS / CACHE
        # ============================================================

        redis_url = os.getenv(
            "LOCADORA_REDIS_URL"
        )

        self.redis_url = (
            redis_url.strip()
            if redis_url
            else None
        )

        redis_prefixo_padrao = (
            f"locadora:{self.ambiente}"
        )

        self.redis_prefixo = (
            os.getenv(
                "LOCADORA_REDIS_PREFIXO",
                redis_prefixo_padrao,
            )
            .strip()
            .strip(":")
            or redis_prefixo_padrao
        )

        self.redis_timeout_ms = _env_int(
            "LOCADORA_REDIS_TIMEOUT_MS",
            500,
            minimo=50,
        )

        self.cache_dashboard_ttl_segundos = _env_int(
            "LOCADORA_CACHE_DASHBOARD_TTL_SEGUNDOS",
            30,
            minimo=1,
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

        if self.ambiente in {
            "staging",
            "production",
        }:
            if not database_url_env:
                raise RuntimeError(
                    "LOCADORA_DATABASE_URL deve ser configurada "
                    f"explicitamente no ambiente {self.ambiente}."
                )

            if not self.database_url.startswith(
                "postgresql+psycopg://"
            ):
                raise RuntimeError(
                    "Staging e production devem usar PostgreSQL "
                    "em LOCADORA_DATABASE_URL."
                )

            if not self.public_url.lower().startswith(
                "https://"
            ):
                raise RuntimeError(
                    "LOCADORA_PUBLIC_URL deve usar HTTPS em "
                    f"{self.ambiente}."
                )


    # ================================================================
    # AMBIENTE
    # ================================================================

    @property
    def em_desenvolvimento(self):
        return self.ambiente == "development"

    @property
    def em_teste(self):
        return self.ambiente == "test"

    @property
    def em_staging(self):
        return self.ambiente == "staging"

    @property
    def em_producao(self):
        return self.ambiente == "production"

    # ================================================================
    # REDIS / CACHE
    # ================================================================

    @property
    def redis_configurado(
        self,
    ):
        return bool(
            self.redis_url
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
