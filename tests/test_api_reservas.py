from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api.dependencias import get_container
from api.main import app
from api.seguranca import criar_token_acesso
from modulos.clientes import Cliente
from modulos.consultas import ResultadoPaginado
from modulos.reservas import Reserva


JWT_SECRET_TESTE = (
    "locadora-jwt-chave-de-testes-1234567890"
)


class ConfiguracaoFake:
    jwt_secret = JWT_SECRET_TESTE


class UsuarioFake:
    def __init__(
        self,
        id_usuario,
        usuario,
        role,
    ):
        self.id = id_usuario
        self.usuario = usuario
        self.ativo = True
        self.role = SimpleNamespace(
            value=role
        )


class AuthServiceFake:
    def __init__(self):
        self.admin = UsuarioFake(
            100,
            "admin",
            "admin",
        )
        self.cliente = UsuarioFake(
            200,
            "ana123",
            "cliente",
        )

    def buscar_por_id(
        self,
        id_usuario,
    ):
        for usuario in (
            self.admin,
            self.cliente,
        ):
            if usuario.id == id_usuario:
                return usuario

        return None


class ClienteServiceFake:
    def __init__(self):
        self.cliente = Cliente(
            id_cliente=1,
            nome="Ana Souza",
            usuario="ana123",
            email="ana@example.com",
            usuario_id=200,
        )

    def buscar_por_usuario_id(
        self,
        usuario_id,
    ):
        if usuario_id == 200:
            return self.cliente

        return None


class ReservaServiceFake:
    def __init__(self):
        inicio = (
            date.today()
            + timedelta(days=5)
        )
        self.reservas = [
            Reserva(
                id_reserva=1,
                cliente_id=1,
                cliente_usuario="ana123",
                cliente_nome="Ana Souza",
                veiculo_id=10,
                veiculo_tipo="Carro",
                veiculo_modelo="Civic",
                data_inicio=(
                    inicio.isoformat()
                ),
                data_fim=(
                    inicio
                    + timedelta(days=3)
                ).isoformat(),
            )
        ]

    def criar(
        self,
        cliente,
        id_veiculo,
        data_inicio,
        data_fim,
    ):
        reserva = Reserva(
            id_reserva=(
                len(self.reservas)
                + 1
            ),
            cliente_id=cliente.id,
            cliente_usuario=(
                cliente.usuario
            ),
            cliente_nome=cliente.nome,
            veiculo_id=id_veiculo,
            veiculo_tipo="Carro",
            veiculo_modelo="Corolla",
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        self.reservas.append(
            reserva
        )
        return reserva

    def listar_todas(self):
        return list(
            self.reservas
        )

    def listar_do_cliente(
        self,
        cliente,
    ):
        return [
            reserva
            for reserva
            in self.reservas
            if reserva.cliente_id
            == cliente.id
        ]

    def consultar(
        self,
        cliente_id=None,
        **_kwargs,
    ):
        items = list(
            self.reservas
        )

        if cliente_id is not None:
            items = [
                reserva
                for reserva in items
                if reserva.cliente_id
                == cliente_id
            ]

        return ResultadoPaginado(
            items=items,
            total=len(items),
            resumo={
                "total": len(items),
                "ativas": len(items),
                "expiradas": 0,
                "canceladas": 0,
                "convertidas": 0,
            },
        )

    def cancelar_do_cliente(
        self,
        id_reserva,
        cliente,
    ):
        reserva = next(
            reserva
            for reserva
            in self.reservas
            if reserva.id
            == id_reserva
            and reserva.cliente_id
            == cliente.id
        )
        reserva.cancelar()
        return reserva

    def cancelar_admin(
        self,
        id_reserva,
    ):
        reserva = next(
            reserva
            for reserva
            in self.reservas
            if reserva.id
            == id_reserva
        )
        reserva.cancelar()
        return reserva


class ContainerFake:
    def __init__(self):
        self.config = ConfiguracaoFake()
        self.auth_service = (
            AuthServiceFake()
        )
        self.cliente_service = (
            ClienteServiceFake()
        )
        self.reserva_service = (
            ReservaServiceFake()
        )
        self.auditoria_service = (
            SimpleNamespace(
                registrar=(
                    lambda **_kwargs: None
                )
            )
        )


def gerar_token(usuario):
    return criar_token_acesso(
        usuario=usuario,
        secret=JWT_SECRET_TESTE,
    )


@pytest.fixture
def ambiente():
    container = ContainerFake()
    app.dependency_overrides[
        get_container
    ] = lambda: container

    with TestClient(app) as client:
        yield client, container

    app.dependency_overrides.clear()


def autorizar(
    client,
    usuario,
):
    token = gerar_token(
        usuario
    )
    client.headers.update(
        {
            "Authorization": (
                f"Bearer {token}"
            )
        }
    )


def test_cliente_cria_reserva(
    ambiente,
):
    client, container = ambiente
    autorizar(
        client,
        container.auth_service.cliente,
    )
    inicio = (
        date.today()
        + timedelta(days=10)
    )

    response = client.post(
        "/api/v1/reservas",
        json={
            "id_veiculo": 20,
            "data_inicio": (
                inicio.isoformat()
            ),
            "data_fim": (
                inicio
                + timedelta(days=2)
            ).isoformat(),
        },
    )

    assert response.status_code == 201
    assert response.json()[
        "cliente_id"
    ] == 1
    assert response.json()[
        "veiculo_id"
    ] == 20


def test_admin_lista_todas_as_reservas(
    ambiente,
):
    client, container = ambiente
    autorizar(
        client,
        container.auth_service.admin,
    )

    response = client.get(
        "/api/v1/reservas"
    )

    assert response.status_code == 200
    assert len(
        response.json()
    ) == 1


def test_cliente_nao_lista_reservas_administrativas(
    ambiente,
):
    client, container = ambiente
    autorizar(
        client,
        container.auth_service.cliente,
    )

    response = client.get(
        "/api/v1/reservas"
    )

    assert response.status_code == 403


def test_cliente_consulta_apenas_as_proprias_reservas(
    ambiente,
):
    client, container = ambiente
    autorizar(
        client,
        container.auth_service.cliente,
    )

    response = client.get(
        "/api/v1/reservas/me/consulta"
    )

    assert response.status_code == 200
    dados = response.json()
    assert dados["total"] == 1
    assert dados["items"][0][
        "cliente_usuario"
    ] == "ana123"


def test_cliente_cancela_a_propria_reserva(
    ambiente,
):
    client, container = ambiente
    autorizar(
        client,
        container.auth_service.cliente,
    )

    response = client.patch(
        "/api/v1/reservas/me/1/cancelar"
    )

    assert response.status_code == 200
    assert response.json()[
        "status"
    ] == "cancelada"
