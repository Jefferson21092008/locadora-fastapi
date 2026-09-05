import pytest

from modulos.servicos.alugueis_service import (
    AluguelService,
)
from modulos.servicos.auth_service import (
    AuthService,
)
from modulos.servicos.clientes_service import (
    ClienteService,
)
from modulos.servicos.manutencao_service import (
    ManutencaoService,
)
from modulos.servicos.relatorios_service import (
    RelatorioService,
)
from modulos.servicos.veiculos_service import (
    VeiculoService,
)


class DependenciaFake:
    pass


def test_auth_service_aceita_repository_sem_dados():
    repository = DependenciaFake()

    service = AuthService(
        usuario_repository=repository,
    )

    assert service.usuario_repository is repository


def test_veiculo_service_aceita_repository_sem_dados():
    repository = DependenciaFake()

    service = VeiculoService(
        veiculo_repository=repository,
    )

    assert service.veiculo_repository is repository


def test_cliente_service_aceita_repositories_sem_dados():
    cliente_repository = DependenciaFake()
    aluguel_repository = DependenciaFake()
    auth_service = DependenciaFake()

    service = ClienteService(
        auth_service=auth_service,
        cliente_repository=cliente_repository,
        aluguel_repository=aluguel_repository,
    )

    assert service.auth_service is auth_service
    assert service.cliente_repository is cliente_repository
    assert service.aluguel_repository is aluguel_repository


def test_aluguel_service_aceita_repository_sem_dados():
    repository = DependenciaFake()
    veiculo_service = DependenciaFake()

    service = AluguelService(
        veiculo_service=veiculo_service,
        aluguel_repository=repository,
    )

    assert service.veiculo_service is veiculo_service
    assert service.aluguel_repository is repository


def test_manutencao_service_aceita_repository_sem_dados():
    repository = DependenciaFake()
    veiculo_service = DependenciaFake()

    service = ManutencaoService(
        veiculo_service=veiculo_service,
        manutencao_repository=repository,
    )

    assert service.veiculo_service is veiculo_service
    assert service.manutencao_repository is repository


def test_relatorio_service_aceita_repositories_sem_dados():
    aluguel_repository = DependenciaFake()
    veiculo_repository = DependenciaFake()
    cliente_repository = DependenciaFake()
    relatorio_repository = DependenciaFake()

    service = RelatorioService(
        aluguel_repository=aluguel_repository,
        veiculo_repository=veiculo_repository,
        cliente_repository=cliente_repository,
        relatorio_repository=relatorio_repository,
    )

    assert service.aluguel_repository is aluguel_repository
    assert service.veiculo_repository is veiculo_repository
    assert service.cliente_repository is cliente_repository
    assert service.relatorio_repository is relatorio_repository


@pytest.mark.parametrize(
    ("nome_parametro", "mensagem"),
    [
        ("aluguel_repository", "AluguelRepository é obrigatório."),
        ("veiculo_repository", "VeiculoRepository é obrigatório."),
        ("cliente_repository", "ClienteRepository é obrigatório."),
        ("relatorio_repository", "RelatorioRepository é obrigatório."),
    ],
)
def test_relatorio_service_exige_todos_repositories(
    nome_parametro,
    mensagem,
):
    dependencias = {
        "aluguel_repository": DependenciaFake(),
        "veiculo_repository": DependenciaFake(),
        "cliente_repository": DependenciaFake(),
        "relatorio_repository": DependenciaFake(),
    }
    dependencias[nome_parametro] = None

    with pytest.raises(
        ValueError,
        match=mensagem,
    ):
        RelatorioService(**dependencias)


def test_aluguel_service_exige_veiculo_service():
    try:
        AluguelService(
            veiculo_service=None,
            aluguel_repository=DependenciaFake(),
        )
    except ValueError as erro:
        assert str(erro) == "VeiculoService é obrigatório."
    else:
        raise AssertionError(
            "AluguelService deveria exigir VeiculoService."
        )


def test_aluguel_service_exige_repository():
    try:
        AluguelService(
            veiculo_service=DependenciaFake(),
            aluguel_repository=None,
        )
    except ValueError as erro:
        assert str(erro) == "AluguelRepository é obrigatório."
    else:
        raise AssertionError(
            "AluguelService deveria exigir AluguelRepository."
        )


def test_manutencao_service_exige_veiculo_service():
    try:
        ManutencaoService(
            veiculo_service=None,
            manutencao_repository=DependenciaFake(),
        )
    except ValueError as erro:
        assert str(erro) == "VeiculoService é obrigatório."
    else:
        raise AssertionError(
            "ManutencaoService deveria exigir VeiculoService."
        )


def test_manutencao_service_exige_repository():
    try:
        ManutencaoService(
            veiculo_service=DependenciaFake(),
            manutencao_repository=None,
        )
    except ValueError as erro:
        assert str(erro) == "ManutencaoRepository é obrigatório."
    else:
        raise AssertionError(
            "ManutencaoService deveria exigir ManutencaoRepository."
        )
