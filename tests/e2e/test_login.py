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
    page.route(
        "**/auth/login",
        lambda route: responder_json(
            route,
            {
                "access_token": "token-e2e",
                "token_type": "bearer",
            },
        ),
    )

    page.route(
        "**/auth/me",
        lambda route: responder_json(
            route,
            {
                "id": 1,
                "usuario": "usuario.e2e",
                "role": "cliente",
                "ativo": True,
            },
        ),
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

    token = page.evaluate(
        "() => sessionStorage"
        ".getItem('locadora_access_token')"
    )

    assert token == "token-e2e"

def test_login_invalido_exibe_mensagem(
    page: Page,
    app_url,
):
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

    token = page.evaluate(
        "() => sessionStorage"
        ".getItem('locadora_access_token')"
    )

    assert token is None