import pytest

from fastapi.testclient import (
    TestClient,
)

from api.main import app


client = TestClient(app)


def test_frontend_login_esta_disponivel():
    resposta = client.get(
        "/app/"
    )

    assert resposta.status_code == 200
    assert (
        "text/html"
        in resposta.headers["content-type"]
    )
    assert 'id="login-form"' in resposta.text
    assert "/app/js/auth.js" in resposta.text
    assert "/app/esqueci-senha.html" in resposta.text


def test_frontend_dashboard_esta_disponivel():
    resposta = client.get(
        "/app/dashboard.html"
    )

    assert resposta.status_code == 200
    assert 'id="metrics-title"' in resposta.text
    assert "/app/js/dashboard.js" in resposta.text


def test_frontend_veiculos_esta_disponivel():
    resposta = client.get(
        "/app/veiculos.html"
    )

    assert resposta.status_code == 200
    assert 'id="vehicles-grid"' in resposta.text
    assert 'id="vehicle-form"' in resposta.text
    assert "/app/js/veiculos.js" in resposta.text


def test_frontend_alugueis_esta_disponivel():
    resposta = client.get(
        "/app/alugueis.html"
    )

    assert resposta.status_code == 200
    assert 'id="rentals-list"' in resposta.text
    assert 'id="rental-form"' in resposta.text
    assert 'id="return-form"' in resposta.text
    assert "/app/js/alugueis.js" in resposta.text


def test_frontend_cadastro_esta_disponivel():
    resposta = client.get(
        "/app/cadastro.html"
    )

    assert resposta.status_code == 200
    assert 'id="register-form"' in resposta.text
    assert "/app/js/cadastro.js" in resposta.text


def test_frontend_clientes_esta_disponivel():
    resposta = client.get(
        "/app/clientes.html"
    )

    assert resposta.status_code == 200
    assert 'id="clients-grid"' in resposta.text
    assert 'id="client-status-dialog"' in resposta.text
    assert "/app/js/clientes.js" in resposta.text


def test_frontend_manutencoes_esta_disponivel():
    resposta = client.get(
        "/app/manutencoes.html"
    )

    assert resposta.status_code == 200
    assert 'id="maintenances-list"' in resposta.text
    assert 'id="maintenance-form"' in resposta.text
    assert 'id="finish-maintenance-form"' in resposta.text
    assert "/app/js/manutencoes.js" in resposta.text


def test_frontend_relatorios_esta_disponivel():
    resposta = client.get(
        "/app/relatorios.html"
    )

    assert resposta.status_code == 200
    assert 'id="reports-content"' in resposta.text
    assert 'id="revenue-by-type"' in resposta.text
    assert 'id="vehicle-results"' in resposta.text
    assert "/app/js/relatorios.js" in resposta.text


def test_frontend_esqueci_senha_esta_disponivel():
    resposta = client.get(
        "/app/esqueci-senha.html"
    )

    assert resposta.status_code == 200
    assert 'id="forgot-password-form"' in resposta.text
    assert "/app/js/esqueci-senha.js" in resposta.text
    assert "/app/redefinir-senha.html" in resposta.text


def test_frontend_redefinir_senha_esta_disponivel():
    resposta = client.get(
        "/app/redefinir-senha.html"
    )

    assert resposta.status_code == 200
    assert 'id="reset-password-form"' in resposta.text
    assert 'id="recovery-token"' in resposta.text
    assert "/app/js/redefinir-senha.js" in resposta.text


@pytest.mark.parametrize(
    "caminho,conteudo_esperado",
    [
        (
            "/app/css/styles.css",
            "--navy-950",
        ),
        (
            "/app/js/api.js",
            'apiRequest("/auth/login"',
        ),
        (
            "/app/js/dashboard.js",
            "getSystemStatus",
        ),
        (
            "/app/js/veiculos.js",
            "getVehicles",
        ),
        (
            "/app/js/alugueis.js",
            "getMyRentals",
        ),
        (
            "/app/js/cadastro.js",
            "createClient",
        ),
        (
            "/app/js/clientes.js",
            "getClients",
        ),
        (
            "/app/js/manutencoes.js",
            "getMaintenances",
        ),
        (
            "/app/js/relatorios.js",
            "getFinancialSummary",
        ),
        (
            "/app/js/esqueci-senha.js",
            "requestPasswordReset",
        ),
        (
            "/app/js/redefinir-senha.js",
            "resetPassword",
        ),
    ],
)
def test_assets_do_frontend_sao_servidos(
    caminho,
    conteudo_esperado,
):
    resposta = client.get(
        caminho
    )

    assert resposta.status_code == 200
    assert conteudo_esperado in resposta.text
