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
from modulos.servicos.pagamento_service import (
    PagamentoService,
)
from modulos.servicos.relatorios_service import (
    RelatorioService,
)
from modulos.servicos.reserva_service import (
    ReservaService,
)
from modulos.servicos.exportacao_relatorios_service import (
    ExportacaoRelatoriosService,
)
from modulos.servicos.sessao_service import (
    SessaoService,
)
from modulos.servicos.veiculos_service import (
    VeiculoService,
)
from modulos.servicos.vistoria_service import (
    VistoriaService,
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
        container.sessao_service,
        SessaoService,
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

    assert isinstance(
        container.reserva_service,
        ReservaService,
    )

    assert isinstance(
        container.exportacao_relatorios_service,
        ExportacaoRelatoriosService,
    )

    assert isinstance(
        container.vistoria_service,
        VistoriaService,
    )

    assert isinstance(
        container.pagamento_service,
        PagamentoService,
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
        container.sessao_service
        .sessao_repository
        is container.sessao_repository
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

    assert (
        container.reserva_service
        .reserva_repository
        is container.reserva_repository
    )

    assert (
        container.aluguel_service
        .reserva_service
        is container.reserva_service
    )

    assert (
        container.cliente_service
        .reserva_repository
        is container.reserva_repository
    )

    assert (
        container.vistoria_service
        .aluguel_repository
        is container.aluguel_repository
    )

    assert (
        container.vistoria_service
        .vistoria_repository
        is container.vistoria_repository
    )

    assert (
        container.pagamento_service
        .pagamento_repository
        is container.pagamento_repository
    )

    assert (
        container.pagamento_service
        .vistoria_service
        is container.vistoria_service
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

    assert (
        container.exportacao_relatorios_service
        .relatorio_service
        is container.relatorio_service
    )
