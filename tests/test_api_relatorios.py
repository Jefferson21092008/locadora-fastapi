from types import SimpleNamespace

import pytest

from fastapi.testclient import TestClient

from api.dependencias import (
    get_container,
)

from api.main import app

from api.seguranca import (
    criar_token_acesso,
)


JWT_SECRET_TESTE = (
    "locadora-jwt-chave-de-testes-1234567890"
)


# ================================================================
# CONFIGURAÇÃO
# ================================================================


class ConfiguracaoFake:
    jwt_secret = JWT_SECRET_TESTE


# ================================================================
# USUÁRIO
# ================================================================


class UsuarioFake:
    def __init__(
        self,
        id_usuario,
        usuario,
        role,
        ativo=True,
    ):
        self.id = id_usuario
        self.usuario = usuario
        self.ativo = ativo

        self.role = SimpleNamespace(
            value=role
        )


# ================================================================
# AUTH SERVICE
# ================================================================


class AuthServiceFake:
    def __init__(self):
        self.admin = UsuarioFake(
            id_usuario=100,
            usuario="admin",
            role="admin",
        )

        self.cliente = UsuarioFake(
            id_usuario=200,
            usuario="cliente",
            role="cliente",
        )

    def buscar_por_id(
        self,
        id_usuario,
    ):
        usuarios = [
            self.admin,
            self.cliente,
        ]

        for usuario in usuarios:
            if (
                usuario.id
                == id_usuario
            ):
                return usuario

        return None


# ================================================================
# RELATÓRIO SERVICE
# ================================================================


class RelatorioServiceFake:
    def gerar_resumo(
        self,
    ):
        return {
            "clientes_ativos": 5,
            "veiculos_ativos": 8,
            "alugueis_ativos": 2,
            "alugueis_finalizados": 15,
            "total_arrecadado": 12500.50,
        }

    def veiculos_mais_alugados(
        self,
        limite=10,
    ):
        dados = [
            {
                "id": 1,
                "tipo": "carro",
                "modelo": "Corolla",
                "total_alugueis": 10,
            },
            {
                "id": 2,
                "tipo": "moto",
                "modelo": "CB 500",
                "total_alugueis": 7,
            },
        ]

        return dados[
            :limite
        ]

    def faturamento_por_tipo(
        self,
    ):
        return [
            {
                "tipo": "carro",
                "total_alugueis": 12,
                "faturamento": 9000.0,
            },
            {
                "tipo": "moto",
                "total_alugueis": 5,
                "faturamento": 3500.0,
            },
        ]

    def custos_manutencao(
        self,
    ):
        return [
            {
                "id": 1,
                "tipo": "carro",
                "modelo": "Corolla",
                "total_manutencoes": 3,
                "custo_total": 1800.0,
            }
        ]

    def clientes_mais_alugam(
        self,
        limite=10,
    ):
        dados = [
            {
                "cliente_id": 1,
                "cliente_nome": "Lucas",
                "cliente_usuario": "lucas123",
                "total_alugueis": 8,
                "total_gasto": 5000.0,
            },
            {
                "cliente_id": 2,
                "cliente_nome": "Maria",
                "cliente_usuario": "maria123",
                "total_alugueis": 4,
                "total_gasto": 2500.0,
            },
        ]

        return dados[
            :limite
        ]

    def resumo_financeiro(
        self,
    ):
        return {
            "receita_alugueis": 15000.0,
            "custos_manutencao": 3000.0,
            "resultado_bruto": 12000.0,
        }

    def resultado_por_veiculo(
        self,
    ):
        return [
            {
                "id": 1,
                "tipo": "carro",
                "modelo": "Corolla",
                "total_alugueis": 10,
                "receita": 8000.0,
                "total_manutencoes": 2,
                "custo_manutencao": 1500.0,
                "resultado_bruto": 6500.0,
            }
        ]


# ================================================================
# CONTAINER
# ================================================================


class ContainerFake:
    def __init__(self):
        self.config = (
            ConfiguracaoFake()
        )

        self.auth_service = (
            AuthServiceFake()
        )

        self.relatorio_service = (
            RelatorioServiceFake()
        )


# ================================================================
# TOKEN
# ================================================================


def gerar_token(
    usuario,
):
    return criar_token_acesso(
        usuario=usuario,
        secret=JWT_SECRET_TESTE,
    )


# ================================================================
# FIXTURES
# ================================================================


@pytest.fixture
def ambiente():
    container_fake = (
        ContainerFake()
    )

    app.dependency_overrides[
        get_container
    ] = lambda: container_fake

    with TestClient(app) as client:
        yield (
            client,
            container_fake,
        )

    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(
    ambiente,
):
    client, container_fake = (
        ambiente
    )

    token = gerar_token(
        container_fake
        .auth_service
        .admin
    )

    client.headers.update(
        {
            "Authorization": (
                f"Bearer {token}"
            )
        }
    )

    return client


@pytest.fixture
def cliente_client(
    ambiente,
):
    client, container_fake = (
        ambiente
    )

    token = gerar_token(
        container_fake
        .auth_service
        .cliente
    )

    client.headers.update(
        {
            "Authorization": (
                f"Bearer {token}"
            )
        }
    )

    return client


# ================================================================
# RESUMO
# ================================================================


def test_admin_pode_ver_resumo(
    admin_client,
):
    response = admin_client.get(
        "/relatorios/resumo"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert (
        dados["clientes_ativos"]
        == 5
    )

    assert (
        dados["veiculos_ativos"]
        == 8
    )

    assert (
        dados["total_arrecadado"]
        == 12500.50
    )


# ================================================================
# VEÍCULOS MAIS ALUGADOS
# ================================================================


def test_veiculos_mais_alugados(
    admin_client,
):
    response = admin_client.get(
        "/relatorios/"
        "veiculos-mais-alugados"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert len(dados) == 2

    assert (
        dados[0]["modelo"]
        == "Corolla"
    )

    assert (
        dados[0][
            "total_alugueis"
        ]
        == 10
    )


def test_limite_veiculos_mais_alugados(
    admin_client,
):
    response = admin_client.get(
        "/relatorios/"
        "veiculos-mais-alugados"
        "?limite=1"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert len(dados) == 1


# ================================================================
# FATURAMENTO
# ================================================================


def test_faturamento_por_tipo(
    admin_client,
):
    response = admin_client.get(
        "/relatorios/"
        "faturamento-por-tipo"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert len(dados) == 2

    assert (
        dados[0]["tipo"]
        == "carro"
    )

    assert (
        dados[0]["faturamento"]
        == 9000.0
    )


# ================================================================
# MANUTENÇÃO
# ================================================================


def test_custos_manutencao(
    admin_client,
):
    response = admin_client.get(
        "/relatorios/"
        "custos-manutencao"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert len(dados) == 1

    assert (
        dados[0]["custo_total"]
        == 1800.0
    )


# ================================================================
# CLIENTES
# ================================================================


def test_clientes_mais_alugam(
    admin_client,
):
    response = admin_client.get(
        "/relatorios/"
        "clientes-mais-alugam"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert len(dados) == 2

    assert (
        dados[0][
            "cliente_usuario"
        ]
        == "lucas123"
    )

    assert (
        dados[0][
            "total_alugueis"
        ]
        == 8
    )


def test_limite_clientes_mais_alugam(
    admin_client,
):
    response = admin_client.get(
        "/relatorios/"
        "clientes-mais-alugam"
        "?limite=1"
    )

    assert (
        response.status_code
        == 200
    )

    assert (
        len(
            response.json()
        )
        == 1
    )


# ================================================================
# FINANCEIRO
# ================================================================


def test_resumo_financeiro(
    admin_client,
):
    response = admin_client.get(
        "/relatorios/"
        "resumo-financeiro"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert (
        dados[
            "receita_alugueis"
        ]
        == 15000.0
    )

    assert (
        dados[
            "custos_manutencao"
        ]
        == 3000.0
    )

    assert (
        dados[
            "resultado_bruto"
        ]
        == 12000.0
    )


def test_resultado_por_veiculo(
    admin_client,
):
    response = admin_client.get(
        "/relatorios/"
        "resultado-por-veiculo"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert len(dados) == 1

    assert (
        dados[0]["modelo"]
        == "Corolla"
    )

    assert (
        dados[0][
            "resultado_bruto"
        ]
        == 6500.0
    )


# ================================================================
# VALIDAÇÃO
# ================================================================


def test_limite_invalido(
    admin_client,
):
    response = admin_client.get(
        "/relatorios/"
        "veiculos-mais-alugados"
        "?limite=0"
    )

    assert (
        response.status_code
        == 422
    )


# ================================================================
# SEGURANÇA
# ================================================================


def test_cliente_nao_pode_ver_relatorios(
    cliente_client,
):
    response = cliente_client.get(
        "/relatorios/resumo"
    )

    assert (
        response.status_code
        == 403
    )

    assert response.json() == {
        "detail": (
            "Acesso permitido "
            "apenas para "
            "administradores."
        )
    }


def test_relatorios_sem_token(
    ambiente,
):
    client, _ = ambiente

    response = client.get(
        "/relatorios/resumo"
    )

    assert (
        response.status_code
        == 401
    )

    assert response.json() == {
        "detail": (
            "Autenticação necessária."
        )
    }