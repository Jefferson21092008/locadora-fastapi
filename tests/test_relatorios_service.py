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
    pass


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
