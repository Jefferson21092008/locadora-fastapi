from types import SimpleNamespace

import pytest

from fastapi.testclient import TestClient
from api.seguranca import (
    criar_token_acesso,
)
from api.dependencias import get_container
from api.main import app
from modulos.excecoes import (
    RecursoNaoEncontrado,
)

class VeiculoFake:
    def __init__(
        self,
        id_veiculo,
        tipo="carro",
        modelo="Civic",
        ano=2025,
        diaria=150.0,
        preco_km=0.40,
        quilometragem=0.0,
        status="disponivel",
        ativo=True,
    ):
        self.id = id_veiculo
        self.TIPO = tipo
        self.modelo = modelo
        self.ano = ano
        self.diaria = diaria
        self.preco_km = preco_km
        self.quilometragem = (
            quilometragem
        )

        self.status = SimpleNamespace(
            value=status
        )

        self.ativo = ativo

JWT_SECRET_TESTE = (
    "locadora-jwt-chave-de-testes-1234567890"
)


class ConfiguracaoFake:
    jwt_secret = JWT_SECRET_TESTE


class UsuarioAdminFake:
    def __init__(self):
        self.id = 1
        self.usuario = "admin"
        self.ativo = True

        self.role = SimpleNamespace(
            value="admin"
        )


class AuthServiceFake:
    def __init__(self):
        self.admin = (
            UsuarioAdminFake()
        )

        self.cliente = (
            SimpleNamespace(
                id=2,
                usuario="cliente",
                ativo=True,
                role=SimpleNamespace(
                    value="cliente"
                ),
            )
        )

    def buscar_por_id(
        self,
        id_usuario,
    ):
        if (
            id_usuario
            == self.admin.id
        ):
            return self.admin

        if (
            id_usuario
            == self.cliente.id
        ):
            return self.cliente

        return None
class VeiculoServiceFake:
    def __init__(self):
        self.veiculos = [
            VeiculoFake(
                id_veiculo=1,
                modelo="Civic",
            ),
            VeiculoFake(
                id_veiculo=2,
                tipo="moto",
                modelo="CG 160",
                diaria=80.0,
                preco_km=0.20,
            ),
        ]

    def listar_todos(self):
        return list(
            self.veiculos
        )

    def buscar_por_id(
        self,
        id_veiculo,
    ):
        for veiculo in self.veiculos:
            if (
                veiculo.id
                == id_veiculo
            ):
                return veiculo

        return None

    def cadastrar(
        self,
        tipo,
        modelo,
        ano,
        diaria,
        preco_km,
    ):
        novo_id = (
            len(self.veiculos)
            + 1
        )

        veiculo = VeiculoFake(
            id_veiculo=novo_id,
            tipo=tipo,
            modelo=modelo,
            ano=ano,
            diaria=diaria,
            preco_km=preco_km,
        )

        self.veiculos.append(
            veiculo
        )

        return veiculo

    def editar(
        self,
        id_veiculo,
        modelo=None,
        ano=None,
        diaria=None,
        preco_km=None,
    ):
        veiculo = self.buscar_por_id(
            id_veiculo
        )

        if veiculo is None:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        if modelo is not None:
            veiculo.modelo = modelo

        if ano is not None:
            veiculo.ano = ano

        if diaria is not None:
            veiculo.diaria = diaria

        if preco_km is not None:
            veiculo.preco_km = (
                preco_km
            )

        return veiculo


    def desativar(
        self,
        id_veiculo,
    ):
        veiculo = self.buscar_por_id(
            id_veiculo
        )

        if veiculo is None:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        veiculo.ativo = False

        veiculo.status = (
            SimpleNamespace(
                value="desativado"
            )
        )

        return veiculo


    def reativar(
        self,
        id_veiculo,
    ):
        veiculo = self.buscar_por_id(
            id_veiculo
        )

        if veiculo is None:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        veiculo.ativo = True

        veiculo.status = (
            SimpleNamespace(
                value="disponivel"
            )
        )

        return veiculo

class ContainerFake:
    def __init__(self):
        self.config = ConfiguracaoFake()

        self.auth_service = (
            AuthServiceFake()
        )

        self.veiculo_service = (
            VeiculoServiceFake()
        )

@pytest.fixture
def client():
    container_fake = (
        ContainerFake()
    )

    app.dependency_overrides[
        get_container
    ] = lambda: container_fake

    with TestClient(app) as client:
        client.headers.update(
            {
                "Authorization": (
                    "Bearer "
                    + criar_token_acesso(
                        usuario=(
                            container_fake
                            .auth_service
                            .admin
                        ),
                        secret=(
                            container_fake
                            .config
                            .jwt_secret
                        ),
                    )
                )
            }
        )

        yield client

    app.dependency_overrides.clear()

def test_listar_veiculos(
    client,
):
    response = client.get(
        "/veiculos"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert len(dados) == 2

    assert (
        dados[0]["modelo"]
        == "Civic"
    )

    assert (
        dados[1]["modelo"]
        == "CG 160"
    )


def test_buscar_veiculo_por_id(
    client,
):
    response = client.get(
        "/veiculos/1"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert dados["id"] == 1

    assert (
        dados["modelo"]
        == "Civic"
    )


def test_buscar_veiculo_inexistente(
    client,
):
    response = client.get(
        "/veiculos/999"
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


def test_cadastrar_veiculo(
    client,
):
    response = client.post(
        "/veiculos",
        json={
            "tipo": "carro",
            "modelo": "Supra",
            "ano": 2025,
            "diaria": 250.0,
            "preco_km": 0.50,
        },
    )

    assert (
        response.status_code
        == 201
    )

    dados = response.json()

    assert dados["id"] == 3

    assert (
        dados["modelo"]
        == "Supra"
    )

    assert (
        dados["status"]
        == "disponivel"
    )

    assert dados["ativo"] is True


def test_cadastrar_com_ano_invalido_para_pydantic(
    client,
):
    response = client.post(
        "/veiculos",
        json={
            "tipo": "carro",
            "modelo": "Supra",
            "ano": "banana",
            "diaria": 250.0,
            "preco_km": 0.50,
        },
    )

    assert (
        response.status_code
        == 422
    )

def test_editar_veiculo(
    client,
):
    response = client.patch(
        "/veiculos/1",
        json={
            "diaria": 200.0
        },
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert dados["id"] == 1

    assert (
        dados["diaria"]
        == 200.0
    )


def test_editar_veiculo_inexistente(
    client,
):
    response = client.patch(
        "/veiculos/999",
        json={
            "diaria": 200.0
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


def test_desativar_veiculo(
    client,
):
    response = client.patch(
        "/veiculos/1/desativar"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert dados["ativo"] is False

    assert (
        dados["status"]
        == "desativado"
    )


def test_reativar_veiculo(
    client,
):
    client.patch(
        "/veiculos/1/desativar"
    )

    response = client.patch(
        "/veiculos/1/reativar"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert dados["ativo"] is True

    assert (
        dados["status"]
        == "disponivel"
    )


def test_desativar_veiculo_inexistente(
    client,
):
    response = client.patch(
        "/veiculos/999/desativar"
    )

    assert (
        response.status_code
        == 404
    )


def test_reativar_veiculo_inexistente(
    client,
):
    response = client.patch(
        "/veiculos/999/reativar"
    )

    assert (
        response.status_code
        == 404
    )

def test_cadastrar_veiculo_sem_token(
    client,
):
    authorization = (
        client.headers.pop(
            "Authorization"
        )
    )

    response = client.post(
        "/veiculos",
        json={
            "tipo": "carro",
            "modelo": "Civic",
            "ano": 2025,
            "diaria": 150.0,
            "preco_km": 0.4,
        },
    )

    client.headers[
        "Authorization"
    ] = authorization

    assert (
        response.status_code
        == 401
    )

def test_cliente_nao_pode_cadastrar_veiculo(
    client,
):
    usuario_cliente = (
        SimpleNamespace(
            id=2,
            usuario="cliente",
            ativo=True,
            role=SimpleNamespace(
                value="cliente"
            ),
        )
    )

    token = criar_token_acesso(
        usuario=usuario_cliente,
        secret=JWT_SECRET_TESTE,
    )

    response = client.post(
        "/veiculos",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        json={
            "tipo": "carro",
            "modelo": "Civic",
            "ano": 2025,
            "diaria": 150.0,
            "preco_km": 0.4,
        },
    )

    assert (
        response.status_code
        == 403
    )

def criar_token_cliente():
    usuario = SimpleNamespace(
        id=2,
        usuario="cliente",
        ativo=True,
        role=SimpleNamespace(
            value="cliente"
        ),
    )

    return criar_token_acesso(
        usuario=usuario,
        secret=(
            "chave-super-secreta-para-testes"
        ),
    )
