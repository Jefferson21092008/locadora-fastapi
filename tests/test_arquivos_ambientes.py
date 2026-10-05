from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def ler(nome):
    return BASE_DIR.joinpath(nome).read_text(encoding="utf-8")


def test_gitignore_protege_envs_reais_e_preserva_exemplos():
    conteudo = ler(".gitignore")

    assert ".env.*" in conteudo
    assert "!.env.development.example" in conteudo
    assert "!.env.staging.example" in conteudo
    assert "!.env.production.example" in conteudo


def test_exemplos_declaram_ambientes_e_namespaces_separados():
    development = ler(".env.development.example")
    staging = ler(".env.staging.example")
    production = ler(".env.production.example")

    assert "LOCADORA_AMBIENTE=development" in development
    assert "LOCADORA_AMBIENTE=staging" in staging
    assert "LOCADORA_AMBIENTE=production" in production
    assert "LOCADORA_REDIS_PREFIXO=locadora:staging" in staging
    assert "LOCADORA_REDIS_PREFIXO=locadora:production" in production
    assert "sqlite:///" not in staging
    assert "sqlite:///" not in production


def test_staging_render_e_separado_da_producao():
    staging = ler("render.staging.yaml")
    production = ler("render.yaml")

    assert "name: locadora-fastapi-staging" in staging
    assert "value: staging" in staging
    assert "locadora:staging" in staging
    assert 'value: "false"' in staging
    assert "name: locadora-fastapi" in production
    assert "value: production" in production
    assert "locadora:production" in production


def test_ci_executa_python_em_ambiente_test():
    conteudo = ler(".github/workflows/ci.yml")

    assert conteudo.count("LOCADORA_AMBIENTE: test") >= 2


def test_documentacao_explica_fluxo_de_promocao():
    conteudo = ler("docs/ambientes.md")

    assert "development -> testes/CI -> staging -> production" in conteudo
    assert "fallback SQLite" in conteudo
    assert "dados sintéticos/anônimos" in conteudo
