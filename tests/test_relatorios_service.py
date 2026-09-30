from modulos.servicos.relatorios_service import RelatorioService


class ClienteFake:
    def __init__(self, ativo=True):
        self.ativo = ativo




class ClienteRepositoryFake:
    def __init__(self, clientes=None):
        self.clientes = clientes or []

    def listar_ativos(self):
        return [
            cliente
            for cliente in self.clientes
            if cliente.ativo
        ]

class VeiculoFake:
    def __init__(self, ativo=True):
        self.ativo = ativo


class VeiculoRepositoryFake:
    def __init__(self, veiculos=None):
        self.veiculos = veiculos or []

    def listar_ativos(self):
        return [
            veiculo
            for veiculo in self.veiculos
            if veiculo.ativo
        ]




class AluguelRepositoryFake:
    def __init__(self, alugueis=None):
        self.alugueis = alugueis or []

    def listar_colecao(self):
        return list(self.alugueis)


class RelatorioRepositoryFake:
    def __init__(self, metricas=None):
        self.metricas = metricas or {}

    def metricas_dashboard(self):
        return dict(self.metricas)


class AluguelFake:
    def __init__(
        self,
        ativo=True,
        valor=0,
    ):
        self.ativo = ativo
        self.valor = valor


def criar_service(
    alugueis=None,
    veiculos=None,
    clientes=None,
):
    return RelatorioService(
        aluguel_repository=(
            AluguelRepositoryFake(
                alugueis or []
            )
        ),
        veiculo_repository=(
            VeiculoRepositoryFake(
                veiculos or []
            )
        ),
        cliente_repository=(
            ClienteRepositoryFake(
                clientes or []
            )
        ),
        relatorio_repository=(
            RelatorioRepositoryFake()
        ),
    )


def test_historico_vazio():
    service = criar_service()

    historico = (
        service.listar_historico()
    )

    assert historico == []


def test_listar_historico():
    aluguel1 = AluguelFake()
    aluguel2 = AluguelFake()

    service = criar_service(
        alugueis=[
            aluguel1,
            aluguel2,
        ]
    )

    historico = (
        service.listar_historico()
    )

    assert len(historico) == 2
    assert aluguel1 in historico
    assert aluguel2 in historico


def test_total_arrecadado():
    alugueis = [
        AluguelFake(
            ativo=False,
            valor=100,
        ),
        AluguelFake(
            ativo=False,
            valor=250,
        ),
    ]

    service = criar_service(
        alugueis=alugueis
    )

    total = (
        service.calcular_total_arrecadado()
    )

    assert total == 350


def test_aluguel_ativo_nao_entra_no_faturamento():
    alugueis = [
        AluguelFake(
            ativo=False,
            valor=100,
        ),
        AluguelFake(
            ativo=True,
            valor=500,
        ),
    ]

    service = criar_service(
        alugueis=alugueis
    )

    total = (
        service.calcular_total_arrecadado()
    )

    assert total == 100


def test_gerar_resumo():
    clientes = [
        ClienteFake(True),
        ClienteFake(True),
        ClienteFake(False),
    ]

    veiculos = [
        VeiculoFake(True),
        VeiculoFake(False),
    ]

    alugueis = [
        AluguelFake(
            ativo=True,
            valor=0,
        ),
        AluguelFake(
            ativo=False,
            valor=200,
        ),
        AluguelFake(
            ativo=False,
            valor=300,
        ),
    ]

    service = criar_service(
        alugueis=alugueis,
        veiculos=veiculos,
        clientes=clientes,
    )

    resumo = (
        service.gerar_resumo()
    )

    assert resumo[
        "clientes_ativos"
    ] == 2

    assert resumo[
        "veiculos_ativos"
    ] == 1

    assert resumo[
        "alugueis_ativos"
    ] == 1

    assert resumo[
        "alugueis_finalizados"
    ] == 2

    assert resumo[
        "total_arrecadado"
    ] == 500

def test_metricas_dashboard_calcula_taxa_e_resultado():
    metricas = {
        "clientes_ativos": 4,
        "clientes_inativos": 1,
        "veiculos_disponiveis": 5,
        "veiculos_alugados": 3,
        "veiculos_manutencao": 2,
        "veiculos_desativados": 1,
        "alugueis_ativos": 3,
        "alugueis_finalizados": 10,
        "manutencoes_ativas": 2,
        "manutencoes_finalizadas": 7,
        "receita_alugueis": 12000.0,
        "custos_manutencao": 2500.0,
        "ticket_medio": 1200.0,
    }

    service = RelatorioService(
        aluguel_repository=AluguelRepositoryFake(),
        veiculo_repository=VeiculoRepositoryFake(),
        cliente_repository=ClienteRepositoryFake(),
        relatorio_repository=RelatorioRepositoryFake(metricas),
    )

    resultado = service.metricas_dashboard()

    assert resultado["veiculos_ativos"] == 10
    assert resultado["taxa_frota_alugada"] == 30.0
    assert resultado["resultado_bruto"] == 9500.0
    assert resultado["ticket_medio"] == 1200.0


class CacheServiceFake:
    def __init__(self):
        self.dados = {}
        self.chamadas_produtor = 0
        self.ignorar_cache = []

    def obter_ou_calcular(
        self,
        chave,
        ttl_segundos,
        produtor,
        ignorar_cache=False,
    ):
        self.ignorar_cache.append(
            ignorar_cache
        )

        if (
            not ignorar_cache
            and chave in self.dados
        ):
            return self.dados[chave]

        self.chamadas_produtor += 1
        valor = produtor()
        self.dados[chave] = valor
        return valor


def _metricas_dashboard_teste():
    return {
        "clientes_ativos": 4,
        "clientes_inativos": 1,
        "veiculos_disponiveis": 5,
        "veiculos_alugados": 3,
        "veiculos_manutencao": 2,
        "veiculos_desativados": 1,
        "alugueis_ativos": 3,
        "alugueis_finalizados": 10,
        "manutencoes_ativas": 2,
        "manutencoes_finalizadas": 7,
        "receita_alugueis": 12000.0,
        "custos_manutencao": 2500.0,
        "ticket_medio": 1200.0,
    }


def test_metricas_dashboard_reutiliza_cache():
    cache = CacheServiceFake()
    repository = RelatorioRepositoryFake(
        _metricas_dashboard_teste()
    )
    service = RelatorioService(
        aluguel_repository=AluguelRepositoryFake(),
        veiculo_repository=VeiculoRepositoryFake(),
        cliente_repository=ClienteRepositoryFake(),
        relatorio_repository=repository,
        cache_service=cache,
        dashboard_cache_ttl_segundos=30,
    )

    primeiro = service.metricas_dashboard()
    repository.metricas[
        "receita_alugueis"
    ] = 99999.0
    segundo = service.metricas_dashboard()

    assert primeiro == segundo
    assert primeiro[
        "receita_alugueis"
    ] == 12000.0
    assert cache.chamadas_produtor == 1


def test_metricas_dashboard_forca_recalculo_e_atualiza_cache():
    cache = CacheServiceFake()
    repository = RelatorioRepositoryFake(
        _metricas_dashboard_teste()
    )
    service = RelatorioService(
        aluguel_repository=AluguelRepositoryFake(),
        veiculo_repository=VeiculoRepositoryFake(),
        cliente_repository=ClienteRepositoryFake(),
        relatorio_repository=repository,
        cache_service=cache,
    )

    service.metricas_dashboard()
    repository.metricas[
        "receita_alugueis"
    ] = 15000.0

    atualizado = service.metricas_dashboard(
        forcar_atualizacao=True
    )

    assert atualizado[
        "receita_alugueis"
    ] == 15000.0
    assert atualizado[
        "resultado_bruto"
    ] == 12500.0
    assert cache.chamadas_produtor == 2
    assert cache.ignorar_cache[-1] is True
