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

class ClienteFake:
    def __init__(
        self,
        id_cliente,
        usuario_id,
        usuario,
        ativo=True,
    ):
        self.id = id_cliente
        self.usuario_id = usuario_id
        self.usuario = usuario
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

class ClienteServiceFake:
    def __init__(
        self,
        auth_service,
    ):
        self.auth_service = (
            auth_service
        )

        self.clientes = [
            ClienteFake(
                id_cliente=1,
                usuario_id=1,
                usuario="lucas123",
            ),
        ]

    def buscar_por_usuario_id(
        self,
        usuario_id,
    ):
        for cliente in self.clientes:
            if (
                cliente.usuario_id
                == usuario_id
            ):
                return cliente

        return None

    def renomear_usuario(
        self,
        cliente,
        novo_usuario,
        senha_atual,
    ):
        conta = (
            self.auth_service
            .buscar_por_id(
                cliente.usuario_id
            )
        )

        if conta is None:
            raise RegraDeNegocio(
                "Conta de usuário "
                "não encontrada."
            )

        if conta.senha != senha_atual:
            raise RegraDeNegocio(
                "Senha atual incorreta."
            )

        novo_usuario = str(
            novo_usuario
        ).strip()

        if (
            novo_usuario.lower()
            == conta.usuario.lower()
        ):
            raise RegraDeNegocio(
                "O novo usuário deve ser "
                "diferente do atual."
            )

        usuario_existente = (
            self.auth_service
            .buscar_por_usuario(
                novo_usuario
            )
        )

        if usuario_existente is not None:
            raise RegraDeNegocio(
                "Esse usuário já existe."
            )

        conta.usuario = novo_usuario
        cliente.usuario = novo_usuario

        return cliente

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

        self.cliente_service = (
            ClienteServiceFake(
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

def obter_token(
    client,
    usuario="lucas123",
    senha="senha123",
):
    resposta = fazer_login(
        client,
        usuario=usuario,
        senha=senha,
    )

    assert resposta.status_code == 200

    return resposta.json()[
        "access_token"
    ]

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

def test_cliente_pode_alterar_usuario(
    client,
):
    token = obter_token(
        client
    )

    resposta = client.patch(
        "/auth/me/usuario",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
        json={
            "novo_usuario": (
                "lucas.novo"
            ),
            "senha_atual": (
                "senha123"
            ),
        },
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert (
        dados["usuario"]
        == "lucas.novo"
    )

    assert dados["role"] == "cliente"


def test_token_continua_valido_apos_renomear(
    client,
):
    token = obter_token(
        client
    )

    resposta = client.patch(
        "/auth/me/usuario",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
        json={
            "novo_usuario": (
                "lucas.novo"
            ),
            "senha_atual": (
                "senha123"
            ),
        },
    )

    assert resposta.status_code == 200

    resposta_me = client.get(
        "/auth/me",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
    )

    assert resposta_me.status_code == 200

    assert (
        resposta_me.json()["usuario"]
        == "lucas.novo"
    )


def test_usuario_antigo_nao_faz_login_apos_renomear(
    client,
):
    token = obter_token(
        client
    )

    resposta = client.patch(
        "/auth/me/usuario",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
        json={
            "novo_usuario": (
                "lucas.novo"
            ),
            "senha_atual": (
                "senha123"
            ),
        },
    )

    assert resposta.status_code == 200

    login_antigo = fazer_login(
        client,
        usuario="lucas123",
        senha="senha123",
    )

    assert (
        login_antigo.status_code
        == 401
    )

    login_novo = fazer_login(
        client,
        usuario="lucas.novo",
        senha="senha123",
    )

    assert (
        login_novo.status_code
        == 200
    )


def test_alterar_usuario_exige_senha_correta(
    client,
):
    token = obter_token(
        client
    )

    resposta = client.patch(
        "/auth/me/usuario",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
        json={
            "novo_usuario": (
                "lucas.novo"
            ),
            "senha_atual": (
                "senha-errada"
            ),
        },
    )

    assert resposta.status_code == 400


def test_nao_permite_usuario_ja_existente(
    client,
):
    token = obter_token(
        client
    )

    resposta = client.patch(
        "/auth/me/usuario",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
        json={
            "novo_usuario": "admin",
            "senha_atual": "senha123",
        },
    )

    assert resposta.status_code == 400


def test_nao_permite_mesmo_usuario_atual(
    client,
):
    token = obter_token(
        client
    )

    resposta = client.patch(
        "/auth/me/usuario",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
        json={
            "novo_usuario": (
                "lucas123"
            ),
            "senha_atual": (
                "senha123"
            ),
        },
    )

    assert resposta.status_code == 400


def test_alterar_usuario_exige_autenticacao(
    client,
):
    resposta = client.patch(
        "/auth/me/usuario",
        json={
            "novo_usuario": (
                "lucas.novo"
            ),
            "senha_atual": (
                "senha123"
            ),
        },
    )

    assert resposta.status_code == 401


def test_admin_nao_pode_usar_rota_de_cliente(
    client,
):
    token = obter_token(
        client,
        usuario="admin",
        senha="admin123",
    )

    resposta = client.patch(
        "/auth/me/usuario",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
        json={
            "novo_usuario": (
                "novo.admin"
            ),
            "senha_atual": (
                "admin123"
            ),
        },
    )

    assert resposta.status_code == 403

def test_login_bloqueia_apos_cinco_falhas(
    client,
):
    for _ in range(5):
        resposta = fazer_login(
            client,
            senha="senha-errada",
        )

        assert resposta.status_code == 401

    bloqueada = fazer_login(
        client,
        senha="senha-errada",
    )

    assert bloqueada.status_code == 429

    assert bloqueada.json() == {
        "detail": (
            "Muitas tentativas. "
            "Tente novamente mais tarde."
        )
    }


def test_login_correto_limpa_tentativas(
    client,
):
    for _ in range(3):
        resposta = fazer_login(
            client,
            senha="senha-errada",
        )

        assert resposta.status_code == 401

    sucesso = fazer_login(
        client,
        senha="senha123",
    )

    assert sucesso.status_code == 200

    for _ in range(5):
        resposta = fazer_login(
            client,
            senha="senha-errada",
        )

        assert resposta.status_code == 401

    bloqueada = fazer_login(
        client,
        senha="senha-errada",
    )

    assert bloqueada.status_code == 429

def test_recuperacao_bloqueia_apos_tres_solicitacoes(
    client,
):
    for _ in range(3):
        resposta = client.post(
            "/auth/esqueci-senha",
            json={
                "usuario": "lucas123",
            },
        )

        assert resposta.status_code == 200

    bloqueada = client.post(
        "/auth/esqueci-senha",
        json={
            "usuario": "lucas123",
        },
    )

    assert bloqueada.status_code == 429


def test_redefinicao_bloqueia_apos_cinco_tentativas(
    client,
):
    for _ in range(5):
        resposta = client.post(
            "/auth/redefinir-senha",
            json={
                "token": "token-invalido",
                "nova_senha": "novaSenha123",
            },
        )

        assert resposta.status_code == 400

    bloqueada = client.post(
        "/auth/redefinir-senha",
        json={
            "token": "token-invalido",
            "nova_senha": "novaSenha123",
        },
    )

    assert bloqueada.status_code == 429

def test_rate_limit_separa_ips_encaminhados(
    client,
):
    for _ in range(5):
        resposta = client.post(
            "/auth/login",
            headers={
                "X-Forwarded-For": (
                    "198.51.100.10"
                ),
            },
            json={
                "usuario": "lucas123",
                "senha": "senha-errada",
            },
        )

        assert resposta.status_code == 401

    bloqueada = client.post(
        "/auth/login",
        headers={
            "X-Forwarded-For": (
                "198.51.100.10"
            ),
        },
        json={
            "usuario": "lucas123",
            "senha": "senha-errada",
        },
    )

    assert bloqueada.status_code == 429

    outro_ip = client.post(
        "/auth/login",
        headers={
            "X-Forwarded-For": (
                "203.0.113.20"
            ),
        },
        json={
            "usuario": "lucas123",
            "senha": "senha-errada",
        },
    )

    assert outro_ip.status_code == 401