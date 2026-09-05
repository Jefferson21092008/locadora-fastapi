import pytest

from modulos.container import Container
from modulos.database import BancoSQLAlchemy

from modulos.servicos.admin_service import (
    AdminService,
)
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


class ConfiguracaoFake:
    admin_usuario = "admin"
    admin_senha = "admin123"

    email_configurado = False
    email_smtp_host = None
    email_smtp_port = 587
    email_usuario = None
    email_senha = None
    email_remetente = None


@pytest.fixture
def container():
    banco = BancoSQLAlchemy(
        "sqlite:///:memory:"
    )

    instancia = Container(
        config=ConfiguracaoFake(),
        banco_sqlalchemy=banco,
    )

    try:
        yield instancia
    finally:
        banco.fechar()


def test_container_cria_services(
    container,
):
    assert isinstance(
        container.auth_service,
        AuthService,
    )

    assert isinstance(
        container.admin_service,
        AdminService,
    )

    assert isinstance(
        container.cliente_service,
        ClienteService,
    )

    assert isinstance(
        container.veiculo_service,
        VeiculoService,
    )

    assert isinstance(
        container.aluguel_service,
        AluguelService,
    )

    assert isinstance(
        container.manutencao_service,
        ManutencaoService,
    )

    assert isinstance(
        container.relatorio_service,
        RelatorioService,
    )


def test_container_cria_admin_padrao(
    container,
):
    admin = (
        container.auth_service
        .buscar_por_usuario(
            "admin"
        )
    )

    assert admin is not None
    assert admin.id == 1
    assert admin.ativo is True


def test_services_compartilham_repositories(
    container,
):
    assert (
        container.auth_service
        .usuario_repository
        is container.usuario_repository
    )

    assert (
        container.veiculo_service
        .veiculo_repository
        is container.veiculo_repository
    )

    assert (
        container.cliente_service
        .cliente_repository
        is container.cliente_repository
    )

    assert (
        container.cliente_service
        .aluguel_repository
        is container.aluguel_repository
    )

    assert (
        container.aluguel_service
        .aluguel_repository
        is container.aluguel_repository
    )

    assert (
        container.manutencao_service
        .manutencao_repository
        is container.manutencao_repository
    )


def test_relatorio_service_compartilha_repositories(
    container,
):
    service = (
        container.relatorio_service
    )

    assert (
        service.aluguel_repository
        is container.aluguel_repository
    )

    assert (
        service.veiculo_repository
        is container.veiculo_repository
    )

    assert (
        service.cliente_repository
        is container.cliente_repository
    )

    assert (
        service.relatorio_repository
        is container.relatorio_repository
    )
