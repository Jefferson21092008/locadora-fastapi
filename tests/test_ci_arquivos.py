from pathlib import Path


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


def ler_workflow():
    return (
        BASE_DIR
        .joinpath(
            ".github",
            "workflows",
            "ci.yml",
        )
        .read_text(
            encoding="utf-8"
        )
    )


def test_ci_executa_em_push_e_pull_request_da_main():
    conteudo = ler_workflow()

    assert "push:\n    branches: [main]" in conteudo
    assert "pull_request:\n    branches: [main]" in conteudo
    assert "workflow_dispatch:" in conteudo


def test_ci_usa_permissoes_minimas_e_acoes_atuais():
    conteudo = ler_workflow()

    assert "permissions:\n  contents: read" in conteudo
    assert "actions/checkout@v6" in conteudo
    assert "actions/setup-python@v6" in conteudo
    assert 'python-version: "3.14"' in conteudo
    assert "cache: pip" in conteudo


def test_ci_cria_postgresql_de_teste_isolado():
    conteudo = ler_workflow()

    assert "image: postgres:18-alpine" in conteudo
    assert "POSTGRES_DB: locadora_test" in conteudo
    assert "POSTGRES_USER: locadora_app" in conteudo
    assert "pg_isready -U locadora_app -d locadora_test" in conteudo
    assert "LOCADORA_TEST_DATABASE_URL:" in conteudo


def test_ci_valida_dependencias_migrations_e_testes():
    conteudo = ler_workflow()

    assert "python -m pip check" in conteudo
    assert "python -m alembic upgrade head" in conteudo
    assert "python -m alembic current" in conteudo
    assert "python -m pytest" in conteudo


def test_ci_valida_compose_e_constroi_imagem():
    conteudo = ler_workflow()

    assert (
        "docker compose --env-file "
        ".env.docker.example config --quiet"
        in conteudo
    )
    assert "docker build --tag locadora-api:ci ." in conteudo