from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def ler(nome):
    return BASE_DIR.joinpath(nome).read_text(encoding="utf-8")


def test_dockerfile_usa_build_multistage_e_copia_apenas_runtime():
    conteudo = ler("Dockerfile")

    assert "AS builder" in conteudo
    assert "AS runtime" in conteudo
    assert "COPY --from=builder /opt/venv /opt/venv" in conteudo
    assert "COPY --chown=app:app api ./api" in conteudo
    assert "COPY --chown=app:app modulos ./modulos" in conteudo
    assert "COPY . ." not in conteudo


def test_dockerfile_usa_uid_fixo_sem_home_e_sem_shell_de_login():
    conteudo = ler("Dockerfile")

    assert "APP_UID=10001" in conteudo
    assert "APP_GID=10001" in conteudo
    assert "--no-create-home" in conteudo
    assert "--shell /usr/sbin/nologin" in conteudo
    assert "USER app:app" in conteudo


def test_dockerfile_tem_healthcheck_e_entrypoint_python():
    conteudo = ler("Dockerfile")

    assert "HEALTHCHECK" in conteudo
    assert "/health" in conteudo
    assert "STOPSIGNAL SIGTERM" in conteudo
    assert 'CMD ["python", "-m", "modulos.container_entrypoint"]' in conteudo
    assert "/bin/sh" not in conteudo


def test_compose_endurece_api_e_migrate():
    conteudo = ler("compose.yaml")

    assert conteudo.count("read_only: true") >= 2
    assert conteudo.count("no-new-privileges:true") >= 2
    assert conteudo.count("- ALL") >= 2
    assert "/tmp:rw,noexec,nosuid,size=64m" in conteudo
    assert "pids_limit: 256" in conteudo
    assert 'PORT: "8000"' in conteudo
    assert 'LOCADORA_EXECUTAR_MIGRATIONS: "false"' in conteudo


def test_dependencias_de_teste_nao_entram_na_imagem_de_producao():
    producao = ler("requirements.txt")
    desenvolvimento = ler("requirements-dev.txt")

    assert "pytest==" not in producao
    assert "httpx2==" not in producao
    assert "pytest==9.1.1" in desenvolvimento


def test_dockerignore_reduz_contexto_e_nao_envia_envs_exemplo():
    conteudo = ler(".dockerignore")

    for item in (
        "tests/",
        "docs/",
        "requirements-dev.txt",
        "pytest.ini",
        "pyproject.toml",
        "*.example",
        "backups/",
        "dados/",
    ):
        assert item in conteudo


def test_ci_valida_usuario_healthcheck_e_ausencia_de_pytest_na_imagem():
    conteudo = ler(".github/workflows/ci.yml")

    assert "Validar hardening da imagem" in conteudo
    assert "os.getuid() == 10001" in conteudo
    assert "Config.Healthcheck" in conteudo
    assert "find_spec('pytest') is None" in conteudo
