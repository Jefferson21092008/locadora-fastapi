from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def ler(caminho):
    return BASE_DIR.joinpath(caminho).read_text(encoding="utf-8")


def test_compose_separa_gateway_api_e_workers():
    compose = ler("compose.yaml")

    assert "gateway:" in compose
    assert "background-worker:" in compose
    assert "outbox-worker:" in compose
    assert 'command: ["python", "-m", "modulos.background_worker"]' in compose
    assert 'command: ["python", "-m", "modulos.outbox_worker"]' in compose
    assert '"127.0.0.1:${API_PORT:-8000}:8080"' in compose
    assert "LOCADORA_WORKERS_EMBUTIDOS" in compose
    assert "LOCADORA_CONTAINER_APLICAR_MIGRATIONS" in compose


def test_gateway_resolve_replicas_dinamicamente():
    nginx = ler("infra/nginx/default.conf")

    assert "resolver 127.0.0.11" in nginx
    assert "least_conn;" in nginx
    assert "server api:8000 resolve;" in nginx
    assert "X-Forwarded-For" in nginx


def test_compose_limita_pool_por_replica():
    compose = ler("compose.yaml")

    assert "LOCADORA_DB_POOL_SIZE" in compose
    assert "LOCADORA_DB_MAX_OVERFLOW" in compose
    assert "LOCADORA_DB_POOL_TIMEOUT_SEGUNDOS" in compose



def test_workers_nao_herdam_healthcheck_http_da_imagem():
    compose = ler("compose.yaml")

    background = compose.split("  background-worker:", 1)[1].split("  outbox-worker:", 1)[0]
    outbox = compose.split("  outbox-worker:", 1)[1].split("  gateway:", 1)[0]

    assert "healthcheck:" in background
    assert "disable: true" in background
    assert "healthcheck:" in outbox
    assert "disable: true" in outbox

def test_documentacao_explica_validacao_com_duas_replicas():
    docs = ler("docs/escala-horizontal.md")

    assert "--scale api=2" in docs
    assert "X-Locadora-Instance" in docs
    assert "LOCADORA_SCALE_SENHA" in docs
    assert "FOR UPDATE SKIP LOCKED" in docs
