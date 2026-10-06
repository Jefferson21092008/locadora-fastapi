from modulos.event_handlers import (
    EVENTOS_QUE_INVALIDAM_DASHBOARD,
    registrar_handlers_padrao,
)
from modulos.eventos import BarramentoEventos, EventoAplicacao
from modulos.servicos.relatorios_service import RelatorioService


class CacheServiceFake:
    def __init__(self):
        self.invalidacoes = []

    def invalidar(self, chave):
        self.invalidacoes.append(chave)
        return True


def test_eventos_operacionais_invalidam_dashboard():
    barramento = BarramentoEventos()
    cache = CacheServiceFake()
    registrar_handlers_padrao(
        barramento=barramento,
        cache_service=cache,
    )

    for nome in sorted(EVENTOS_QUE_INVALIDAM_DASHBOARD):
        barramento.publicar(EventoAplicacao(nome=nome))

    assert cache.invalidacoes == [
        RelatorioService.CHAVE_CACHE_DASHBOARD
    ] * len(EVENTOS_QUE_INVALIDAM_DASHBOARD)


def test_evento_sem_impacto_no_dashboard_nao_invalida_cache():
    barramento = BarramentoEventos()
    cache = CacheServiceFake()
    registrar_handlers_padrao(
        barramento=barramento,
        cache_service=cache,
    )

    barramento.publicar(
        EventoAplicacao(nome="pagamento.registrado")
    )

    assert cache.invalidacoes == []
