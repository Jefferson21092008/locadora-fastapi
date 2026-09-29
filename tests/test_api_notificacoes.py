from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api.dependencias import get_container
from api.main import app
from api.seguranca import criar_token_acesso
from modulos.consultas import ResultadoPaginado
from modulos.notificacoes import Notificacao


JWT_SECRET_TESTE = "locadora-jwt-chave-de-testes-1234567890"


class ConfiguracaoFake:
    jwt_secret = JWT_SECRET_TESTE


class UsuarioFake:
    def __init__(self, id_usuario, usuario, role):
        self.id = id_usuario
        self.usuario = usuario
        self.ativo = True
        self.role = SimpleNamespace(value=role)


class AuthServiceFake:
    def __init__(self):
        self.admin = UsuarioFake(1, "admin", "admin")
        self.cliente = UsuarioFake(2, "cliente", "cliente")

    def buscar_por_id(self, id_usuario):
        return {
            1: self.admin,
            2: self.cliente,
        }.get(id_usuario)


class NotificacaoServiceFake:
    def __init__(self):
        self.item = Notificacao(
            id_notificacao=7,
            usuario_id=2,
            tipo="reserva_proxima",
            titulo="Reserva amanhã",
            mensagem="Seu veículo está reservado.",
            chave_deduplicacao="usuario:2:reserva:10:d1",
            referencia_tipo="reserva",
            referencia_id=10,
        )

    def processar_usuario(self, usuario):
        return {
            "criadas": 1,
            "emails_enviados": 0,
            "emails_falharam": 0,
        }

    def consultar(self, usuario_id, **kwargs):
        items = [self.item] if usuario_id == 2 else []
        return ResultadoPaginado(
            items=items,
            total=len(items),
            resumo={
                "total": len(items),
                "nao_lidas": len(items),
                "lidas": 0,
            },
        )

    def marcar_como_lida(self, id_notificacao, usuario_id):
        assert id_notificacao == 7
        assert usuario_id == 2
        self.item.marcar_como_lida()
        return self.item

    def marcar_todas_como_lidas(self, usuario_id):
        return 1 if usuario_id == 2 else 0


class ContainerFake:
    def __init__(self):
        self.config = ConfiguracaoFake()
        self.auth_service = AuthServiceFake()
        self.notificacao_service = NotificacaoServiceFake()


def gerar_token(usuario):
    return criar_token_acesso(
        usuario=usuario,
        secret=JWT_SECRET_TESTE,
    )


@pytest.fixture
def ambiente():
    container = ContainerFake()
    app.dependency_overrides[get_container] = lambda: container

    with TestClient(app) as client:
        yield client, container

    app.dependency_overrides.clear()


def test_cliente_sincroniza_consulta_e_le_notificacao(ambiente):
    client, container = ambiente
    token = gerar_token(container.auth_service.cliente)
    client.headers.update(
        {"Authorization": f"Bearer {token}"}
    )

    sincronizacao = client.post(
        "/api/v1/notificacoes/sincronizar"
    )
    assert sincronizacao.status_code == 200
    assert sincronizacao.json()["criadas"] == 1

    consulta = client.get(
        "/api/v1/notificacoes/consulta"
    )
    assert consulta.status_code == 200
    assert consulta.json()["total"] == 1
    assert consulta.json()["resumo"]["nao_lidas"] == 1

    leitura = client.patch(
        "/api/v1/notificacoes/7/ler"
    )
    assert leitura.status_code == 200
    assert leitura.json()["lida"] is True


def test_admin_tambem_tem_acesso_a_central(ambiente):
    client, container = ambiente
    token = gerar_token(container.auth_service.admin)
    client.headers.update(
        {"Authorization": f"Bearer {token}"}
    )

    response = client.get(
        "/api/v1/notificacoes/consulta"
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_sem_token_nao_acessa_notificacoes(ambiente):
    client, _ = ambiente

    response = client.get(
        "/api/v1/notificacoes/consulta"
    )

    assert response.status_code == 401
