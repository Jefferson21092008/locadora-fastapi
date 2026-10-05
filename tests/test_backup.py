import json
import sqlite3

from contextlib import closing

from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

import pytest

from modulos import backup
from modulos.backup import (
    BackupErro,
    aplicar_retencao,
    criar_backup,
    ler_metadata,
    restaurar_backup,
    verificar_backup,
)


def _criar_sqlite(path, valor):
    with closing(sqlite3.connect(path)) as conexao:
        conexao.execute(
            "CREATE TABLE exemplo "
            "(id INTEGER PRIMARY KEY, valor TEXT NOT NULL)"
        )
        conexao.execute(
            "INSERT INTO exemplo (valor) VALUES (?)",
            (valor,),
        )
        conexao.execute(
            "CREATE TABLE alembic_version "
            "(version_num TEXT NOT NULL)"
        )
        conexao.execute(
            "INSERT INTO alembic_version VALUES (?)",
            ("20260930_0009",),
        )
        conexao.commit()


def test_backup_sqlite_cria_metadata_verifica_e_restaura(
    tmp_path,
):
    origem = tmp_path / "origem.db"
    destino = tmp_path / "restaurado.db"
    backups = tmp_path / "backups"
    _criar_sqlite(
        origem,
        "dado-original",
    )

    resultado = criar_backup(
        f"sqlite:///{origem.as_posix()}",
        backups,
        agora=datetime(
            2026,
            9,
            30,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert resultado.arquivo.is_file()
    assert resultado.metadata.is_file()
    assert resultado.backend == "sqlite"
    assert resultado.revisao_alembic == "20260930_0009"
    assert resultado.arquivo.name == (
        "locadora_sqlite_origem_20260930T120000Z.sqlite3"
    )

    metadata = verificar_backup(
        resultado.arquivo
    )
    assert metadata["sha256"] == resultado.sha256
    assert metadata["tamanho_bytes"] > 0

    restaurar_backup(
        resultado.arquivo,
        f"sqlite:///{destino.as_posix()}",
        confirmar=True,
    )

    with closing(sqlite3.connect(destino)) as conexao:
        valor = conexao.execute(
            "SELECT valor FROM exemplo"
        ).fetchone()[0]

    assert valor == "dado-original"


def test_verificacao_detecta_backup_alterado(
    tmp_path,
):
    origem = tmp_path / "origem.db"
    _criar_sqlite(
        origem,
        "seguro",
    )
    resultado = criar_backup(
        f"sqlite:///{origem.as_posix()}",
        tmp_path / "backups",
    )

    with resultado.arquivo.open("ab") as stream:
        stream.write(b"alteracao")

    with pytest.raises(
        BackupErro,
        match="Checksum",
    ):
        verificar_backup(
            resultado.arquivo
        )


def test_restore_exige_confirmacao_explicita(
    tmp_path,
):
    origem = tmp_path / "origem.db"
    _criar_sqlite(
        origem,
        "seguro",
    )
    resultado = criar_backup(
        f"sqlite:///{origem.as_posix()}",
        tmp_path / "backups",
    )

    with pytest.raises(
        BackupErro,
        match="confirmação explícita",
    ):
        restaurar_backup(
            resultado.arquivo,
            f"sqlite:///{(tmp_path / 'destino.db').as_posix()}",
        )


def test_pg_dump_nao_expoe_senha_na_linha_de_comando(
    tmp_path,
    monkeypatch,
):
    executado = {}

    monkeypatch.setattr(
        backup,
        "resolver_executavel_postgres",
        lambda nome, configurado=None: "/usr/bin/pg_dump",
    )
    monkeypatch.setattr(
        backup,
        "_revisao_alembic",
        lambda database_url: "20260930_0009",
    )

    def fake_run(
        comando,
        *,
        env,
        check,
        capture_output,
        text,
        timeout,
    ):
        executado["comando"] = comando
        executado["env"] = env
        destino = Path(
            comando[
                comando.index("--file") + 1
            ]
        )
        destino.write_bytes(
            b"PGDMP-falso"
        )

    monkeypatch.setattr(
        backup.subprocess,
        "run",
        fake_run,
    )

    resultado = criar_backup(
        (
            "postgresql+psycopg://usuario:senha-super-secreta@"
            "db.exemplo.test:5432/locadora?sslmode=require"
        ),
        tmp_path,
    )

    comando = " ".join(
        executado["comando"]
    )
    assert "senha-super-secreta" not in comando
    assert executado["env"]["PGPASSWORD"] == "senha-super-secreta"
    assert executado["env"]["PGSSLMODE"] == "require"
    assert resultado.arquivo.suffix == ".dump"


def test_pg_restore_verifica_antes_de_restaurar(
    tmp_path,
    monkeypatch,
):
    arquivo = tmp_path / "backup.dump"
    arquivo.write_bytes(
        b"PGDMP-falso"
    )
    metadata_path = Path(
        f"{arquivo}.metadata.json"
    )
    metadata_path.write_text(
        json.dumps(
            {
                "metadata_versao": 1,
                "arquivo": arquivo.name,
                "metadata": metadata_path.name,
                "backend": "postgresql",
                "banco": "locadora",
                "sha256": backup.calcular_sha256(arquivo),
                "tamanho_bytes": arquivo.stat().st_size,
                "criado_em": "2026-09-30T12:00:00+00:00",
                "revisao_alembic": "20260930_0009",
            }
        ),
        encoding="utf-8",
    )

    comandos = []

    monkeypatch.setattr(
        backup,
        "resolver_executavel_postgres",
        lambda nome, configurado=None: f"/usr/bin/{nome}",
    )

    def fake_run(
        comando,
        *,
        check,
        capture_output,
        text,
        timeout,
        env=None,
    ):
        comandos.append(comando)

    monkeypatch.setattr(
        backup.subprocess,
        "run",
        fake_run,
    )

    restaurar_backup(
        arquivo,
        (
            "postgresql+psycopg://usuario:senha@"
            "localhost:5432/destino"
        ),
        confirmar=True,
    )

    assert comandos[0][1] == "--list"
    assert "--single-transaction" in comandos[1]
    assert "--clean" in comandos[1]
    assert "senha" not in " ".join(comandos[1])


def test_retencao_remove_backup_e_metadata_mais_antigos(
    tmp_path,
):
    origem = tmp_path / "origem.db"
    _criar_sqlite(
        origem,
        "dado",
    )
    backups = tmp_path / "backups"

    resultados = []
    for dia in (1, 2, 3):
        resultados.append(
            criar_backup(
                f"sqlite:///{origem.as_posix()}",
                backups,
                agora=datetime(
                    2026,
                    9,
                    dia,
                    tzinfo=timezone.utc,
                ),
            )
        )

    removidos = aplicar_retencao(
        backups,
        manter=2,
    )

    assert removidos == [
        resultados[0].arquivo
    ]
    assert not resultados[0].arquivo.exists()
    assert not resultados[0].metadata.exists()
    assert resultados[1].arquivo.exists()
    assert resultados[2].arquivo.exists()


def test_metadata_nao_armazena_url_ou_senha(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        backup,
        "resolver_executavel_postgres",
        lambda nome, configurado=None: "/usr/bin/pg_dump",
    )
    monkeypatch.setattr(
        backup,
        "_revisao_alembic",
        lambda database_url: None,
    )

    def fake_run(
        comando,
        **kwargs,
    ):
        destino = Path(
            comando[
                comando.index("--file") + 1
            ]
        )
        destino.write_bytes(b"dump")

    monkeypatch.setattr(
        backup.subprocess,
        "run",
        fake_run,
    )

    resultado = criar_backup(
        (
            "postgresql+psycopg://usuario:senha-secreta@"
            "host.exemplo/locadora"
        ),
        tmp_path,
    )
    conteudo = resultado.metadata.read_text(
        encoding="utf-8"
    )

    assert "senha-secreta" not in conteudo
    assert "host.exemplo" not in conteudo
    assert ler_metadata(resultado.arquivo)["banco"] == "locadora"
