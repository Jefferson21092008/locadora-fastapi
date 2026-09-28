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
    assert (
        'id="rename-user-button"'
        in resposta.text
    )

    assert (
        'id="rename-user-dialog"'
        in resposta.text
    )

    assert (
        'id="rename-user-form"'
        in resposta.text
    )


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

def test_frontend_possui_funcao_para_renomear_usuario():
    resposta = client.get(
        "/app/js/api.js"
    )

    assert resposta.status_code == 200

    assert (
        '"/auth/me/usuario"'
        in resposta.text
    )

    assert (
        'method: "PATCH"'
        in resposta.text
    )

    assert "novo_usuario" in resposta.text
    assert "senha_atual" in resposta.text
    assert (
        'method: "PATCH"'
        in resposta.text
    )

    assert "novo_usuario" in resposta.text
    assert "senha_atual" in resposta.text

def test_frontend_renova_access_token_e_faz_logout_no_backend():
    resposta = client.get(
        "/app/js/api.js"
    )

    assert resposta.status_code == 200
    assert '`${API_BASE}/auth/refresh`' in resposta.text
    assert '`${API_BASE}/auth/logout`' in resposta.text
    assert "refreshPromise" in resposta.text
    assert "navigator.locks" in resposta.text
    assert "locadora-refresh-token" in resposta.text
    assert "restoreSession" in resposta.text
    assert 'credentials: "same-origin"' in resposta.text
    assert 'method: "POST"' in resposta.text


def test_frontend_nao_persiste_access_token_no_web_storage():
    resposta = client.get(
        "/app/js/api.js"
    )

    assert resposta.status_code == 200
    assert "let accessToken = null;" in resposta.text
    assert "sessionStorage" not in resposta.text
    assert "localStorage" not in resposta.text
    assert "locadora_access_token" not in resposta.text



@pytest.mark.parametrize(
    "caminho",
    [
        "/app/js/dashboard.js",
        "/app/js/veiculos.js",
        "/app/js/alugueis.js",
        "/app/js/clientes.js",
        "/app/js/manutencoes.js",
        "/app/js/relatorios.js",
    ],
)
def test_paginas_protegidas_restauram_sessao_sem_web_storage(
    caminho,
):
    resposta = client.get(
        caminho
    )

    assert resposta.status_code == 200
    assert "restoreSession" in resposta.text
    assert "getToken" not in resposta.text


def test_frontend_consume_permissoes_rbac():
    api_js = client.get(
        "/app/js/api.js"
    )
    dashboard_js = client.get(
        "/app/js/dashboard.js"
    )

    assert api_js.status_code == 200
    assert dashboard_js.status_code == 200
    assert "Permissions" in api_js.text
    assert "hasPermission" in api_js.text
    assert (
        "applyNavigationPermissions"
        in api_js.text
    )
    assert (
        "Permissions.CONTA_RENOMEAR"
        in dashboard_js.text
    )


def test_frontend_remove_token_de_recuperacao_da_url():
    resposta = client.get(
        "/app/js/redefinir-senha.js"
    )

    assert resposta.status_code == 200
    assert "window.history.replaceState" in resposta.text
    assert "window.location.pathname" in resposta.text


def test_frontend_design_system_define_tokens_compartilhados():
    resposta = client.get(
        "/app/css/styles.css"
    )

    assert resposta.status_code == 200
    assert "--surface-subtle:" in resposta.text
    assert "--space-4:" in resposta.text
    assert "--shadow-md:" in resposta.text
    assert "--transition-base:" in resposta.text
    assert ".skip-link" in resposta.text


@pytest.mark.parametrize(
    "caminho",
    [
        "/app/",
        "/app/dashboard.html",
        "/app/veiculos.html",
        "/app/alugueis.html",
        "/app/clientes.html",
        "/app/manutencoes.html",
        "/app/relatorios.html",
        "/app/cadastro.html",
        "/app/esqueci-senha.html",
        "/app/redefinir-senha.html",
    ],
)
def test_paginas_frontend_possuem_link_de_salto_acessivel(
    caminho,
):
    resposta = client.get(
        caminho
    )

    assert resposta.status_code == 200
    assert 'class="skip-link"' in resposta.text
    assert 'href="#main-content"' in resposta.text
    assert 'id="main-content"' in resposta.text
    assert 'name="theme-color"' in resposta.text
