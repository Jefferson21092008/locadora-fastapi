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
            "queryVehicles",
        ),
        (
            "/app/js/alugueis.js",
            "queryRentals",
        ),
        (
            "/app/js/cadastro.js",
            "createClient",
        ),
        (
            "/app/js/clientes.js",
            "queryClients",
        ),
        (
            "/app/js/manutencoes.js",
            "queryMaintenances",
        ),
        (
            "/app/js/relatorios.js",
            "getFinancialSummary",
        ),
        (
            "/app/js/auditoria.js",
            "getAuditLogs",
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
        "/app/js/auditoria.js",
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
        "/app/auditoria.html",
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


def test_dashboard_expoe_visao_operacional_e_atalhos():
    resposta = client.get(
        "/app/dashboard.html"
    )

    assert resposta.status_code == 200
    assert 'id="dashboard-sync-label"' in resposta.text
    assert 'id="dashboard-last-updated"' in resposta.text
    assert 'id="quick-actions-title"' in resposta.text
    assert 'class="quick-action"' in resposta.text
    assert 'id="quick-clientes"' in resposta.text
    assert 'id="quick-manutencoes"' in resposta.text
    assert 'id="quick-relatorios"' in resposta.text
    assert 'id="quick-auditoria"' in resposta.text
    assert 'data-metric-card' in resposta.text
    assert 'id="admin-dashboard-insights"' in resposta.text
    assert 'id="dashboard-fleet-rate"' in resposta.text
    assert 'id="dashboard-gross-result"' in resposta.text
    assert 'id="dashboard-average-ticket"' in resposta.text


def test_dashboard_js_controla_sincronizacao_e_loading():
    resposta = client.get(
        "/app/js/dashboard.js"
    )

    assert resposta.status_code == 200
    assert "setDashboardLoading" in resposta.text
    assert "markDashboardSynced" in resposta.text
    assert "markDashboardError" in resposta.text
    assert "Intl.DateTimeFormat" in resposta.text
    assert "dashboard-metric-card--loading" in resposta.text
    assert "applyNavigationPermissions(currentUser)" in resposta.text
    assert "getDashboardMetrics" in resposta.text
    assert "Permissions.RELATORIOS_LER" in resposta.text
    assert "updateAdminMetrics" in resposta.text
    assert "formatCurrency" in resposta.text


def test_frontend_auditoria_esta_disponivel():
    resposta = client.get(
        "/app/auditoria.html"
    )

    assert resposta.status_code == 200
    assert 'id="audit-list"' in resposta.text
    assert 'id="audit-search"' in resposta.text
    assert 'id="audit-resource-filter"' in resposta.text
    assert 'id="audit-action-filter"' in resposta.text
    assert "/app/js/auditoria.js" in resposta.text


def test_frontend_api_expoe_consulta_de_auditoria():
    resposta = client.get(
        "/app/js/api.js"
    )

    assert resposta.status_code == 200
    assert 'return apiRequest("/auditoria")' in resposta.text
    assert (
        '"/app/auditoria.html": Permissions.AUDITORIA_LER'
        in resposta.text
    )


@pytest.mark.parametrize(
    "caminho,contador,limpar",
    [
        (
            "/app/veiculos.html",
            "vehicles-results-count",
            "clear-vehicle-filters",
        ),
        (
            "/app/clientes.html",
            "clients-results-count",
            "clear-client-filters",
        ),
        (
            "/app/alugueis.html",
            "rentals-results-count",
            "clear-rental-filters",
        ),
        (
            "/app/manutencoes.html",
            "maintenances-results-count",
            "clear-maintenance-filters",
        ),
    ],
)
def test_telas_operacionais_expoem_feedback_de_filtros(
    caminho,
    contador,
    limpar,
):
    resposta = client.get(
        caminho
    )

    assert resposta.status_code == 200
    assert f'id="{contador}"' in resposta.text
    assert f'id="{limpar}"' in resposta.text


def test_auditoria_frontend_respeita_rbac_e_filtros():
    resposta = client.get(
        "/app/js/auditoria.js"
    )

    assert resposta.status_code == 200
    assert "Permissions.AUDITORIA_LER" in resposta.text
    assert "applyNavigationPermissions" in resposta.text
    assert "filteredLogs" in resposta.text
    assert "request_id" in resposta.text
    assert "campos_alterados" in resposta.text


def test_frontend_ui_compartilhada_adiciona_melhorias_de_ux():
    resposta = client.get("/app/js/ui.js")

    assert resposta.status_code == 200
    assert "setupSearchShortcuts" in resposta.text
    assert "setupDialogFocus" in resposta.text
    assert "setupFormBusyStates" in resposta.text
    assert "setupNetworkStatus" in resposta.text
    assert 'aria-keyshortcuts' in resposta.text
    assert "MutationObserver" in resposta.text
    assert "Conexão restaurada" in resposta.text


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
        "/app/auditoria.html",
        "/app/cadastro.html",
        "/app/esqueci-senha.html",
        "/app/redefinir-senha.html",
    ],
)
def test_paginas_frontend_carregam_camada_compartilhada_de_ux(caminho):
    resposta = client.get(caminho)

    assert resposta.status_code == 200
    assert '<script type="module" src="/app/js/ui.js"></script>' in resposta.text


def test_telas_operacionais_relacionam_busca_com_resultados():
    casos = [
        ("/app/veiculos.html", "vehicle-search", "vehicles-grid", "vehicles-results-count"),
        ("/app/clientes.html", "client-search", "clients-grid", "clients-results-count"),
        ("/app/alugueis.html", "rental-search", "rentals-list", "rentals-results-count"),
        ("/app/manutencoes.html", "maintenance-search", "maintenances-list", "maintenances-results-count"),
        ("/app/auditoria.html", "audit-search", "audit-list", "audit-results-count"),
    ]

    for caminho, campo, lista, contador in casos:
        resposta = client.get(caminho)
        assert resposta.status_code == 200
        assert f'id="{campo}"' in resposta.text
        assert f'aria-controls="{lista}"' in resposta.text
        assert f'aria-describedby="{contador}"' in resposta.text
        assert 'enterkeyhint="search"' in resposta.text


def test_dialogos_principais_possuem_nome_acessivel():
    veiculos = client.get("/app/veiculos.html").text
    alugueis = client.get("/app/alugueis.html").text
    manutencoes = client.get("/app/manutencoes.html").text
    clientes = client.get("/app/clientes.html").text

    assert 'aria-labelledby="vehicle-dialog-title"' in veiculos
    assert 'aria-labelledby="status-dialog-title"' in veiculos
    assert 'aria-labelledby="rental-dialog-title"' in alugueis
    assert 'aria-labelledby="return-dialog-title"' in alugueis
    assert 'aria-labelledby="maintenance-dialog-title"' in manutencoes
    assert 'aria-labelledby="finish-maintenance-title"' in manutencoes
    assert 'aria-labelledby="client-status-title"' in clientes


def test_css_final_cobre_mobile_contraste_e_estado_de_rede():
    resposta = client.get("/app/css/styles.css")

    assert resposta.status_code == 200
    assert ".network-status" in resposta.text
    assert "100dvh" in resposta.text
    assert "prefers-contrast: more" in resposta.text
    assert "forced-colors: active" in resposta.text
    assert "pointer: coarse" in resposta.text
    assert "body:has(dialog[open])" in resposta.text


def test_relatorio_tabela_rolavel_e_focavel_por_teclado():
    resposta = client.get("/app/relatorios.html")

    assert resposta.status_code == 200
    assert 'class="report-table-scroll"' in resposta.text
    assert 'role="region"' in resposta.text
    assert 'aria-label="Resultados por veículo"' in resposta.text
    assert 'tabindex="0"' in resposta.text

@pytest.mark.parametrize(
    "caminho,ordem,pagina_anterior,pagina_proxima",
    [
        (
            "/app/clientes.html",
            "client-order",
            "clients-page-previous",
            "clients-page-next",
        ),
        (
            "/app/veiculos.html",
            "vehicle-order",
            "vehicles-page-previous",
            "vehicles-page-next",
        ),
        (
            "/app/alugueis.html",
            "rental-order",
            "rentals-page-previous",
            "rentals-page-next",
        ),
        (
            "/app/manutencoes.html",
            "maintenance-order",
            "maintenances-page-previous",
            "maintenances-page-next",
        ),
    ],
)
def test_telas_operacionais_expoem_ordenacao_e_paginacao(
    caminho,
    ordem,
    pagina_anterior,
    pagina_proxima,
):
    resposta = client.get(caminho)

    assert resposta.status_code == 200
    assert f'id="{ordem}"' in resposta.text
    assert f'id="{pagina_anterior}"' in resposta.text
    assert f'id="{pagina_proxima}"' in resposta.text
    assert "por página" in resposta.text


def test_frontend_api_expoe_consultas_server_side():
    resposta = client.get("/app/js/api.js")

    assert resposta.status_code == 200
    assert "/clientes/consulta" in resposta.text
    assert "/veiculos/consulta" in resposta.text
    assert "/alugueis/consulta" in resposta.text
    assert "/alugueis/me/consulta" in resposta.text
    assert "/manutencoes/consulta" in resposta.text
    assert "URLSearchParams" in resposta.text


def test_frontend_operacional_deixa_de_filtrar_listas_inteiras_localmente():
    clientes = client.get("/app/js/clientes.js").text
    veiculos = client.get("/app/js/veiculos.js").text
    alugueis = client.get("/app/js/alugueis.js").text
    manutencoes = client.get("/app/js/manutencoes.js").text

    assert "queryClients" in clientes
    assert "queryVehicles" in veiculos
    assert "queryRentals" in alugueis
    assert "queryMaintenances" in manutencoes
    assert "total_paginas" in clientes
    assert "total_paginas" in veiculos
    assert "total_paginas" in alugueis
    assert "total_paginas" in manutencoes

def test_frontend_api_expoe_metricas_do_dashboard():
    resposta = client.get(
        "/app/js/api.js"
    )

    assert resposta.status_code == 200
    assert "getDashboardMetrics" in resposta.text
    assert 'apiRequest("/relatorios/dashboard")' in resposta.text
