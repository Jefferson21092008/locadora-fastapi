from pathlib import Path

from fastapi.testclient import TestClient

from api.dependencias import get_container
from api.main import app


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


def ler_render_yaml():
    return (
        BASE_DIR
        .joinpath("render.yaml")
        .read_text(encoding="utf-8")
    )


def test_render_usa_docker_free_e_health_check():
    conteudo = ler_render_yaml()

    assert "runtime: docker" in conteudo
    assert "plan: free" in conteudo
    assert "region: virginia" in conteudo
    assert "healthCheckPath: /health" in conteudo
    assert "autoDeployTrigger: checksPass" in conteudo


def test_render_executa_migration_e_usa_port_da_plataforma():
    conteudo = ler_render_yaml()

    assert "python -m alembic upgrade head" in conteudo
    assert "--host 0.0.0.0" in conteudo
    assert '${PORT:-10000}' in conteudo


def test_render_nao_versiona_segredos():
    conteudo = ler_render_yaml()

    assert "LOCADORA_DATABASE_URL" in conteudo
    assert "LOCADORA_ADMIN_SENHA" in conteudo
    assert "LOCADORA_JWT_SECRET" in conteudo
    assert "generateValue: true" in conteudo
    assert conteudo.count("sync: false") >= 2


def test_health_check_confirma_api_e_banco(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(
        "LOCADORA_ADMIN_SENHA",
        "senha-de-teste1",
    )
    monkeypatch.setenv(
        "LOCADORA_JWT_SECRET",
        "segredo-de-teste",
    )
    monkeypatch.setenv(
        "LOCADORA_DATABASE_URL",
        (
            "sqlite:///"
            + (
                tmp_path
                / "health.db"
            ).as_posix()
        ),
    )

    get_container.cache_clear()

    try:
        with TestClient(app) as client:
            resposta = client.get("/health")

        assert resposta.status_code == 200
        assert resposta.json() == {
            "status": "ok"
        }

    finally:
        get_container.cache_clear()
