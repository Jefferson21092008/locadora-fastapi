from modulos.servicos.cache_service import CacheService


class CacheBackendFake:
    def __init__(self):
        self.habilitado = True
        self.dados = {}
        self.definicoes = []

    def obter_json(self, chave):
        return self.dados.get(chave)

    def definir_json(
        self,
        chave,
        valor,
        ttl_segundos,
    ):
        self.dados[chave] = valor
        self.definicoes.append(
            (chave, valor, ttl_segundos)
        )
        return True

    def remover(self, chave):
        self.dados.pop(chave, None)
        return True


def test_cache_service_reutiliza_valor_sem_recalcular():
    backend = CacheBackendFake()
    service = CacheService(backend)
    chamadas = []

    def produtor():
        chamadas.append(True)
        return {"valor": 42}

    primeiro = service.obter_ou_calcular(
        "teste",
        ttl_segundos=30,
        produtor=produtor,
    )
    segundo = service.obter_ou_calcular(
        "teste",
        ttl_segundos=30,
        produtor=produtor,
    )

    assert primeiro == {"valor": 42}
    assert segundo == primeiro
    assert len(chamadas) == 1


def test_cache_service_pode_forcar_atualizacao():
    backend = CacheBackendFake()
    backend.dados["teste"] = {
        "valor": "antigo"
    }
    service = CacheService(backend)

    resultado = service.obter_ou_calcular(
        "teste",
        ttl_segundos=15,
        produtor=lambda: {
            "valor": "novo"
        },
        ignorar_cache=True,
    )

    assert resultado == {
        "valor": "novo"
    }
    assert backend.dados["teste"] == {
        "valor": "novo"
    }
    assert backend.definicoes[-1][2] == 15


def test_cache_service_invalida_chave():
    backend = CacheBackendFake()
    backend.dados["teste"] = {
        "ok": True
    }
    service = CacheService(backend)

    assert service.invalidar("teste") is True
    assert service.obter("teste") is None
