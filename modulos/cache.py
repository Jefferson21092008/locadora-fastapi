import json

from modulos.redis_client import (
    RedisError,
    criar_cliente_redis,
)


class CacheRedis:
    """
    Cache JSON opcional apoiado em Redis/Valkey.

    Falhas do cache não interrompem as regras de negócio: em caso
    de indisponibilidade, a aplicação trata a leitura como cache miss
    e continua consultando o banco relacional.
    """

    def __init__(
        self,
        redis_url=None,
        prefixo="locadora",
        timeout_ms=500,
        cliente=None,
    ):
        self.prefixo = (
            str(prefixo or "locadora")
            .strip()
            .strip(":")
            or "locadora"
        )

        self.cliente = (
            cliente
            if cliente is not None
            else criar_cliente_redis(
                redis_url,
                timeout_ms,
            )
        )

    @property
    def habilitado(self):
        return self.cliente is not None

    def _chave(self, chave):
        return (
            f"{self.prefixo}:cache:"
            f"{str(chave).strip()}"
        )

    def obter_json(self, chave):
        if not self.habilitado:
            return None

        try:
            valor = self.cliente.get(
                self._chave(chave)
            )
        except (RedisError, OSError):
            return None

        if valor is None:
            return None

        try:
            return json.loads(valor)
        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            return None

    def definir_json(
        self,
        chave,
        valor,
        ttl_segundos,
    ):
        if not self.habilitado:
            return False

        try:
            payload = json.dumps(
                valor,
                ensure_ascii=False,
                separators=(",", ":"),
            )

            self.cliente.set(
                self._chave(chave),
                payload,
                ex=max(
                    int(ttl_segundos),
                    1,
                ),
            )
            return True
        except (
            RedisError,
            OSError,
            TypeError,
            ValueError,
        ):
            return False

    def remover(self, chave):
        if not self.habilitado:
            return False

        try:
            self.cliente.delete(
                self._chave(chave)
            )
            return True
        except (RedisError, OSError):
            return False

    def ping(self):
        if not self.habilitado:
            return False

        try:
            return bool(
                self.cliente.ping()
            )
        except (RedisError, OSError):
            return False
