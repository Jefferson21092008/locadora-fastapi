from types import SimpleNamespace

import pytest

from fastapi.testclient import TestClient

from api.dependencias import get_container
from api.main import app
from api.seguranca import criar_token_acesso

from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)


JWT_SECRET_TESTE = (
    "locadora-jwt-chave-de-testes-1234567890"
)


# ================================================================
# CONFIGURAÇÃO FAKE
# ================================================================


class ConfiguracaoFake:
    jwt_secret = JWT_SECRET_TESTE


# ================================================================
# USUÁRIO FAKE
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
# CLIENTE FAKE
# ================================================================


class ClienteFake:
    def __init__(
        self,
        id_cliente,
        usuario_id,
        nome,
        usuario,
        ativo=True,
    ):
        self.id = id_cliente
        self.usuario_id = usuario_id
        self.nome = nome
        self.usuario = usuario
        self.ativo = ativo


# ================================================================
# ALUGUEL FAKE
# ================================================================


class AluguelFake:
    def __init__(
        self,
        id_aluguel,
        cliente,
        id_veiculo,
        veiculo_tipo="carro",
        veiculo_modelo="Civic",
        dias=3,
        status="ativo",
    ):
        self.id = id_aluguel

        self.cliente_id = (
            cliente.id
        )

        self.cliente_usuario = (
            cliente.usuario
        )

        self.cliente_nome = (
            cliente.nome
        )

        self.veiculo_id = id_veiculo

        self.veiculo_tipo = (
            veiculo_tipo
        )

        self.veiculo_modelo = (
            veiculo_modelo
        )

        self.dias = dias
        self.status = status

        self.km = 0.0
        self.pagamento = None
        self.valor = 0.0

        self.data_inicio = (
            "2026-08-27"
        )

        self.data_prevista = (
            "2026-08-30"
        )

        self.data_fim = None

        self.dias_atraso = 0
        self.multa = 0.0


# ================================================================
# AUTH SERVICE FAKE
# ================================================================


class AuthServiceFake:
    def __init__(self):
        self.cliente = UsuarioFake(
            id_usuario=100,
            usuario="lucas123",
            role="cliente",
        )

        self.admin = UsuarioFake(
            id_usuario=200,
            usuario="admin",
            role="admin",
        )

        self.sem_perfil = UsuarioFake(
            id_usuario=300,
            usuario="semperfil",
            role="cliente",
        )

        self.desativado = UsuarioFake(
            id_usuario=400,
            usuario="desativado",
            role="cliente",
        )

    def buscar_por_id(
        self,
        id_usuario,
    ):
        usuarios = [
            self.cliente,
            self.admin,
            self.sem_perfil,
            self.desativado,
        ]

        for usuario in usuarios:
            if (
                usuario.id
                == id_usuario
            ):
                return usuario

        return None


# ================================================================
# CLIENTE SERVICE FAKE
# ================================================================


class ClienteServiceFake:
    def __init__(self):
        self.cliente = ClienteFake(
            id_cliente=1,
            usuario_id=100,
            nome="Lucas",
            usuario="lucas123",
        )

        self.cliente_desativado = (
            ClienteFake(
                id_cliente=2,
                usuario_id=400,
                nome="Pedro",
                usuario="desativado",
                ativo=False,
            )
        )

    def buscar_por_usuario_id(
        self,
        usuario_id,
    ):
        clientes = [
            self.cliente,
            self.cliente_desativado,
        ]

        for cliente in clientes:
            if (
                cliente.usuario_id
                == usuario_id
            ):
                return cliente

        return None


# ================================================================
# ALUGUEL SERVICE FAKE
# ================================================================


class AluguelServiceFake:
    def __init__(
        self,
        cliente_service,
    ):
        self.cliente_service = (
            cliente_service
        )

        outro_cliente = ClienteFake(
            id_cliente=99,
            usuario_id=999,
            nome="Maria",
            usuario="maria123",
        )

        self.alugueis = [
            AluguelFake(
                id_aluguel=1,
                cliente=(
                    cliente_service
                    .cliente
                ),
                id_veiculo=10,
                veiculo_modelo=(
                    "Corolla"
                ),
                dias=5,
            ),

            AluguelFake(
                id_aluguel=2,
                cliente=outro_cliente,
                id_veiculo=20,
                veiculo_modelo=(
                    "Civic"
                ),
                dias=4,
                status="finalizado",
            ),
        ]

    # ============================================================
    # CONSULTAS
    # ============================================================

    def listar_do_cliente(
        self,
        cliente,
    ):
        return [
            aluguel
            for aluguel
            in self.alugueis
            if (
                aluguel.cliente_id
                == cliente.id
            )
        ]

    def listar_alugueis(
        self,
    ):
        return list(
            self.alugueis
        )

    def listar_ativos(
        self,
    ):
        return [
            aluguel
            for aluguel
            in self.alugueis
            if (
                aluguel.status
                == "ativo"
            )
        ]

    # ============================================================
    # NOVO ALUGUEL
    # ============================================================

    def alugar(
        self,
        cliente,
        id_veiculo,
        dias,
        anos_habilitacao=None,
    ):
        if dias <= 0:
            raise RegraDeNegocio(
                "A quantidade de dias "
                "deve ser maior que zero."
            )

        if id_veiculo == 999:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        novo_aluguel = AluguelFake(
            id_aluguel=(
                len(
                    self.alugueis
                )
                + 1
            ),
            cliente=cliente,
            id_veiculo=id_veiculo,
            dias=dias,
        )

        self.alugueis.append(
            novo_aluguel
        )

        return novo_aluguel

    # ============================================================
    # DEVOLUÇÃO
    # ============================================================

    def devolver(
        self,
        cliente,
        id_veiculo,
        km,
        forma_pagamento,
        parcelas=None,
        data_referencia=None,
    ):
        if km < 0:
            raise RegraDeNegocio(
                "A quilometragem não pode "
                "ser negativa."
            )

        aluguel = None

        for item in self.alugueis:
            if (
                item.cliente_id
                == cliente.id
                and item.veiculo_id
                == id_veiculo
                and item.status
                == "ativo"
            ):
                aluguel = item
                break

        if aluguel is None:
            raise RegraDeNegocio(
                "Esse veículo não pertence "
                "aos seus aluguéis ativos."
            )

        if forma_pagamento == 5:
            if (
                parcelas is None
                or not 2 <= parcelas <= 12
            ):
                raise RegraDeNegocio(
                    "A quantidade de parcelas "
                    "deve estar entre 2 e 12."
                )

        formas = {
            1: "Dinheiro",
            2: "Pix",
            3: "Débito",
            4: "Crédito à vista",
            6: "Boleto",
            7: "Transferência",
        }

        if (
            forma_pagamento != 5
            and forma_pagamento
            not in formas
        ):
            raise RegraDeNegocio(
                "Forma de pagamento inválida."
            )

        valor_aluguel = 300.0
        multa = 0.0

        total = (
            valor_aluguel
            + multa
        )

        if forma_pagamento == 5:
            forma = (
                f"Crédito {parcelas}x"
            )

            if parcelas <= 2:
                juros = 0.0

            elif parcelas <= 6:
                juros = 0.10

            else:
                juros = 0.20

            valor_final = (
                total
                * (1 + juros)
            )

            quantidade_parcelas = (
                parcelas
            )

        else:
            forma = formas[
                forma_pagamento
            ]

            taxas = {
                1: -0.10,
                2: -0.15,
                3: -0.05,
                4: 0.0,
                6: -0.05,
                7: -0.05,
            }

            valor_final = (
                total
                * (
                    1
                    + taxas[
                        forma_pagamento
                    ]
                )
            )

            quantidade_parcelas = 1

        pagamento = {
            "valor_final": (
                valor_final
            ),

            "forma": forma,

            "parcelas": (
                quantidade_parcelas
            ),

            "valor_parcela": (
                valor_final
                / quantidade_parcelas
            ),
        }

        aluguel.status = (
            "finalizado"
        )

        aluguel.km = km

        aluguel.pagamento = (
            pagamento[
                "forma"
            ]
        )

        aluguel.valor = (
            pagamento[
                "valor_final"
            ]
        )

        aluguel.data_fim = (
            "2026-08-27"
        )

        aluguel.dias_atraso = 0
        aluguel.multa = multa

        return {
            "aluguel": aluguel,

            "veiculo": (
                SimpleNamespace(
                    id=id_veiculo
                )
            ),

            "valor_aluguel": (
                valor_aluguel
            ),

            "dias_atraso": 0,

            "multa": multa,

            "valor_inicial": (
                total
            ),

            "pagamento": (
                pagamento
            ),
        }


# ================================================================
# CONTAINER FAKE
# ================================================================


class ContainerFake:
    def __init__(self):
        self.config = (
            ConfiguracaoFake()
        )

        self.auth_service = (
            AuthServiceFake()
        )

        self.cliente_service = (
            ClienteServiceFake()
        )

        self.aluguel_service = (
            AluguelServiceFake(
                self.cliente_service
            )
        )


# ================================================================
# JWT
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
def client(
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
# CLIENTE - LISTAGEM
# ================================================================


def test_listar_meus_alugueis(
    client,
):
    response = client.get(
        "/alugueis/me"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert len(dados) == 1

    aluguel = dados[0]

    assert aluguel["id"] == 1

    assert (
        aluguel["cliente_id"]
        == 1
    )

    assert (
        aluguel["cliente_usuario"]
        == "lucas123"
    )

    assert (
        aluguel["veiculo_id"]
        == 10
    )

    assert (
        aluguel["veiculo_modelo"]
        == "Corolla"
    )

    assert (
        aluguel["status"]
        == "ativo"
    )


# ================================================================
# CLIENTE - CRIAÇÃO
# ================================================================


def test_criar_aluguel(
    client,
):
    response = client.post(
        "/alugueis",
        json={
            "id_veiculo": 30,
            "dias": 3,
            "anos_habilitacao": 5,
        },
    )

    assert (
        response.status_code
        == 201
    )

    dados = response.json()

    assert dados["id"] == 3

    assert (
        dados["cliente_id"]
        == 1
    )

    assert (
        dados["cliente_usuario"]
        == "lucas123"
    )

    assert (
        dados["veiculo_id"]
        == 30
    )

    assert dados["dias"] == 3

    assert (
        dados["status"]
        == "ativo"
    )


def test_criar_aluguel_sem_enviar_cliente_id(
    client,
):
    response = client.post(
        "/alugueis",
        json={
            "id_veiculo": 30,
            "dias": 2,
            "anos_habilitacao": 4,
        },
    )

    assert (
        response.status_code
        == 201
    )

    dados = response.json()

    assert (
        dados["cliente_id"]
        == 1
    )

    assert (
        dados["cliente_usuario"]
        == "lucas123"
    )


def test_criar_aluguel_com_dias_invalidos(
    client,
):
    response = client.post(
        "/alugueis",
        json={
            "id_veiculo": 30,
            "dias": 0,
            "anos_habilitacao": 5,
        },
    )

    assert (
        response.status_code
        == 422
    )


def test_criar_aluguel_com_veiculo_inexistente(
    client,
):
    response = client.post(
        "/alugueis",
        json={
            "id_veiculo": 999,
            "dias": 3,
            "anos_habilitacao": 5,
        },
    )

    assert (
        response.status_code
        == 404
    )

    assert response.json() == {
        "detail": (
            "Veículo não encontrado."
        )
    }


def test_criar_aluguel_sem_anos_habilitacao(
    client,
):
    response = client.post(
        "/alugueis",
        json={
            "id_veiculo": 30,
            "dias": 3,
        },
    )

    assert (
        response.status_code
        == 201
    )


# ================================================================
# SEGURANÇA
# ================================================================


def test_alugueis_sem_token(
    ambiente,
):
    client, _ = ambiente

    response = client.get(
        "/alugueis/me"
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


def test_admin_nao_pode_usar_rota_de_cliente(
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

    response = client.get(
        "/alugueis/me",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert (
        response.status_code
        == 403
    )

    assert response.json() == {
        "detail": (
            "Acesso permitido "
            "apenas para clientes."
        )
    }


def test_usuario_sem_perfil_de_cliente(
    ambiente,
):
    client, container_fake = (
        ambiente
    )

    token = gerar_token(
        container_fake
        .auth_service
        .sem_perfil
    )

    response = client.get(
        "/alugueis/me",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert (
        response.status_code
        == 404
    )

    assert response.json() == {
        "detail": (
            "Cliente vinculado "
            "ao usuário não "
            "foi encontrado."
        )
    }


def test_cliente_desativado_nao_pode_alugar(
    ambiente,
):
    client, container_fake = (
        ambiente
    )

    token = gerar_token(
        container_fake
        .auth_service
        .desativado
    )

    response = client.post(
        "/alugueis",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "id_veiculo": 30,
            "dias": 3,
            "anos_habilitacao": 5,
        },
    )

    assert (
        response.status_code
        == 403
    )

    assert response.json() == {
        "detail": (
            "Cliente desativado."
        )
    }


# ================================================================
# DEVOLUÇÃO
# ================================================================


def test_devolver_veiculo(
    client,
):
    response = client.patch(
        "/alugueis/10/devolver",
        json={
            "km": 250.0,
            "forma_pagamento": 2,
        },
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert (
        dados["veiculo_id"]
        == 10
    )

    assert (
        dados["aluguel"]["status"]
        == "finalizado"
    )

    assert (
        dados["aluguel"]["km"]
        == 250.0
    )

    assert (
        dados["pagamento"]["forma"]
        == "Pix"
    )

    assert (
        dados["pagamento"][
            "parcelas"
        ]
        == 1
    )


def test_devolver_com_credito_parcelado(
    client,
):
    response = client.patch(
        "/alugueis/10/devolver",
        json={
            "km": 100.0,
            "forma_pagamento": 5,
            "parcelas": 6,
        },
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert (
        dados["pagamento"]["forma"]
        == "Crédito 6x"
    )

    assert (
        dados["pagamento"][
            "parcelas"
        ]
        == 6
    )


def test_devolver_com_km_negativa(
    client,
):
    response = client.patch(
        "/alugueis/10/devolver",
        json={
            "km": -10,
            "forma_pagamento": 2,
        },
    )

    assert (
        response.status_code
        == 422
    )


def test_devolver_veiculo_que_nao_pertence(
    client,
):
    response = client.patch(
        "/alugueis/999/devolver",
        json={
            "km": 100,
            "forma_pagamento": 2,
        },
    )

    assert (
        response.status_code
        == 400
    )

    assert response.json() == {
        "detail": (
            "Esse veículo não pertence "
            "aos seus aluguéis ativos."
        )
    }


def test_credito_parcelado_com_parcelas_invalidas(
    client,
):
    response = client.patch(
        "/alugueis/10/devolver",
        json={
            "km": 100,
            "forma_pagamento": 5,
            "parcelas": 1,
        },
    )

    assert (
        response.status_code
        == 422
    )


def test_devolver_com_forma_pagamento_invalida(
    client,
):
    response = client.patch(
        "/alugueis/10/devolver",
        json={
            "km": 100,
            "forma_pagamento": 99,
        },
    )

    assert (
        response.status_code
        == 422
    )


# ================================================================
# ADMIN
# ================================================================


def test_admin_pode_listar_todos_alugueis(
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

    response = client.get(
        "/alugueis",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert len(dados) == 2

    assert (
        dados[0]["id"]
        == 1
    )

    assert (
        dados[1]["id"]
        == 2
    )


def test_admin_pode_listar_alugueis_ativos(
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

    response = client.get(
        "/alugueis/ativos",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert len(dados) == 1

    assert (
        dados[0]["status"]
        == "ativo"
    )

    assert (
        dados[0]["id"]
        == 1
    )


def test_cliente_nao_pode_listar_todos_alugueis(
    client,
):
    response = client.get(
        "/alugueis"
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


def test_listar_todos_alugueis_sem_token(
    ambiente,
):
    client, _ = ambiente

    response = client.get(
        "/alugueis"
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