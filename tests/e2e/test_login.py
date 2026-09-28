import json

from playwright.sync_api import (
    Page,
    expect,
)


def responder_json(
    route,
    conteudo,
    status=200,
):
    route.fulfill(
        status=status,
        content_type="application/json",
        body=json.dumps(
            conteudo
        ),
    )


def test_login_abre_dashboard(
    page: Page,
    app_url,
):
    autenticado = {
        "valor": False,
    }
    autorizacoes = []

    def responder_login(route):
        autenticado["valor"] = True
        responder_json(
            route,
            {
                "access_token": "token-e2e",
                "token_type": "bearer",
            },
        )

    def responder_refresh(route):
        if not autenticado["valor"]:
            responder_json(
                route,
                {
                    "detail": "Sessão inválida ou expirada.",
                },
                status=401,
            )
            return

        responder_json(
            route,
            {
                "access_token": "token-e2e-restaurado",
                "token_type": "bearer",
            },
        )

    page.route(
        "**/auth/login",
        responder_login,
    )

    page.route(
        "**/auth/refresh",
        responder_refresh,
    )

    def responder_me(route):
        autorizacoes.append(
            route.request.headers.get(
                "authorization"
            )
        )
        responder_json(
            route,
            {
                "id": 1,
                "usuario": "usuario.e2e",
                "role": "cliente",
                "permissoes": [
                    "alugueis:criar",
                    "alugueis:devolver",
                    "alugueis:proprios:ler",
                    "conta:renomear",
                    "sessoes:gerenciar",
                ],
                "ativo": True,
            },
        )

    page.route(
        "**/auth/me",
        responder_me,
    )

    page.route(
        "**/status",
        lambda route: responder_json(
            route,
            {
                "clientes": 2,
                "veiculos": 3,
                "alugueis": 1,
                "manutencoes": 0,
            },
        ),
    )

    page.goto(
        f"{app_url}/app/"
    )

    page.locator(
        "#usuario"
    ).fill(
        "usuario.e2e"
    )

    page.locator(
        "#senha"
    ).fill(
        "Senha123"
    )

    page.locator(
        "#login-button"
    ).click()

    expect(page).to_have_url(
        f"{app_url}/app/dashboard.html"
    )

    expect(
        page.locator(
            "#current-username"
        )
    ).to_have_text(
        "usuario.e2e"
    )

    expect(
        page.locator(
            "#metric-clientes"
        )
    ).to_have_text(
        "2"
    )

    expect(
        page.locator(
            "#dashboard-sync-label"
        )
    ).to_have_text(
        "Sincronizado"
    )

    expect(
        page.locator(
            "#dashboard-last-updated"
        )
    ).to_contain_text(
        "Atualizado às"
    )

    expect(
        page.locator(
            "#quick-clientes"
        )
    ).to_be_hidden()

    token_session = page.evaluate(
        "() => sessionStorage"
        ".getItem('locadora_access_token')"
    )
    token_local = page.evaluate(
        "() => localStorage"
        ".getItem('locadora_access_token')"
    )

    assert token_session is None
    assert token_local is None
    assert (
        "Bearer token-e2e-restaurado"
        in autorizacoes
    )


def test_login_invalido_exibe_mensagem(
    page: Page,
    app_url,
):
    page.route(
        "**/auth/refresh",
        lambda route: responder_json(
            route,
            {
                "detail": "Sessão inválida ou expirada.",
            },
            status=401,
        ),
    )

    page.route(
        "**/auth/login",
        lambda route: responder_json(
            route,
            {
                "detail": (
                    "Usuário ou senha incorretos."
                )
            },
            status=401,
        ),
    )

    page.goto(
        f"{app_url}/app/"
    )

    page.locator(
        "#usuario"
    ).fill(
        "usuario.errado"
    )

    page.locator(
        "#senha"
    ).fill(
        "SenhaErrada123"
    )

    page.locator(
        "#login-button"
    ).click()

    expect(
        page.locator(
            "#login-message"
        )
    ).to_contain_text(
        "Usuário ou senha incorretos"
    )

    expect(page).to_have_url(
        f"{app_url}/app/"
    )

    token_session = page.evaluate(
        "() => sessionStorage"
        ".getItem('locadora_access_token')"
    )
    token_local = page.evaluate(
        "() => localStorage"
        ".getItem('locadora_access_token')"
    )

    assert token_session is None
    assert token_local is None
