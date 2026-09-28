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
)
from modulos.vistorias import (
    CaucaoAluguel,
    DanoAluguel,
    InspecaoAluguel,
    MultaTransito,
)


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
            1,
            "admin",
            "admin",
        )
        self.cliente = UsuarioFake(
            2,
            "cliente",
            "cliente",
        )

    def buscar_por_id(
        self,
        id_usuario,
    ):
        if id_usuario == 1:
            return self.admin

        if id_usuario == 2:
            return self.cliente

        return None


class VistoriaServiceFake:
    def __init__(self):
        self.inspecao = InspecaoAluguel(
            id_inspecao=1,
            aluguel_id=10,
            tipo="retirada",
            quilometragem=12000,
            combustivel_percentual=80,
        )
        self.dano = DanoAluguel(
            id_dano=2,
            aluguel_id=10,
            descricao="Risco na porta",
            valor_estimado=300,
        )
        self.multa = MultaTransito(
            id_multa=3,
            aluguel_id=10,
            descricao="Excesso de velocidade",
            valor=195,
            data_ocorrencia="2026-09-28",
        )
        self.caucao = CaucaoAluguel(
            id_caucao=4,
            aluguel_id=10,
            valor=1000,
            valor_liberado=200,
        )
        self.aluguel = SimpleNamespace(
            id=10,
            cliente_id=5,
            cliente_nome="Lucas",
            cliente_usuario="lucas",
            veiculo_id=7,
            veiculo_tipo="carro",
            veiculo_modelo="Civic",
            status="ativo",
            data_inicio="2026-09-28",
            data_prevista="2026-10-01",
            data_fim=None,
        )

    def obter_resumo(
        self,
        id_aluguel,
    ):
        if id_aluguel == 999:
            raise RecursoNaoEncontrado(
                "Aluguel não encontrado."
            )

        return {
            "aluguel": self.aluguel,
            "inspecoes": [
                self.inspecao
            ],
            "danos": [
                self.dano
            ],
            "multas": [
                self.multa
            ],
            "caucao": self.caucao,
            "indicadores": {
                "combustivel_retirada": 80,
                "combustivel_devolucao": None,
                "combustivel_faltante": 0,
                "danos_ativos_total": 300,
                "multas_ativas_total": 195,
                "caucao_retida": 800,
                "pendencias_estimadas_total": 495,
            },
        }

    def registrar_inspecao(
        self,
        **kwargs,
    ):
        return InspecaoAluguel(
            id_inspecao=8,
            aluguel_id=kwargs[
                "id_aluguel"
            ],
            tipo=kwargs["tipo"],
            quilometragem=kwargs[
                "quilometragem"
            ],
            combustivel_percentual=kwargs[
                "combustivel_percentual"
            ],
            observacoes=kwargs[
                "observacoes"
            ],
        )

    def registrar_dano(
        self,
        **kwargs,
    ):
        return DanoAluguel(
            id_dano=9,
            aluguel_id=kwargs[
                "id_aluguel"
            ],
            descricao=kwargs[
                "descricao"
            ],
            valor_estimado=kwargs[
                "valor_estimado"
            ],
        )

    def cancelar_dano(
        self,
        id_dano,
    ):
        dano = DanoAluguel(
            id_dano=id_dano,
            aluguel_id=10,
            descricao="Risco na porta",
            valor_estimado=300,
        )
        dano.cancelar()
        return dano

    def registrar_multa(
        self,
        **kwargs,
    ):
        return MultaTransito(
            id_multa=10,
            aluguel_id=kwargs[
                "id_aluguel"
            ],
            descricao=kwargs[
                "descricao"
            ],
            valor=kwargs[
                "valor"
            ],
            data_ocorrencia=kwargs[
                "data_ocorrencia"
            ],
        )

    def cancelar_multa(
        self,
        id_multa,
    ):
        multa = MultaTransito(
            id_multa=id_multa,
            aluguel_id=10,
            descricao="Excesso de velocidade",
            valor=195,
            data_ocorrencia="2026-09-28",
        )
        multa.cancelar()
        return multa

    def definir_caucao(
        self,
        **kwargs,
    ):
        return CaucaoAluguel(
            id_caucao=11,
            aluguel_id=kwargs[
                "id_aluguel"
            ],
            valor=kwargs[
                "valor"
            ],
            valor_liberado=kwargs[
                "valor_liberado"
            ],
            observacoes=kwargs[
                "observacoes"
            ],
        )


class ContainerFake:
    def __init__(self):
        self.config = ConfiguracaoFake()
        self.auth_service = (
            AuthServiceFake()
        )
        self.vistoria_service = (
            VistoriaServiceFake()
        )
        self.auditoria_service = (
            SimpleNamespace(
                registrar=lambda **kwargs: None,
            )
        )


def gerar_token(
    usuario,
):
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


@pytest.fixture
def admin_client(
    ambiente,
):
    client, container = ambiente
    token = gerar_token(
        container.auth_service.admin
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
    client, container = ambiente
    token = gerar_token(
        container.auth_service.cliente
    )
    client.headers.update(
        {
            "Authorization": (
                f"Bearer {token}"
            )
        }
    )
    return client


def test_admin_consulta_resumo_da_vistoria(
    admin_client,
):
    response = admin_client.get(
        "/api/v1/vistorias/alugueis/10"
    )

    assert response.status_code == 200
    dados = response.json()
    assert dados["aluguel"]["id"] == 10
    assert dados["indicadores"][
        "pendencias_estimadas_total"
    ] == 495
    assert dados["caucao"][
        "valor_retido"
    ] == 800


def test_admin_registra_inspecao(
    admin_client,
):
    response = admin_client.post(
        "/api/v1/vistorias/alugueis/10/inspecoes",
        json={
            "tipo": "devolucao",
            "quilometragem": 12300,
            "combustivel_percentual": 55,
            "observacoes": "Vistoria final.",
        },
    )

    assert response.status_code == 201
    assert response.json()[
        "tipo"
    ] == "devolucao"


def test_admin_registra_e_atualiza_caucao(
    admin_client,
):
    response = admin_client.put(
        "/api/v1/vistorias/alugueis/10/caucao",
        json={
            "valor": 1000,
            "valor_liberado": 500,
            "observacoes": "Liberação parcial.",
        },
    )

    assert response.status_code == 200
    assert response.json()[
        "status"
    ] == "parcial"
    assert response.json()[
        "valor_retido"
    ] == 500


def test_cliente_nao_pode_gerenciar_vistorias(
    cliente_client,
):
    response = cliente_client.get(
        "/api/v1/vistorias/alugueis/10"
    )

    assert response.status_code == 403


def test_vistoria_retorna_404_para_aluguel_inexistente(
    admin_client,
):
    response = admin_client.get(
        "/api/v1/vistorias/alugueis/999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Aluguel não encontrado."
    }
