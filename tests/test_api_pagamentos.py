from types import SimpleNamespace

import pytest

from fastapi.testclient import TestClient

from api.dependencias import get_container
from api.main import app
from api.seguranca import criar_token_acesso
from modulos.consultas import ResultadoPaginado
from modulos.pagamentos import PagamentoFinanceiro


JWT_SECRET_TESTE = (
    "locadora-jwt-chave-de-testes-1234567890"
)


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
        self.admin = UsuarioFake(
            1,
            "admin",
            "admin",
        )
        self.cliente = UsuarioFake(
            2,
            "cliente",
            "cliente",
        )

    def buscar_por_id(self, id_usuario):
        return {
            1: self.admin,
            2: self.cliente,
        }.get(id_usuario)


class PagamentoServiceFake:
    def __init__(self):
        self.aluguel = SimpleNamespace(
            id=10,
            cliente_id=5,
            cliente_nome="Lucas",
            cliente_usuario="lucas",
            veiculo_id=7,
            veiculo_tipo="carro",
            veiculo_modelo="Civic",
            status="finalizado",
            data_inicio="2026-09-20",
            data_prevista="2026-09-23",
            data_fim="2026-09-23",
            pagamento="Pix",
        )
        self.pagamentos = []

    def obter_resumo(self, id_aluguel):
        saldo = 400 - sum(
            item.valor
            for item in self.pagamentos
            if item.confirmado
        )
        return {
            "aluguel": self.aluguel,
            "pagamentos": self.pagamentos,
            "valor_devolucao": 450,
            "multa_atraso": 0,
            "danos_total": 300,
            "multas_transito_total": 100,
            "total_devido": 850,
            "valor_legado_pago": 450,
            "pagamentos_adicionais": 400 - max(saldo, 0),
            "total_pago": 850 - max(saldo, 0),
            "saldo_pendente": max(saldo, 0),
            "credito_cliente": max(-saldo, 0),
            "caucao_retida_disponivel": 500,
            "status_financeiro": (
                "liquidado"
                if saldo <= 0
                else (
                    "parcial"
                    if self.pagamentos
                    else "pendente"
                )
            ),
        }

    def consultar_contas(self, **kwargs):
        return ResultadoPaginado(
            items=[self.obter_resumo(10)],
            total=1,
            resumo={
                "total": 1,
                "ativos": 0,
                "finalizados": 1,
                "atrasados": 0,
            },
        )

    def registrar_pagamento(self, **kwargs):
        pagamento = PagamentoFinanceiro(
            id_pagamento=1,
            aluguel_id=kwargs["id_aluguel"],
            valor=kwargs["valor"],
            forma=kwargs["forma"],
            parcelas=kwargs["parcelas"],
            observacoes=kwargs["observacoes"],
        )
        self.pagamentos.append(pagamento)
        return pagamento

    def estornar_pagamento(self, id_pagamento):
        pagamento = self.pagamentos[0]
        pagamento.estornar()
        return pagamento


class ContainerFake:
    def __init__(self):
        self.config = ConfiguracaoFake()
        self.auth_service = AuthServiceFake()
        self.pagamento_service = PagamentoServiceFake()
        self.auditoria_service = SimpleNamespace(
            registrar=lambda **kwargs: None,
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


def test_admin_consulta_e_registra_pagamento(
    ambiente,
):
    client, container = ambiente
    token = gerar_token(
        container.auth_service.admin
    )
    client.headers.update(
        {"Authorization": f"Bearer {token}"}
    )

    resumo = client.get(
        "/api/v1/pagamentos/alugueis/10"
    )
    assert resumo.status_code == 200
    assert resumo.json()["saldo_pendente"] == 400

    response = client.post(
        "/api/v1/pagamentos/alugueis/10",
        json={
            "valor": 150,
            "forma": "pix",
            "parcelas": 1,
        },
    )
    assert response.status_code == 201
    assert response.json()["valor"] == 150


def test_cliente_nao_acessa_financeiro(
    ambiente,
):
    client, container = ambiente
    token = gerar_token(
        container.auth_service.cliente
    )
    client.headers.update(
        {"Authorization": f"Bearer {token}"}
    )

    response = client.get(
        "/api/v1/pagamentos/consulta"
    )

    assert response.status_code == 403


def test_admin_consulta_lista_e_estorna_pagamento(
    ambiente,
):
    client, container = ambiente
    token = gerar_token(
        container.auth_service.admin
    )
    client.headers.update(
        {"Authorization": f"Bearer {token}"}
    )

    lista = client.get(
        "/api/v1/pagamentos/consulta"
    )
    assert lista.status_code == 200
    assert lista.json()["total"] == 1

    criado = client.post(
        "/api/v1/pagamentos/alugueis/10",
        json={
            "valor": 100,
            "forma": "pix",
        },
    )
    pagamento_id = criado.json()["id"]

    estorno = client.patch(
        f"/api/v1/pagamentos/{pagamento_id}/estornar"
    )

    assert estorno.status_code == 200
    assert estorno.json()["status"] == "estornado"
