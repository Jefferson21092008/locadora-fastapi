from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api.dependencias import get_container
from api.main import app

from modulos.excecoes import (
    RegraDeNegocio,
)


JWT_SECRET_TESTE = (
    "locadora-jwt-chave-de-testes-1234567890"
)

MENSAGEM_RECUPERACAO = (
    "Se a conta estiver disponível, "
    "as instruções de recuperação "
    "serão enviadas."
)

TOKEN_RECUPERACAO_TESTE = (
    "token-recuperacao-lucas"
)


class ConfiguracaoFake:
    jwt_secret = JWT_SECRET_TESTE


class UsuarioFake:
    def __init__(
        self,
        id_usuario,
        usuario,
        senha,
        role="cliente",
        ativo=True,
    ):
        self.id = id_usuario
        self.usuario = usuario
        self.senha = senha

        self.role = SimpleNamespace(
            value=role
        )

        self.ativo = ativo


class AuthServiceFake:
    def __init__(self):
        self.usuarios = [
            UsuarioFake(
                id_usuario=1,
                usuario="lucas123",
                senha="senha123",
            ),
            UsuarioFake(
                id_usuario=2,
                usuario="admin",
                senha="admin123",
                role="admin",
            ),
        ]

    def buscar_por_usuario(
        self,
        nome_usuario,
    ):
        for usuario in self.usuarios:
            if (
                usuario.usuario
                == nome_usuario
            ):
                return usuario

        return None

    def buscar_por_id(
        self,
        id_usuario,
    ):
        for usuario in self.usuarios:
            if (
                usuario.id
                == id_usuario
            ):
                return usuario

        return None

    def autenticar(
        self,
        nome_usuario,
        senha,
        role,
    ):
        usuario = (
            self.buscar_por_usuario(
                nome_usuario
            )
        )

        if usuario is None:
            return False

        if not usuario.ativo:
            return False

        if usuario.senha != senha:
            return False

        if (
            usuario.role.value
            != role.value
        ):
            return False

        return True


class RecuperacaoSenhaServiceFake:
    def __init__(
        self,
        auth_service,
    ):
        self.auth_service = (
            auth_service
        )

        self.tokens = {}

    def solicitar_recuperacao(
        self,
        nome_usuario,
    ):
        usuario = (
            self.auth_service
            .buscar_por_usuario(
                nome_usuario
            )
        )

        if (
            usuario is None
            or not usuario.ativo
        ):
            return None

        # Para o teste usamos um token previsível.
        # O service real gera um token aleatório.
        token = (
            TOKEN_RECUPERACAO_TESTE
        )

        # Invalida tokens anteriores.
        self.tokens.clear()

        self.tokens[token] = {
            "usuario_id": usuario.id,
            "usado": False,
        }

        return token

    def redefinir_senha(
        self,
        token,
        nova_senha,
    ):
        registro = (
            self.tokens.get(
                token
            )
        )

        if (
            registro is None
            or registro["usado"]
        ):
            raise RegraDeNegocio(
                "Token de recuperação "
                "inválido ou expirado."
            )

        usuario = (
            self.auth_service
            .buscar_por_id(
                registro["usuario_id"]
            )
        )

        if (
            usuario is None
            or not usuario.ativo
        ):
            raise RegraDeNegocio(
                "Token de recuperação "
                "inválido ou expirado."
            )

        if (
            usuario.senha
            == nova_senha
        ):
            raise RegraDeNegocio(
                "A nova senha deve ser "
                "diferente da senha atual."
            )

        usuario.senha = nova_senha

        registro["usado"] = True

        return (
            "Senha redefinida "
            "com sucesso."
        )


class ContainerFake:
    def __init__(self):
        self.config = (
            ConfiguracaoFake()
        )

        self.auth_service = (
            AuthServiceFake()
        )

        self.recuperacao_senha_service = (
            RecuperacaoSenhaServiceFake(
                self.auth_service
            )
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
        yield client

    app.dependency_overrides.clear()


def fazer_login(
    client,
    usuario="lucas123",
    senha="senha123",
):
    return client.post(
        "/auth/login",
        json={
            "usuario": usuario,
            "senha": senha,
        },
    )


# ================================================================
# LOGIN
# ================================================================


def test_login_com_sucesso(
    client,
):
    response = fazer_login(
        client
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert (
        "access_token"
        in dados
    )

    assert (
        dados["token_type"]
        == "bearer"
    )


def test_login_com_senha_incorreta(
    client,
):
    response = fazer_login(
        client,
        senha="senhaerrada",
    )

    assert (
        response.status_code
        == 401
    )

    assert response.json() == {
        "detail": (
            "Usuário ou senha "
            "incorretos."
        )
    }


def test_login_com_usuario_inexistente(
    client,
):
    response = fazer_login(
        client,
        usuario="naoexiste",
    )

    assert (
        response.status_code
        == 401
    )


def test_login_admin(
    client,
):
    response = fazer_login(
        client,
        usuario="admin",
        senha="admin123",
    )

    assert (
        response.status_code
        == 200
    )

    token = (
        response.json()[
            "access_token"
        ]
    )

    response_me = client.get(
        "/auth/me",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert (
        response_me.status_code
        == 200
    )

    assert (
        response_me.json()["role"]
        == "admin"
    )


# ================================================================
# USUÁRIO ATUAL
# ================================================================


def test_me_sem_token(
    client,
):
    response = client.get(
        "/auth/me"
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


def test_me_com_token_valido(
    client,
):
    login = fazer_login(
        client
    )

    token = (
        login.json()[
            "access_token"
        ]
    )

    response = client.get(
        "/auth/me",
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

    assert dados["id"] == 1

    assert (
        dados["usuario"]
        == "lucas123"
    )

    assert (
        dados["role"]
        == "cliente"
    )

    assert dados["ativo"] is True


def test_me_com_token_invalido(
    client,
):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": (
                "Bearer token-invalido"
            )
        },
    )

    assert (
        response.status_code
        == 401
    )

    assert response.json() == {
        "detail": (
            "Token inválido "
            "ou expirado."
        )
    }


# ================================================================
# RECUPERAÇÃO DE SENHA
# ================================================================


def test_solicitar_recuperacao_usuario_existente(
    client,
):
    response = client.post(
        "/auth/esqueci-senha",
        json={
            "usuario": "lucas123",
        },
    )

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "mensagem": (
            MENSAGEM_RECUPERACAO
        )
    }


def test_solicitar_recuperacao_usuario_inexistente(
    client,
):
    response = client.post(
        "/auth/esqueci-senha",
        json={
            "usuario": "naoexiste",
        },
    )

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "mensagem": (
            MENSAGEM_RECUPERACAO
        )
    }


def test_recuperacao_nao_revela_se_usuario_existe(
    client,
):
    existente = client.post(
        "/auth/esqueci-senha",
        json={
            "usuario": "lucas123",
        },
    )

    inexistente = client.post(
        "/auth/esqueci-senha",
        json={
            "usuario": "naoexiste",
        },
    )

    assert (
        existente.status_code
        == inexistente.status_code
        == 200
    )

    assert (
        existente.json()
        == inexistente.json()
    )


def test_redefinir_senha_com_token_valido(
    client,
):
    client.post(
        "/auth/esqueci-senha",
        json={
            "usuario": "lucas123",
        },
    )

    response = client.post(
        "/auth/redefinir-senha",
        json={
            "token": (
                TOKEN_RECUPERACAO_TESTE
            ),
            "nova_senha": (
                "novaSenha123"
            ),
        },
    )

    assert (
        response.status_code
        == 200
    )

    assert response.json() == {
        "mensagem": (
            "Senha redefinida "
            "com sucesso."
        )
    }


def test_login_funciona_com_nova_senha(
    client,
):
    client.post(
        "/auth/esqueci-senha",
        json={
            "usuario": "lucas123",
        },
    )

    redefinicao = client.post(
        "/auth/redefinir-senha",
        json={
            "token": (
                TOKEN_RECUPERACAO_TESTE
            ),
            "nova_senha": (
                "novaSenha123"
            ),
        },
    )

    assert (
        redefinicao.status_code
        == 200
    )

    login_antigo = fazer_login(
        client,
        senha="senha123",
    )

    assert (
        login_antigo.status_code
        == 401
    )

    login_novo = fazer_login(
        client,
        senha="novaSenha123",
    )

    assert (
        login_novo.status_code
        == 200
    )


def test_redefinir_senha_com_token_invalido(
    client,
):
    response = client.post(
        "/auth/redefinir-senha",
        json={
            "token": "token-invalido",
            "nova_senha": (
                "novaSenha123"
            ),
        },
    )

    assert (
        response.status_code
        == 400
    )

    assert response.json() == {
        "detail": (
            "Token de recuperação "
            "inválido ou expirado."
        )
    }


def test_token_nao_pode_ser_reutilizado(
    client,
):
    client.post(
        "/auth/esqueci-senha",
        json={
            "usuario": "lucas123",
        },
    )

    primeira = client.post(
        "/auth/redefinir-senha",
        json={
            "token": (
                TOKEN_RECUPERACAO_TESTE
            ),
            "nova_senha": (
                "novaSenha123"
            ),
        },
    )

    assert (
        primeira.status_code
        == 200
    )

    segunda = client.post(
        "/auth/redefinir-senha",
        json={
            "token": (
                TOKEN_RECUPERACAO_TESTE
            ),
            "nova_senha": (
                "outraSenha123"
            ),
        },
    )

    assert (
        segunda.status_code
        == 400
    )

    assert segunda.json() == {
        "detail": (
            "Token de recuperação "
            "inválido ou expirado."
        )
    }


def test_redefinir_senha_invalida(
    client,
):
    client.post(
        "/auth/esqueci-senha",
        json={
            "usuario": "lucas123",
        },
    )

    response = client.post(
        "/auth/redefinir-senha",
        json={
            "token": (
                TOKEN_RECUPERACAO_TESTE
            ),
            "nova_senha": (
                "semdigitos"
            ),
        },
    )

    assert (
        response.status_code
        == 422
    )


def test_redefinir_com_mesma_senha_atual(
    client,
):
    client.post(
        "/auth/esqueci-senha",
        json={
            "usuario": "lucas123",
        },
    )

    response = client.post(
        "/auth/redefinir-senha",
        json={
            "token": (
                TOKEN_RECUPERACAO_TESTE
            ),
            "nova_senha": (
                "senha123"
            ),
        },
    )

    assert (
        response.status_code
        == 400
    )

    assert response.json() == {
        "detail": (
            "A nova senha deve ser "
            "diferente da senha atual."
        )
    }
