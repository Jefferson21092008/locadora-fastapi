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
    assert "modulos.container_entrypoint" in conteudo
    assert "HEALTHCHECK" in conteudo
    assert "USER app:app" in conteudo

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
        "LOCADORA_AMBIENTE",
        "LOCADORA_PUBLIC_URL",
        "API_PORT",
        "LOCADORA_REDIS_URL",
        "LOCADORA_REDIS_PREFIXO",
        "LOCADORA_REDIS_TIMEOUT_MS",
        "LOCADORA_CACHE_DASHBOARD_TTL_SEGUNDOS",
        "LOCADORA_BACKGROUND_JOBS_ENABLED",
        "LOCADORA_BACKGROUND_JOBS_INTERVALO_SEGUNDOS",
        "LOCADORA_BACKGROUND_JOBS_LOTE",
        "LOCADORA_BACKGROUND_JOBS_TIMEOUT_BLOQUEIO_SEGUNDOS",
        "LOCADORA_MENSAGERIA_ENABLED",
        "LOCADORA_MENSAGERIA_INTERVALO_SEGUNDOS",
        "LOCADORA_MENSAGERIA_LOTE",
        "LOCADORA_MENSAGERIA_TIMEOUT_BLOQUEIO_SEGUNDOS",
        "LOCADORA_MENSAGERIA_RETRY_BASE_SEGUNDOS",
        "LOCADORA_MENSAGERIA_RETRY_MAX_SEGUNDOS",
        "LOCADORA_ESCALA_HORIZONTAL_ENABLED",
        "LOCADORA_WORKERS_EMBUTIDOS",
        "LOCADORA_CONTAINER_APLICAR_MIGRATIONS",
        "LOCADORA_DB_POOL_SIZE",
        "LOCADORA_DB_MAX_OVERFLOW",
        "LOCADORA_DB_POOL_TIMEOUT_SEGUNDOS",
        "LOCADORA_EXECUTAR_MIGRATIONS",
    )

    for variavel in variaveis_obrigatorias:
        assert f"{variavel}=" in conteudo
        assert f"{variavel}=\n" not in conteudo

def test_compose_configura_redis_para_cache_e_rate_limit():
    conteudo = ler_arquivo(
        "compose.yaml"
    )

    assert "redis:8-alpine" in conteudo
    assert "redis://cache:6379/0" in conteudo
    assert "LOCADORA_REDIS_PREFIXO" in conteudo
    assert "LOCADORA_CACHE_DASHBOARD_TTL_SEGUNDOS" in conteudo
    assert 'test: ["CMD", "redis-cli", "ping"]' in conteudo


def test_backups_locais_nao_entram_no_git_ou_imagem():
    gitignore = ler_arquivo(
        ".gitignore"
    )
    dockerignore = ler_arquivo(
        ".dockerignore"
    )

    assert "backups/" in gitignore
    assert "backups/" in dockerignore


def test_env_exemplo_documenta_backup_e_recuperacao():
    conteudo = ler_arquivo(
        ".env.example"
    )

    assert "LOCADORA_BACKUP_DATABASE_URL" in conteudo
    assert "LOCADORA_BACKUP_DIRETORIO=backups" in conteudo
    assert "LOCADORA_BACKUP_MANTER=7" in conteudo
    assert "LOCADORA_PG_DUMP" in conteudo
    assert "LOCADORA_PG_RESTORE" in conteudo


def test_compose_habilita_mensageria_outbox():
    conteudo = ler_arquivo("compose.yaml")

    assert "LOCADORA_MENSAGERIA_ENABLED" in conteudo
    assert "LOCADORA_MENSAGERIA_INTERVALO_SEGUNDOS" in conteudo
    assert "LOCADORA_MENSAGERIA_LOTE" in conteudo
    assert "LOCADORA_MENSAGERIA_TIMEOUT_BLOQUEIO_SEGUNDOS" in conteudo

def test_compose_api_fica_atras_do_gateway_para_permitir_replicas():
    conteudo = ler_arquivo("compose.yaml")

    assert "gateway:" in conteudo
    assert '"127.0.0.1:${API_PORT:-8000}:8080"' in conteudo
    assert 'expose:\n      - "8000"' in conteudo
    assert "http://127.0.0.1:8000/ready" in conteudo
