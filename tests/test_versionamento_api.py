from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_api_v1_e_interface_canonica():
    response = client.get("/api/v1")

    assert response.status_code == 200
    assert response.json() == {
        "mensagem": "API da Locadora funcionando"
    }


def test_rota_legada_raiz_permanece_compativel():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "mensagem": "API da Locadora funcionando"
    }


def test_rota_versionada_e_legada_de_auth_coexistem():
    response_versionada = client.get("/api/v1/auth/me")
    response_legada = client.get("/auth/me")

    assert response_versionada.status_code != 404
    assert response_legada.status_code != 404


def test_openapi_expoe_somente_rotas_versionadas():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/auth/login" in paths
    assert "/api/v1/clientes" in paths
    assert "/api/v1/veiculos" in paths
    assert "/api/v1/alugueis" in paths
    assert "/api/v1/manutencoes" in paths
    assert "/api/v1/relatorios/resumo" in paths
    assert "/api/v1/auditoria" in paths
    assert "/api/v1/status" in paths

    assert "/auth/login" not in paths
    assert "/clientes" not in paths
    assert "/veiculos" not in paths
    assert "/status" not in paths


def test_frontend_centraliza_prefixo_v1():
    response = client.get("/app/js/api.js")

    assert response.status_code == 200
    assert 'const API_BASE = "/api/v1";' in response.text
    assert 'fetch(`${API_BASE}${path}`' in response.text


def test_health_continua_fora_do_versionamento():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/health" not in paths
    assert "/api/v1/health" not in paths
