import os

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import Request

from modulos.redis_client import (
    RedisError,
    criar_cliente_redis,
)


def obter_ip_cliente(
    request: Request,
) -> str:
    forwarded_for = request.headers.get(
        "x-forwarded-for"
    )

    if forwarded_for:
        return (
            forwarded_for
            .split(",", 1)[0]
            .strip()
        )

    if request.client:
        return request.client.host

    return "desconhecido"


class RateLimiter:
    """
    Rate limiter com backend Redis opcional e fallback local.

    Quando Redis/Valkey está configurado, os contadores são compartilhados
    entre instâncias da API. Se o datastore ficar indisponível, a aplicação
    preserva a proteção local em memória em vez de indisponibilizar o login.
    """

    def __init__(
        self,
        redis_url=None,
        redis_prefixo="locadora",
        redis_timeout_ms=500,
        redis_client=None,
    ):
        self._tentativas = defaultdict(deque)
        self._lock = Lock()
        self._redis_prefixo = (
            str(redis_prefixo or "locadora")
            .strip()
            .strip(":")
            or "locadora"
        )
        self._redis = (
            redis_client
            if redis_client is not None
            else criar_cliente_redis(
                redis_url,
                redis_timeout_ms,
            )
        )

    @property
    def redis_habilitado(self):
        return self._redis is not None

    def _chave_redis(self, chave):
        return (
            f"{self._redis_prefixo}:"
            f"rate_limit:{chave}"
        )

    def atingiu_limite(
        self,
        chave: str,
        limite: int,
        janela_segundos: int,
    ) -> bool:
        if self.redis_habilitado:
            try:
                valor = self._redis.get(
                    self._chave_redis(chave)
                )

                return int(
                    valor or 0
                ) >= limite
            except (
                RedisError,
                OSError,
                TypeError,
                ValueError,
            ):
                pass

        return self._atingiu_limite_memoria(
            chave=chave,
            limite=limite,
            janela_segundos=janela_segundos,
        )

    def _atingiu_limite_memoria(
        self,
        chave,
        limite,
        janela_segundos,
    ):
        agora = monotonic()
        inicio_janela = agora - janela_segundos

        with self._lock:
            tentativas = self._tentativas[chave]

            while (
                tentativas
                and tentativas[0] <= inicio_janela
            ):
                tentativas.popleft()

            return len(tentativas) >= limite

    def registrar(
        self,
        chave: str,
        janela_segundos=60,
    ):
        if self.redis_habilitado:
            try:
                redis_chave = self._chave_redis(
                    chave
                )
                criada = self._redis.set(
                    redis_chave,
                    1,
                    ex=max(
                        int(janela_segundos),
                        1,
                    ),
                    nx=True,
                )

                if not criada:
                    self._redis.incr(
                        redis_chave
                    )

                return
            except (
                RedisError,
                OSError,
                TypeError,
                ValueError,
            ):
                pass

        with self._lock:
            self._tentativas[chave].append(
                monotonic()
            )

    def limpar(
        self,
        chave: str,
    ):
        if self.redis_habilitado:
            try:
                self._redis.delete(
                    self._chave_redis(chave)
                )
            except (
                RedisError,
                OSError,
            ):
                pass

        with self._lock:
            self._tentativas.pop(
                chave,
                None,
            )

    def limpar_tudo(self):
        with self._lock:
            self._tentativas.clear()

        if not self.redis_habilitado:
            return

        try:
            chaves = list(
                self._redis.scan_iter(
                    match=(
                        f"{self._redis_prefixo}:"
                        "rate_limit:*"
                    )
                )
            )

            if chaves:
                self._redis.delete(
                    *chaves
                )
        except (
            RedisError,
            OSError,
        ):
            return


def _env_int(
    nome,
    padrao,
    minimo=1,
):
    try:
        valor = int(
            os.getenv(
                nome,
                str(padrao),
            )
        )
    except ValueError:
        return padrao

    return max(
        valor,
        minimo,
    )


def _redis_url_rate_limit():
    if (
        os.getenv(
            "LOCADORA_AMBIENTE",
            "development",
        )
        .strip()
        .lower()
        == "test"
    ):
        return None

    valor = os.getenv(
        "LOCADORA_REDIS_URL"
    )

    return (
        valor.strip()
        if valor
        else None
    )


rate_limiter = RateLimiter(
    redis_url=_redis_url_rate_limit(),
    redis_prefixo=os.getenv(
        "LOCADORA_REDIS_PREFIXO",
        "locadora",
    ),
    redis_timeout_ms=_env_int(
        "LOCADORA_REDIS_TIMEOUT_MS",
        500,
        minimo=50,
    ),
)
