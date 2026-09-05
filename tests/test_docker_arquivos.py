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
    conteudo = ler_arquivo(
        "Dockerfile"
    )

    assert "FROM python:3.14-slim" in conteudo
    assert "USER app" in conteudo
    assert '"--host", "0.0.0.0"' in conteudo


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
