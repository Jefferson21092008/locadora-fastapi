from functools import lru_cache

try:
    import redis
    from redis.exceptions import RedisError
except ImportError:  # pragma: no cover - dependency is installed in app envs
    redis = None

    class RedisError(Exception):
        pass


@lru_cache(maxsize=8)
def criar_cliente_redis(
    redis_url,
    timeout_ms=500,
):
    """
    Cria um cliente Redis/Valkey compartilhado por processo.

    A conexão é lazy: ``from_url`` apenas configura o pool e a
    primeira operação efetivamente abre a conexão.
    """
    if not redis_url or redis is None:
        return None

    timeout_segundos = max(
        int(timeout_ms),
        50,
    ) / 1000

    return redis.Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=timeout_segundos,
        socket_timeout=timeout_segundos,
        health_check_interval=30,
    )
