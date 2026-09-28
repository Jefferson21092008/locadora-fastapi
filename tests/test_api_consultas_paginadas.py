from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api.dependencias import get_container
from api.main import app
from api.seguranca import criar_token_acesso
from modulos.consultas import ResultadoPaginado


JWT_SECRET_TESTE = "locadora-jwt-chave-de-testes-1234567890"


class UsuarioFake:
    def __init__(self, id_usuario, usuario, role):
        self.id = id_usuario
        self.usuario = usuario
        self.ativo = True
        self.role = SimpleNamespace(value=role)


class ClienteFake:
    def __init__(self, id_cliente=1):
        self.id = id_cliente
        self.usuario_id = 2
        self.nome = "Lucas Silva"
        self.usuario = "lucas"
        self.email = "lucas@email.com"
        self.ativo = True


class VeiculoFake:
    def __init__(self):
        self.id = 1
        self.TIPO = "carro"
        self.modelo = "Civic"
        self.ano = 2025
        self.diaria = 180.0
        self.preco_km = 1.5
        self.quilometragem = 10000.0
        self.status = SimpleNamespace(value="disponivel")
        self.ativo = True


class AluguelFake:
    def __init__(self):
        self.id = 1
        self.cliente_id = 1
        self.cliente_usuario = "lucas"
        self.cliente_nome = "Lucas Silva"
        self.veiculo_id = 1
        self.veiculo_tipo = "carro"
        self.veiculo_modelo = "Civic"
        self.dias = 3
        self.status = "ativo"
        self.km = 0.0
        self.pagamento = None
        self.valor = 540.0
        self.data_inicio = "2026-09-20"
        self.data_prevista = "2026-09-23"
        self.data_fim = None
        self.dias_atraso = 0
        self.multa = 0.0


class ManutencaoFake:
    def __init__(self):
        self.id = 1
        self.veiculo_id = 1
        self.motivo = "Troca de óleo"
        self.quilometragem = 10000.0
        self.custo = 0.0
        self.data_inicio = "2026-09-20"
        self.data_fim = None
        self.status = "ativa"
        self.tipo = "preventiva"
        self.prioridade = "media"
        self.fornecedor = "Oficina Central"
        self.custo_estimado = 350.0
        self.data_prevista = "2026-09-22"
        self.observacoes = None
        self.atrasada = False


class AuthServiceFake:
    def __init__(self):
        self.admin = UsuarioFake(1, "admin", "admin")
        self.cliente = UsuarioFake(2, "lucas", "cliente")

    def buscar_por_id(self, id_usuario):
        if id_usuario == 1:
            return self.admin
        if id_usuario == 2:
            return self.cliente
        return None


class ClienteServiceFake:
    def __init__(self):
        self.cliente = ClienteFake()
        self.ultima_consulta = None

    def consultar_clientes(self, **kwargs):
        self.ultima_consulta = kwargs
        return ResultadoPaginado(
            items=[self.cliente],
            total=1,
            resumo={"total": 1, "ativos": 1, "desativados": 0},
        )

    def buscar_por_usuario_id(self, usuario_id):
        return self.cliente if usuario_id == 2 else None


class VeiculoServiceFake:
    def consultar_veiculos(self, **kwargs):
        return ResultadoPaginado(
            items=[VeiculoFake()],
            total=1,
            resumo={
                "total": 1,
                "disponiveis": 1,
                "alugados": 0,
                "manutencao": 0,
                "desativados": 0,
            },
        )


class AluguelServiceFake:
    def __init__(self):
        self.ultima_consulta = None

    def consultar_alugueis(self, **kwargs):
        self.ultima_consulta = kwargs
        return ResultadoPaginado(
            items=[AluguelFake()],
            total=1,
            resumo={
                "total": 1,
                "ativos": 1,
                "finalizados": 0,
                "atrasados": 0,
            },
        )


class ManutencaoServiceFake:
    def consultar_manutencoes(self, **kwargs):
        return ResultadoPaginado(
            items=[ManutencaoFake()],
            total=1,
            resumo={
                "total": 1,
                "ativas": 1,
                "finalizadas": 0,
                "custo_finalizado": 0.0,
            },
        )


class ContainerFake:
    def __init__(self):
        self.config = SimpleNamespace(jwt_secret=JWT_SECRET_TESTE)
        self.auth_service = AuthServiceFake()
        self.cliente_service = ClienteServiceFake()
        self.veiculo_service = VeiculoServiceFake()
        self.aluguel_service = AluguelServiceFake()
        self.manutencao_service = ManutencaoServiceFake()


@pytest.fixture
def client():
    container = ContainerFake()
    app.dependency_overrides[get_container] = lambda: container

    admin_token = criar_token_acesso(
        usuario=container.auth_service.admin,
        secret=JWT_SECRET_TESTE,
    )
    cliente_token = criar_token_acesso(
        usuario=container.auth_service.cliente,
        secret=JWT_SECRET_TESTE,
    )

    with TestClient(app) as test_client:
        yield test_client, container, admin_token, cliente_token

    app.dependency_overrides.clear()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_consulta_clientes_retorna_metadados_e_encaminha_filtros(client):
    http, container, admin_token, _ = client

    response = http.get(
        "/api/v1/clientes/consulta",
        params={
            "pagina": 2,
            "por_pagina": 5,
            "busca": "lucas",
            "status": "ativo",
            "ordenar": "nome",
            "direcao": "desc",
        },
        headers=auth(admin_token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["total_paginas"] == 1
    assert payload["items"][0]["usuario"] == "lucas"
    assert container.cliente_service.ultima_consulta["pagina"] == 2
    assert container.cliente_service.ultima_consulta["busca"] == "lucas"


def test_consulta_veiculos_e_publica(client):
    http, _, _, _ = client

    response = http.get("/api/v1/veiculos/consulta")

    assert response.status_code == 200
    assert response.json()["resumo"]["disponiveis"] == 1


def test_consulta_alugueis_admin_exige_permissao(client):
    http, _, _, cliente_token = client

    response = http.get(
        "/api/v1/alugueis/consulta",
        headers=auth(cliente_token),
    )

    assert response.status_code == 403


def test_consulta_meus_alugueis_limita_ao_cliente_autenticado(client):
    http, container, _, cliente_token = client

    response = http.get(
        "/api/v1/alugueis/me/consulta",
        headers=auth(cliente_token),
    )

    assert response.status_code == 200
    assert container.aluguel_service.ultima_consulta["cliente_id"] == 1


def test_consulta_manutencoes_valida_paginacao(client):
    http, _, admin_token, _ = client

    response = http.get(
        "/api/v1/manutencoes/consulta",
        params={"por_pagina": 101},
        headers=auth(admin_token),
    )

    assert response.status_code == 422
