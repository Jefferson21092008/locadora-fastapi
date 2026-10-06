from modulos.servicos.relatorios_service import RelatorioService


EVENTOS_QUE_INVALIDAM_DASHBOARD = {
    "aluguel.criado",
    "aluguel.finalizado",
    "manutencao.aberta",
    "manutencao.atualizada",
    "manutencao.finalizada",
}


class InvalidarDashboardAoMudarOperacao:
    """Handler pequeno e desacoplado dos services que geram os eventos."""

    def __init__(self, cache_service):
        self.cache_service = cache_service

    def __call__(self, evento):
        return self.cache_service.invalidar(
            RelatorioService.CHAVE_CACHE_DASHBOARD
        )


def registrar_handlers_padrao(barramento, cache_service):
    handler_dashboard = InvalidarDashboardAoMudarOperacao(
        cache_service
    )

    for nome_evento in sorted(EVENTOS_QUE_INVALIDAM_DASHBOARD):
        barramento.assinar(nome_evento, handler_dashboard)

    return {
        "dashboard": handler_dashboard,
    }
