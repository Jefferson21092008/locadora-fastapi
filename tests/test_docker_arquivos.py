from pathlib import Path


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


def ler_arquivo(nome):
    return (
        BASE_DIR
        .joinpath(nome)
        .read_text(
            encoding="utf-8"
        )
    )


def test_dockerfile_executa_api_sem_usuario_root():
    conteudo = ler_arquivo("Dockerfile")

    assert "FROM python:3.14-slim" in conteudo
    assert "USER app" in conteudo
    assert "python -m alembic upgrade head" in conteudo
    assert "python -m uvicorn api.main:app" in conteudo
    assert "--host 0.0.0.0" in conteudo
    assert "${PORT:-10000}" in conteudo

def test_dockerignore_protege_segredos_e_banco_local():
    conteudo = ler_arquivo(
        ".dockerignore"
    )

    assert ".env\n" in conteudo
    assert ".env.*" in conteudo
    assert "dados/*.db" in conteudo


def test_compose_usa_postgresql_18_com_volume_correto():
    conteudo = ler_arquivo(
        "compose.yaml"
    )

    assert "postgres:18-alpine" in conteudo
    assert (
        "locadora_postgres_data:"
        "/var/lib/postgresql"
        in conteudo
    )
    assert "service_healthy" in conteudo


def test_compose_executa_migration_antes_da_api():
    conteudo = ler_arquivo(
        "compose.yaml"
    )

    assert (
        'command: ["python", "-m", '
        '"alembic", "upgrade", "head"]'
        in conteudo
    )
    assert (
        "service_completed_successfully"
        in conteudo
    )
    assert (
        '"127.0.0.1:${POSTGRES_PORT:-5433}:5432"'
        in conteudo
    )

def test_env_docker_exemplo_documenta_variaveis_obrigatorias():
    conteudo = ler_arquivo(
        ".env.docker.example"
    )

    variaveis_obrigatorias = (
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_PORT",
        "LOCADORA_ADMIN_USUARIO",
        "LOCADORA_ADMIN_SENHA",
        "LOCADORA_JWT_SECRET",
        "API_PORT",
    )

    for variavel in variaveis_obrigatorias:
        assert f"{variavel}=" in conteudo
        assert f"{variavel}=\n" not in conteudo