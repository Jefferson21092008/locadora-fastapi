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


def test_dependencias_de_desenvolvimento_ficam_separadas():
    conteudo = ler_arquivo(
        "requirements-dev.txt"
    )

    assert "-r requirements.txt" in conteudo
    assert "ruff==0.16.6" in conteudo
    assert "pip-audit==2.10.1" in conteudo


def test_ruff_tem_configuracao_conservadora():
    conteudo = ler_arquivo(
        "pyproject.toml"
    )

    assert 'target-version = "py314"' in conteudo
    assert 'select = ["E4", "E7", "E9", "F"]' in conteudo
    assert 'extend-exclude = ["scripts/legacy"]' in conteudo


def test_ci_executa_lint_e_auditoria():
    conteudo = ler_arquivo(
        ".github/workflows/ci.yml"
    )

    assert "python -m ruff check ." in conteudo
    assert "python -m pip_audit -r requirements.txt" in conteudo


def test_dependabot_monitora_ecossistemas_do_projeto():
    conteudo = ler_arquivo(
        ".github/dependabot.yml"
    )

    assert "package-ecosystem: pip" in conteudo
    assert "package-ecosystem: github-actions" in conteudo
    assert "package-ecosystem: docker" in conteudo
    assert 'timezone: "America/Recife"' in conteudo