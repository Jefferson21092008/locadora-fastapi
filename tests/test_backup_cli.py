import sqlite3

from contextlib import closing

from modulos.backup_cli import (
    main,
)


def test_cli_criar_listar_verificar_e_restaurar(
    tmp_path,
    capsys,
):
    origem = tmp_path / "origem.db"
    destino = tmp_path / "destino.db"
    diretorio = tmp_path / "backups"

    with closing(sqlite3.connect(origem)) as conexao:
        conexao.execute(
            "CREATE TABLE exemplo (valor TEXT NOT NULL)"
        )
        conexao.execute(
            "INSERT INTO exemplo VALUES ('ok')"
        )
        conexao.commit()

    assert main(
        [
            "criar",
            "--database-url",
            f"sqlite:///{origem.as_posix()}",
            "--diretorio",
            str(diretorio),
        ]
    ) == 0

    arquivo = next(
        diretorio.glob("*.sqlite3")
    )

    assert main(
        [
            "listar",
            "--diretorio",
            str(diretorio),
        ]
    ) == 0
    assert arquivo.name in capsys.readouterr().out

    assert main(
        [
            "verificar",
            str(arquivo),
        ]
    ) == 0

    assert main(
        [
            "restaurar",
            str(arquivo),
            "--destino-url",
            f"sqlite:///{destino.as_posix()}",
            "--confirmar",
        ]
    ) == 0

    with closing(sqlite3.connect(destino)) as conexao:
        assert conexao.execute(
            "SELECT valor FROM exemplo"
        ).fetchone()[0] == "ok"


def test_cli_restore_sem_confirmacao_retorna_erro(
    tmp_path,
    capsys,
):
    arquivo = tmp_path / "inexistente.sqlite3"

    codigo = main(
        [
            "restaurar",
            str(arquivo),
            "--destino-url",
            f"sqlite:///{(tmp_path / 'destino.db').as_posix()}",
        ]
    )

    assert codigo == 1
    assert "confirmação explícita" in capsys.readouterr().err
