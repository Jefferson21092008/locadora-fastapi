from fastapi.routing import iter_route_contexts
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
    caminhos = {
        route_context.path
        for route_context in iter_route_contexts(app.routes)
    }

    assert "/api/v1/auth/me" in caminhos
    assert "/auth/me" in caminhos


def test_openapi_expoe_somente_rotas_versionadas():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/refresh" in paths
    assert "/api/v1/auth/logout" in paths
    assert "/api/v1/auth/sessoes" in paths
    assert "/api/v1/clientes" in paths
    assert "/api/v1/veiculos" in paths
    assert "/api/v1/alugueis" in paths
    assert "/api/v1/manutencoes" in paths
    assert "/api/v1/relatorios/resumo" in paths
    assert "/api/v1/relatorios/dashboard" in paths
    assert (
        "/api/v1/relatorios/resultado-por-veiculo/"
        "exportar/{formato}"
        in paths
    )
    assert "/api/v1/auditoria" in paths
    assert "/api/v1/status" in paths
    assert "/api/v1/clientes/consulta" in paths
    assert "/api/v1/veiculos/consulta" in paths
    assert "/api/v1/alugueis/consulta" in paths
    assert "/api/v1/alugueis/me/consulta" in paths
    assert "/api/v1/manutencoes/consulta" in paths
    assert "/api/v1/reservas" in paths
    assert "/api/v1/reservas/consulta" in paths
    assert "/api/v1/reservas/me/consulta" in paths
    assert "/api/v1/manutencoes/{id_manutencao}" in paths
    assert "/api/v1/vistorias/alugueis/{id_aluguel}" in paths
    assert (
        "/api/v1/vistorias/alugueis/{id_aluguel}/inspecoes"
        in paths
    )
    assert (
        "/api/v1/vistorias/alugueis/{id_aluguel}/caucao"
        in paths
    )
    assert "/api/v1/pagamentos/consulta" in paths
    assert "/api/v1/pagamentos/alugueis/{id_aluguel}" in paths
    assert "/api/v1/pagamentos/{id_pagamento}/estornar" in paths
    assert "/api/v1/notificacoes/consulta" in paths
    assert "/api/v1/notificacoes/sincronizar" in paths
    assert "/api/v1/notificacoes/ler-todas" in paths
    assert "/api/v1/notificacoes/{id_notificacao}/ler" in paths

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
