from api.rate_limit import RateLimiter
from modulos.redis_client import RedisError


class RedisFake:
    def __init__(self):
        self.dados = {}
        self.expiracoes = {}
        self.falhar = False

    def _checar(self):
        if self.falhar:
            raise RedisError("redis indisponível")

    def get(self, chave):
        self._checar()
        return self.dados.get(chave)

    def set(
        self,
        chave,
        valor,
        ex=None,
        nx=False,
    ):
        self._checar()

        if nx and chave in self.dados:
            return False

        self.dados[chave] = int(valor)
        self.expiracoes[chave] = ex
        return True

    def incr(self, chave):
        self._checar()
        self.dados[chave] = int(
            self.dados.get(chave, 0)
        ) + 1
        return self.dados[chave]

    def delete(self, *chaves):
        self._checar()

        for chave in chaves:
            self.dados.pop(chave, None)
            self.expiracoes.pop(chave, None)

    def scan_iter(self, match=None):
        self._checar()
        prefixo = (match or "").removesuffix("*")

        return iter(
            chave
            for chave in list(self.dados)
            if chave.startswith(prefixo)
        )


def test_rate_limiter_redis_compartilha_contador_entre_instancias():
    redis_fake = RedisFake()
    primeiro = RateLimiter(
        redis_client=redis_fake,
        redis_prefixo="teste",
    )
    segundo = RateLimiter(
        redis_client=redis_fake,
        redis_prefixo="teste",
    )

    for _ in range(5):
        primeiro.registrar(
            "login:ip:usuario",
            janela_segundos=60,
        )

    assert segundo.atingiu_limite(
        "login:ip:usuario",
        limite=5,
        janela_segundos=60,
    ) is True
    assert redis_fake.expiracoes[
        "teste:rate_limit:login:ip:usuario"
    ] == 60


def test_rate_limiter_redis_limpar_remove_contador():
    redis_fake = RedisFake()
    limiter = RateLimiter(
        redis_client=redis_fake,
    )

    limiter.registrar(
        "login:teste",
        janela_segundos=60,
    )
    limiter.limpar("login:teste")

    assert limiter.atingiu_limite(
        "login:teste",
        limite=1,
        janela_segundos=60,
    ) is False


def test_rate_limiter_faz_fallback_para_memoria_se_redis_falhar():
    redis_fake = RedisFake()
    redis_fake.falhar = True

    limiter = RateLimiter(
        redis_client=redis_fake,
    )

    for _ in range(3):
        limiter.registrar(
            "recuperacao:teste",
            janela_segundos=900,
        )

    assert limiter.atingiu_limite(
        "recuperacao:teste",
        limite=3,
        janela_segundos=900,
    ) is True


def test_rate_limiter_memoria_continua_disponivel_sem_redis():
    limiter = RateLimiter()

    limiter.registrar(
        "login:teste",
        janela_segundos=60,
    )

    assert limiter.atingiu_limite(
        "login:teste",
        limite=1,
        janela_segundos=60,
    ) is True
