class CacheService:
    """Coordena leituras cache-aside sem mover regra de negócio para o Redis."""

    def __init__(
        self,
        cache_backend,
    ):
        if cache_backend is None:
            raise ValueError(
                "Cache backend é obrigatório."
            )

        self.cache_backend = cache_backend

    @property
    def habilitado(self):
        return self.cache_backend.habilitado

    def obter(self, chave):
        return (
            self.cache_backend
            .obter_json(chave)
        )

    def definir(
        self,
        chave,
        valor,
        ttl_segundos,
    ):
        return (
            self.cache_backend
            .definir_json(
                chave,
                valor,
                ttl_segundos,
            )
        )

    def invalidar(self, chave):
        return (
            self.cache_backend
            .remover(chave)
        )

    def obter_ou_calcular(
        self,
        chave,
        ttl_segundos,
        produtor,
        ignorar_cache=False,
    ):
        if not ignorar_cache:
            valor_cache = self.obter(
                chave
            )

            if valor_cache is not None:
                return valor_cache

        valor = produtor()

        self.definir(
            chave=chave,
            valor=valor,
            ttl_segundos=ttl_segundos,
        )

        return valor
