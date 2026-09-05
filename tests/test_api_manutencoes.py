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
# MANUTENÇÃO FAKE
# ================================================================


class ManutencaoFake:
    def __init__(
        self,
        id_manutencao,
        veiculo_id,
        motivo,
        quilometragem,
        custo=0.0,
        data_inicio="2026-08-27",
        data_fim=None,
        status="ativa",
    ):
        self.id = id_manutencao
        self.veiculo_id = veiculo_id

        self.motivo = motivo

        self.quilometragem = float(
            quilometragem
        )

        self.custo = float(
            custo
        )

        self.data_inicio = (
            data_inicio
        )

        self.data_fim = data_fim

        self.status = status

    @property
    def ativa(self):
        return (
            self.status
            == "ativa"
        )


# ================================================================
# AUTH SERVICE FAKE
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
            usuario="lucas123",
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
# MANUTENÇÃO SERVICE FAKE
# ================================================================


class ManutencaoServiceFake:
    def __init__(self):
        self.manutencoes = [
            ManutencaoFake(
                id_manutencao=1,
                veiculo_id=10,
                motivo=(
                    "Revisão preventiva"
                ),
                quilometragem=50000,
                status="ativa",
            ),

            ManutencaoFake(
                id_manutencao=2,
                veiculo_id=20,
                motivo=(
                    "Troca de pneus"
                ),
                quilometragem=70000,
                custo=1200,
                data_fim="2026-08-20",
                status="finalizada",
            ),
        ]

    # ============================================================
    # CONSULTAS
    # ============================================================

    def listar_manutencoes(
        self,
    ):
        return list(
            self.manutencoes
        )

    def listar_ativas(
        self,
    ):
        return [
            manutencao
            for manutencao
            in self.manutencoes
            if manutencao.ativa
        ]

    def listar_por_veiculo(
        self,
        id_veiculo,
    ):
        return [
            manutencao
            for manutencao
            in self.manutencoes
            if (
                manutencao.veiculo_id
                == id_veiculo
            )
        ]

    def buscar_ativa_por_veiculo(
        self,
        id_veiculo,
    ):
        for manutencao in (
            self.manutencoes
        ):
            if (
                manutencao.veiculo_id
                == id_veiculo
                and manutencao.ativa
            ):
                return manutencao

        return None

    # ============================================================
    # ABRIR
    # ============================================================

    def abrir(
        self,
        id_veiculo,
        motivo,
    ):
        if id_veiculo == 999:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        manutencao_ativa = (
            self.buscar_ativa_por_veiculo(
                id_veiculo
            )
        )

        if manutencao_ativa is not None:
            raise RegraDeNegocio(
                "Esse veículo já possui "
                "uma manutenção ativa."
            )

        motivo = str(
            motivo
        ).strip()

        if not motivo:
            raise RegraDeNegocio(
                "O motivo da manutenção "
                "não pode ficar vazio."
            )

        nova_manutencao = (
            ManutencaoFake(
                id_manutencao=(
                    len(
                        self.manutencoes
                    )
                    + 1
                ),
                veiculo_id=id_veiculo,
                motivo=motivo,
                quilometragem=35000,
            )
        )

        self.manutencoes.append(
            nova_manutencao
        )

        return nova_manutencao

    # ============================================================
    # FINALIZAR
    # ============================================================

    def finalizar(
        self,
        id_veiculo,
        custo,
        data_fim=None,
    ):
        if id_veiculo == 999:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        manutencao = (
            self.buscar_ativa_por_veiculo(
                id_veiculo
            )
        )

        if manutencao is None:
            raise RecursoNaoEncontrado(
                "Esse veículo não possui "
                "manutenção ativa."
            )

        try:
            custo = float(
                custo
            )

        except (
            TypeError,
            ValueError,
        ):
            raise RegraDeNegocio(
                "Custo inválido."
            )

        if custo < 0:
            raise RegraDeNegocio(
                "O custo não pode ser negativo."
            )

        manutencao.custo = custo

        manutencao.data_fim = (
            data_fim
            or "2026-08-27"
        )

        manutencao.status = (
            "finalizada"
        )

        return manutencao


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

        self.manutencao_service = (
            ManutencaoServiceFake()
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
# LISTAGEM
# ================================================================


def test_admin_pode_listar_manutencoes(
    admin_client,
):
    response = admin_client.get(
        "/manutencoes"
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


def test_admin_pode_listar_manutencoes_ativas(
    admin_client,
):
    response = admin_client.get(
        "/manutencoes/ativas"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert len(dados) == 1

    assert (
        dados[0]["id"]
        == 1
    )

    assert (
        dados[0]["status"]
        == "ativa"
    )


def test_admin_pode_ver_historico_do_veiculo(
    admin_client,
):
    response = admin_client.get(
        "/manutencoes/veiculo/20"
    )

    assert (
        response.status_code
        == 200
    )

    dados = response.json()

    assert len(dados) == 1

    assert (
        dados[0]["veiculo_id"]
        == 20
    )

    assert (
        dados[0]["status"]
        == "finalizada"
    )


# ================================================================
# ABERTURA
# ================================================================


def test_admin_pode_abrir_manutencao(
    admin_client,
):
    response = admin_client.post(
        "/manutencoes",
        json={
            "id_veiculo": 30,
            "motivo": (
                "Troca de óleo"
            ),
        },
    )

    assert (
        response.status_code
        == 201
    )

    dados = response.json()

    assert (
        dados["id"]
        == 3
    )

    assert (
        dados["veiculo_id"]
        == 30
    )

    assert (
        dados["motivo"]
        == "Troca de óleo"
    )

    assert (
        dados["status"]
        == "ativa"
    )

    assert (
        dados["custo"]
        == 0.0
    )

    assert (
        dados["data_fim"]
        is None
    )


def test_nao_pode_abrir_manutencao_em_veiculo_inexistente(
    admin_client,
):
    response = admin_client.post(
        "/manutencoes",
        json={
            "id_veiculo": 999,
            "motivo": "Revisão",
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


def test_nao_pode_abrir_duas_manutencoes_ativas(
    admin_client,
):
    response = admin_client.post(
        "/manutencoes",
        json={
            "id_veiculo": 10,
            "motivo": (
                "Outro reparo"
            ),
        },
    )

    assert (
        response.status_code
        == 400
    )

    assert response.json() == {
        "detail": (
            "Esse veículo já possui "
            "uma manutenção ativa."
        )
    }


def test_nao_pode_abrir_com_motivo_vazio(
    admin_client,
):
    response = admin_client.post(
        "/manutencoes",
        json={
            "id_veiculo": 30,
            "motivo": "   ",
        },
    )

    assert (
        response.status_code
        == 422
    )


# ================================================================
# FINALIZAÇÃO
# ================================================================


def test_admin_pode_finalizar_manutencao(
    admin_client,
):
    response = admin_client.patch(
        "/manutencoes/10/finalizar",
        json={
            "custo": 850.50
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
        dados["status"]
        == "finalizada"
    )

    assert (
        dados["custo"]
        == 850.50
    )

    assert (
        dados["data_fim"]
        is not None
    )


def test_nao_pode_finalizar_com_custo_negativo(
    admin_client,
):
    response = admin_client.patch(
        "/manutencoes/10/finalizar",
        json={
            "custo": -100
        },
    )

    assert (
        response.status_code
        == 422
    )


def test_nao_pode_finalizar_sem_manutencao_ativa(
    admin_client,
):
    response = admin_client.patch(
        "/manutencoes/20/finalizar",
        json={
            "custo": 500
        },
    )

    assert (
        response.status_code
        == 404
    )

    assert response.json() == {
        "detail": (
            "Esse veículo não possui "
            "manutenção ativa."
        )
    }


def test_finalizar_veiculo_inexistente(
    admin_client,
):
    response = admin_client.patch(
        "/manutencoes/999/finalizar",
        json={
            "custo": 500
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


# ================================================================
# SEGURANÇA
# ================================================================


def test_cliente_nao_pode_acessar_manutencoes(
    cliente_client,
):
    response = cliente_client.get(
        "/manutencoes"
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


def test_manutencoes_sem_token(
    ambiente,
):
    client, _ = ambiente

    response = client.get(
        "/manutencoes"
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