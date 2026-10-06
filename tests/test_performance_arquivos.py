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


def test_resultados_de_performance_nao_entram_no_git():
    conteudo = ler_arquivo(
        ".gitignore"
    )

    assert "performance-results/" in conteudo


def test_resultados_de_performance_nao_entram_na_imagem():
    conteudo = ler_arquivo(
        ".dockerignore"
    )

    assert "performance-results/" in conteudo


def test_documentacao_define_baseline_antes_de_otimizar():
    conteudo = ler_arquivo(
        "docs/testes-carga-otimizacao.md"
    )

    assert "medir baseline" in conteudo
    assert "p95" in conteudo
    assert "--allow-remote" in conteudo


def test_runner_nao_embute_credenciais():
    conteudo = ler_arquivo(
        "scripts/performance/load_test.py"
    )

    assert "LOCADORA_LOAD_USUARIO" in conteudo
    assert "LOCADORA_LOAD_SENHA" in conteudo
    assert "SUA_SENHA_LOCAL" not in conteudo
