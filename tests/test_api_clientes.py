from types import SimpleNamespace

import pytest

from fastapi.testclient import (
    TestClient,
)

from api.dependencias import (
    get_container,
)

from api.main import app

from api.seguranca import (
    criar_token_acesso,
)


from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)


JWT_SECRET_TESTE = (
    "locadora-jwt-chave-de-testes-1234567890"
)


class ConfiguracaoFake:
    jwt_secret = JWT_SECRET_TESTE


class ClienteFake:
    def __init__(
        self,
        id_cliente,
        nome,
        usuario,
        email,
        ativo=True,
    ):
        self.id = id_cliente
        self.nome = nome
        self.usuario = usuario
        self.email = email
        self.ativo = ativo


class UsuarioAdminFake:
    def __init__(self):
        self.id = 100
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
                id=200,
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


class ClienteServiceFake:
    def __init__(self):
        self.clientes = [
            ClienteFake(
                id_cliente=1,
                nome="Lucas",
                usuario="lucas123",
                email="lucas@email.com",
            ),
            ClienteFake(
                id_cliente=2,
                nome="Maria",
                usuario="maria123",
                email="maria@email.com",
            ),
        ]

    def listar_clientes(
        self,
    ):
        return self.clientes

    def buscar_por_id(
        self,
        id_cliente,
    ):
        for cliente in self.clientes:
            if (
                cliente.id
                == id_cliente
            ):
                return cliente

        return None

    def criar_conta(
        self,
        nome,
        usuario,
        email,
        senha,
    ):
        for cliente in self.clientes:
            if (
                cliente.usuario
                == usuario
            ):
                raise RegraDeNegocio(
                    "Usuário já cadastrado."
                )

            if (
                cliente.email
                == email
            ):
                raise RegraDeNegocio(
                    "E-mail já cadastrado."
                )

        novo_id = (
            max(
                cliente.id
                for cliente
                in self.clientes
            )
            + 1
        )

        novo_cliente = ClienteFake(
            id_cliente=novo_id,
            nome=nome,
            usuario=usuario,
            email=email,
        )

        self.clientes.append(
            novo_cliente
        )

        return novo_cliente

    def desativar(
        self,
        id_cliente,
    ):
        cliente = self.buscar_por_id(
            id_cliente
        )

        if cliente is None:
            raise RecursoNaoEncontrado(
                "Cliente não encontrado."
            )

        if not cliente.ativo:
            raise RegraDeNegocio(
                "Cliente já está desativado."
            )

        cliente.ativo = False
        return cliente

    def reativar(
        self,
        id_cliente,
    ):
        cliente = self.buscar_por_id(
            id_cliente
        )

        if cliente is None:
            raise RecursoNaoEncontrado(
                "Cliente não encontrado."
            )

        if cliente.ativo:
            raise RegraDeNegocio(
                "Cliente já está ativo."
            )

        cliente.ativo = True
        return cliente


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


@pytest.fixture
def client():
    container_fake = (
        ContainerFake()
    )

    app.dependency_overrides[
        get_container
    ] = lambda: container_fake

    token_admin = criar_token_acesso(
        usuario=(
            container_fake
            .auth_service
            .admin
        ),
        secret=JWT_SECRET_TESTE,
    )

    with TestClient(app) as client:
        client.headers.update(
            {
                "Authorization": (
                    f"Bearer {token_admin}"
                )
            }
        )

        yield client

    app.dependency_overrides.clear()


def test_listar_clientes(
    client,
):
    response = client.get(
        "/clientes"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert len(dados) == 2

    assert (
        dados[0]["nome"]
        == "Lucas"
    )

    assert (
        dados[1]["nome"]
        == "Maria"
    )


def test_buscar_cliente_por_id(
    client,
):
    response = client.get(
        "/clientes/1"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert dados["id"] == 1

    assert (
        dados["usuario"]
        == "lucas123"
    )


def test_buscar_cliente_inexistente(
    client,
):
    response = client.get(
        "/clientes/999"
    )

    assert (
        response.status_code
        == 404
    )

    assert response.json() == {
        "detail": (
            "Cliente não encontrado."
        )
    }


def test_criar_cliente(
    client,
):
    response = client.post(
        "/clientes",
        json={
            "nome": "Pedro",
            "usuario": "pedro123",
            "email": (
                "pedro@email.com"
            ),
            "senha": "pedro123",
        },
    )

    assert (
        response.status_code
        == 201
    )

    dados = response.json()

    assert (
        dados["nome"]
        == "Pedro"
    )

    assert (
        dados["usuario"]
        == "pedro123"
    )

    assert (
        dados["email"]
        == "pedro@email.com"
    )

    assert dados["ativo"] is True

    assert "senha" not in dados


def test_criar_cliente_com_usuario_duplicado(
    client,
):
    response = client.post(
        "/clientes",
        json={
            "nome": "Outro Lucas",
            "usuario": "lucas123",
            "email": (
                "outro@email.com"
            ),
            "senha": "senha123",
        },
    )

    assert (
        response.status_code
        == 400
    )

    assert response.json() == {
        "detail": (
            "Usuário já cadastrado."
        )
    }


def test_criar_cliente_com_email_duplicado(
    client,
):
    response = client.post(
        "/clientes",
        json={
            "nome": "Outro Lucas",
            "usuario": "outrolucas",
            "email": (
                "lucas@email.com"
            ),
            "senha": "senha123",
        },
    )

    assert (
        response.status_code
        == 400
    )

    assert response.json() == {
        "detail": (
            "E-mail já cadastrado."
        )
    }


def test_desativar_cliente(
    client,
):
    response = client.patch(
        "/clientes/1/desativar"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert dados["id"] == 1

    assert (
        dados["ativo"]
        is False
    )


def test_reativar_cliente(
    client,
):
    client.patch(
        "/clientes/1/desativar"
    )

    response = client.patch(
        "/clientes/1/reativar"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert dados["id"] == 1

    assert (
        dados["ativo"]
        is True
    )


def test_desativar_cliente_inexistente(
    client,
):
    response = client.patch(
        "/clientes/999/desativar"
    )

    assert (
        response.status_code
        == 404
    )

    assert response.json() == {
        "detail": (
            "Cliente não encontrado."
        )
    }


def test_reativar_cliente_inexistente(
    client,
):
    response = client.patch(
        "/clientes/999/reativar"
    )

    assert (
        response.status_code
        == 404
    )

    assert response.json() == {
        "detail": (
            "Cliente não encontrado."
        )
    }


def test_listar_clientes_sem_token(
    client,
):
    authorization = (
        client.headers.pop(
            "Authorization"
        )
    )

    response = client.get(
        "/clientes"
    )

    client.headers[
        "Authorization"
    ] = authorization

    assert (
        response.status_code
        == 401
    )


def test_cliente_nao_pode_listar_clientes(
    client,
):
    usuario_cliente = (
        SimpleNamespace(
            id=200,
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

    response = client.get(
        "/clientes",
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
            "apenas para "
            "administradores."
        )
    }


def test_criar_cliente_sem_token(
    client,
):
    authorization = (
        client.headers.pop(
            "Authorization"
        )
    )

    response = client.post(
        "/clientes",
        json={
            "nome": "Pedro",
            "usuario": "pedro123",
            "email": (
                "pedro@email.com"
            ),
            "senha": "pedro123",
        },
    )

    client.headers[
        "Authorization"
    ] = authorization

    assert (
        response.status_code
        == 201
    )

    dados = response.json()

    assert (
        dados["usuario"]
        == "pedro123"
    )

    assert "senha" not in dados