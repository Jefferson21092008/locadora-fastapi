from modulos.cache import CacheRedis
from modulos.redis_client import RedisError


class RedisFake:
    def __init__(self):
        self.dados = {}
        self.ttls = {}
        self.falhar = False

    def _checar(self):
        if self.falhar:
            raise RedisError("redis indisponível")

    def get(self, chave):
        self._checar()
        return self.dados.get(chave)

    def set(self, chave, valor, ex=None, nx=False):
        self._checar()

        if nx and chave in self.dados:
            return False

        self.dados[chave] = valor
        self.ttls[chave] = ex
        return True

    def delete(self, *chaves):
        self._checar()
        removidas = 0

        for chave in chaves:
            if chave in self.dados:
                removidas += 1
                self.dados.pop(chave, None)
                self.ttls.pop(chave, None)

        return removidas

    def ping(self):
        self._checar()
        return True


def test_cache_redis_serializa_json_e_respeita_ttl():
    redis_fake = RedisFake()
    cache = CacheRedis(
        cliente=redis_fake,
        prefixo="locadora-teste",
    )

    gravou = cache.definir_json(
        "dashboard",
        {"total": 10, "ok": True},
        ttl_segundos=30,
    )

    assert gravou is True
    assert cache.obter_json("dashboard") == {
        "total": 10,
        "ok": True,
    }
    assert redis_fake.ttls[
        "locadora-teste:cache:dashboard"
    ] == 30


def test_cache_redis_remove_e_ping():
    redis_fake = RedisFake()
    cache = CacheRedis(
        cliente=redis_fake,
    )

    cache.definir_json(
        "chave",
        {"valor": 1},
        ttl_segundos=10,
    )

    assert cache.ping() is True
    assert cache.remover("chave") is True
    assert cache.obter_json("chave") is None


def test_cache_redis_degrada_para_miss_quando_redis_falha():
    redis_fake = RedisFake()
    redis_fake.falhar = True

    cache = CacheRedis(
        cliente=redis_fake,
    )

    assert cache.obter_json("dashboard") is None
    assert cache.definir_json(
        "dashboard",
        {"total": 10},
        ttl_segundos=30,
    ) is False
    assert cache.ping() is False


def test_cache_sem_redis_fica_desabilitado():
    cache = CacheRedis(
        redis_url=None,
    )

    assert cache.habilitado is False
    assert cache.obter_json("qualquer") is None
    assert cache.definir_json(
        "qualquer",
        {"ok": True},
        ttl_segundos=30,
    ) is False
