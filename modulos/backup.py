from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess

from contextlib import closing
from dataclasses import (
    asdict,
    dataclass,
)
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

from sqlalchemy import (
    create_engine,
    text,
)
from sqlalchemy.engine import (
    make_url,
)


METADATA_VERSAO = 1
BACKUP_PREFIXO = "locadora"


class BackupErro(RuntimeError):
    """Falha controlada durante backup, verificação ou restauração."""


@dataclass(frozen=True)
class ResultadoBackup:
    arquivo: Path
    metadata: Path
    backend: str
    banco: str
    sha256: str
    tamanho_bytes: int
    criado_em: str
    revisao_alembic: str | None


def _agora_utc():
    return datetime.now(timezone.utc)


def _slug(valor):
    texto = "".join(
        caractere
        if caractere.isalnum()
        else "-"
        for caractere in str(valor)
    )
    texto = "-".join(
        parte
        for parte in texto.split("-")
        if parte
    )
    return texto.lower() or "banco"


def _backend(database_url):
    return make_url(database_url).get_backend_name()


def _database_name(database_url):
    url = make_url(database_url)
    database = url.database or "banco"

    if url.get_backend_name() == "sqlite":
        return Path(database).stem or "banco"

    return database


def _metadata_path(arquivo):
    return Path(f"{arquivo}.metadata.json")


def calcular_sha256(arquivo):
    digest = hashlib.sha256()

    with Path(arquivo).open("rb") as stream:
        for bloco in iter(
            lambda: stream.read(1024 * 1024),
            b"",
        ):
            digest.update(bloco)

    return digest.hexdigest()


def _revisao_alembic(database_url):
    engine = None

    try:
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
        )
        with engine.connect() as conexao:
            return conexao.scalar(
                text(
                    "SELECT version_num "
                    "FROM alembic_version"
                )
            )
    except Exception:
        return None
    finally:
        if engine is not None:
            engine.dispose()


def resolver_executavel_postgres(
    nome,
    configurado=None,
):
    if configurado:
        caminho = Path(configurado)
        if caminho.is_file():
            return str(caminho)

        resolvido = shutil.which(configurado)
        if resolvido:
            return resolvido

        raise BackupErro(
            f"Executável PostgreSQL não encontrado: {configurado}"
        )

    resolvido = shutil.which(nome)
    if resolvido:
        return resolvido

    if os.name == "nt":
        program_files = Path(
            os.getenv(
                "ProgramFiles",
                r"C:\Program Files",
            )
        )
        raiz = program_files / "PostgreSQL"
        candidatos = list(
            raiz.glob(
                f"*/bin/{nome}.exe"
            )
        )

        def chave(caminho):
            try:
                return int(
                    caminho.parent.parent.name
                )
            except ValueError:
                return -1

        candidatos.sort(
            key=chave,
            reverse=True,
        )
        if candidatos:
            return str(candidatos[0])

    raise BackupErro(
        f"{nome} não foi encontrado. Instale as ferramentas "
        "cliente do PostgreSQL ou configure o caminho explicitamente."
    )


def _conexao_postgres(database_url):
    url = make_url(database_url)

    if url.get_backend_name() != "postgresql":
        raise BackupErro(
            "A URL informada não é PostgreSQL."
        )

    if not url.host or not url.database:
        raise BackupErro(
            "A URL PostgreSQL precisa informar host e banco."
        )

    argumentos = [
        "--host",
        str(url.host),
        "--port",
        str(url.port or 5432),
        "--dbname",
        str(url.database),
    ]

    if url.username:
        argumentos.extend(
            [
                "--username",
                str(url.username),
            ]
        )

    ambiente = os.environ.copy()
    if url.password:
        ambiente["PGPASSWORD"] = str(
            url.password
        )

    query = dict(url.query)
    mapeamento = {
        "sslmode": "PGSSLMODE",
        "sslrootcert": "PGSSLROOTCERT",
        "sslcert": "PGSSLCERT",
        "sslkey": "PGSSLKEY",
        "channel_binding": "PGCHANNELBINDING",
        "connect_timeout": "PGCONNECT_TIMEOUT",
        "options": "PGOPTIONS",
    }

    for chave, variavel in mapeamento.items():
        valor = query.get(chave)
        if valor:
            ambiente[variavel] = str(valor)

    return argumentos, ambiente


def _escrever_metadata(resultado):
    dados = asdict(resultado)
    dados["arquivo"] = resultado.arquivo.name
    dados["metadata"] = resultado.metadata.name
    dados["metadata_versao"] = METADATA_VERSAO

    resultado.metadata.write_text(
        json.dumps(
            dados,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def ler_metadata(arquivo):
    caminho = _metadata_path(arquivo)
    if not caminho.is_file():
        raise BackupErro(
            f"Metadata não encontrada para {Path(arquivo).name}."
        )

    try:
        dados = json.loads(
            caminho.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise BackupErro(
            "Metadata do backup está inválida."
        ) from exc

    if dados.get("metadata_versao") != METADATA_VERSAO:
        raise BackupErro(
            "Versão de metadata de backup não suportada."
        )

    return dados


def _nome_backup(
    database_url,
    criado_em,
):
    backend = _backend(database_url)
    banco = _slug(
        _database_name(database_url)
    )
    timestamp = criado_em.strftime(
        "%Y%m%dT%H%M%SZ"
    )
    extensao = (
        ".sqlite3"
        if backend == "sqlite"
        else ".dump"
    )
    return (
        f"{BACKUP_PREFIXO}_{backend}_{banco}_"
        f"{timestamp}{extensao}"
    )


def _criar_backup_sqlite(
    database_url,
    destino,
):
    url = make_url(database_url)
    origem = url.database

    if not origem or origem == ":memory:":
        raise BackupErro(
            "Backup SQLite exige um banco persistido em arquivo."
        )

    origem_path = Path(origem)
    if not origem_path.is_file():
        raise BackupErro(
            f"Banco SQLite não encontrado: {origem_path}"
        )

    with closing(
        sqlite3.connect(
            origem_path
        )
    ) as conexao_origem:
        with closing(
            sqlite3.connect(
                destino
            )
        ) as conexao_destino:
            conexao_origem.backup(
                conexao_destino
            )

            integridade = conexao_destino.execute(
                "PRAGMA integrity_check"
            ).fetchone()[0]

    if integridade != "ok":
        raise BackupErro(
            "O backup SQLite falhou no integrity_check."
        )


def _criar_backup_postgres(
    database_url,
    destino,
    executavel_pg_dump=None,
):
    executavel = resolver_executavel_postgres(
        "pg_dump",
        executavel_pg_dump,
    )
    conexao, ambiente = _conexao_postgres(
        database_url
    )

    comando = [
        executavel,
        *conexao,
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--file",
        str(destino),
    ]

    try:
        subprocess.run(
            comando,
            env=ambiente,
            check=True,
            capture_output=True,
            text=True,
            timeout=900,
        )
    except subprocess.TimeoutExpired as exc:
        raise BackupErro(
            "pg_dump excedeu o limite de 15 minutos."
        ) from exc
    except subprocess.CalledProcessError as exc:
        mensagem = (
            exc.stderr.strip()
            if exc.stderr
            else "erro sem detalhes"
        )
        raise BackupErro(
            f"pg_dump falhou: {mensagem}"
        ) from exc


def criar_backup(
    database_url,
    diretorio,
    *,
    agora=None,
    executavel_pg_dump=None,
):
    criado_em = agora or _agora_utc()
    diretorio = Path(diretorio)
    diretorio.mkdir(
        parents=True,
        exist_ok=True,
    )

    backend = _backend(database_url)
    if backend not in {
        "sqlite",
        "postgresql",
    }:
        raise BackupErro(
            f"Backend de backup não suportado: {backend}"
        )

    arquivo = diretorio / _nome_backup(
        database_url,
        criado_em,
    )
    temporario = Path(
        f"{arquivo}.tmp"
    )

    if temporario.exists():
        temporario.unlink()

    try:
        if backend == "sqlite":
            _criar_backup_sqlite(
                database_url,
                temporario,
            )
        else:
            _criar_backup_postgres(
                database_url,
                temporario,
                executavel_pg_dump,
            )

        temporario.replace(arquivo)

        resultado = ResultadoBackup(
            arquivo=arquivo,
            metadata=_metadata_path(
                arquivo
            ),
            backend=backend,
            banco=_database_name(
                database_url
            ),
            sha256=calcular_sha256(
                arquivo
            ),
            tamanho_bytes=(
                arquivo.stat().st_size
            ),
            criado_em=(
                criado_em
                .astimezone(timezone.utc)
                .isoformat()
            ),
            revisao_alembic=(
                _revisao_alembic(
                    database_url
                )
            ),
        )
        _escrever_metadata(
            resultado
        )
        return resultado
    except Exception:
        if temporario.exists():
            temporario.unlink()
        raise


def _verificar_sqlite(arquivo):
    try:
        with closing(
            sqlite3.connect(
                arquivo
            )
        ) as conexao:
            resultado = conexao.execute(
                "PRAGMA integrity_check"
            ).fetchone()[0]
    except sqlite3.DatabaseError as exc:
        raise BackupErro(
            "O arquivo SQLite não pôde ser aberto."
        ) from exc

    if resultado != "ok":
        raise BackupErro(
            "Backup SQLite corrompido segundo integrity_check."
        )


def _verificar_postgres(
    arquivo,
    executavel_pg_restore=None,
):
    executavel = resolver_executavel_postgres(
        "pg_restore",
        executavel_pg_restore,
    )

    try:
        subprocess.run(
            [
                executavel,
                "--list",
                str(arquivo),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise BackupErro(
            "pg_restore --list excedeu o limite de 2 minutos."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise BackupErro(
            "O dump PostgreSQL não passou na verificação estrutural."
        ) from exc


def verificar_backup(
    arquivo,
    *,
    executavel_pg_restore=None,
):
    arquivo = Path(arquivo)
    if not arquivo.is_file():
        raise BackupErro(
            f"Backup não encontrado: {arquivo}"
        )

    metadata = ler_metadata(
        arquivo
    )
    esperado = metadata.get(
        "sha256"
    )
    atual = calcular_sha256(
        arquivo
    )

    if not esperado or atual != esperado:
        raise BackupErro(
            "Checksum SHA-256 do backup não confere."
        )

    if arquivo.stat().st_size != metadata.get(
        "tamanho_bytes"
    ):
        raise BackupErro(
            "Tamanho do backup não confere com a metadata."
        )

    backend = metadata.get(
        "backend"
    )
    if backend == "sqlite":
        _verificar_sqlite(
            arquivo
        )
    elif backend == "postgresql":
        _verificar_postgres(
            arquivo,
            executavel_pg_restore,
        )
    else:
        raise BackupErro(
            "Backend registrado na metadata não é suportado."
        )

    return metadata


def _restaurar_sqlite(
    arquivo,
    destino_url,
):
    url = make_url(destino_url)
    destino = url.database

    if not destino or destino == ":memory:":
        raise BackupErro(
            "Restore SQLite exige banco de destino em arquivo."
        )

    destino_path = Path(destino)
    destino_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with closing(
        sqlite3.connect(
            arquivo
        )
    ) as conexao_origem:
        with closing(
            sqlite3.connect(
                destino_path
            )
        ) as conexao_destino:
            conexao_origem.backup(
                conexao_destino
            )


def _restaurar_postgres(
    arquivo,
    destino_url,
    executavel_pg_restore=None,
):
    executavel = resolver_executavel_postgres(
        "pg_restore",
        executavel_pg_restore,
    )
    conexao, ambiente = _conexao_postgres(
        destino_url
    )

    comando = [
        executavel,
        *conexao,
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-privileges",
        "--exit-on-error",
        "--single-transaction",
        str(arquivo),
    ]

    try:
        subprocess.run(
            comando,
            env=ambiente,
            check=True,
            capture_output=True,
            text=True,
            timeout=1800,
        )
    except subprocess.TimeoutExpired as exc:
        raise BackupErro(
            "pg_restore excedeu o limite de 30 minutos."
        ) from exc
    except subprocess.CalledProcessError as exc:
        mensagem = (
            exc.stderr.strip()
            if exc.stderr
            else "erro sem detalhes"
        )
        raise BackupErro(
            f"pg_restore falhou: {mensagem}"
        ) from exc


def restaurar_backup(
    arquivo,
    destino_url,
    *,
    confirmar=False,
    executavel_pg_restore=None,
):
    if not confirmar:
        raise BackupErro(
            "Restore é destrutivo. Informe confirmação explícita."
        )

    metadata = verificar_backup(
        arquivo,
        executavel_pg_restore=(
            executavel_pg_restore
        ),
    )
    backend_destino = _backend(
        destino_url
    )

    if backend_destino != metadata.get(
        "backend"
    ):
        raise BackupErro(
            "O backend do destino é diferente do backup."
        )

    if backend_destino == "sqlite":
        _restaurar_sqlite(
            Path(arquivo),
            destino_url,
        )
    elif backend_destino == "postgresql":
        _restaurar_postgres(
            Path(arquivo),
            destino_url,
            executavel_pg_restore,
        )
    else:
        raise BackupErro(
            f"Backend de restore não suportado: {backend_destino}"
        )


def listar_backups(diretorio):
    diretorio = Path(diretorio)
    if not diretorio.exists():
        return []

    itens = []
    for metadata_path in diretorio.glob(
        "*.metadata.json"
    ):
        nome_arquivo = metadata_path.name.removesuffix(
            ".metadata.json"
        )
        arquivo = diretorio / nome_arquivo
        if not arquivo.is_file():
            continue

        try:
            dados = ler_metadata(
                arquivo
            )
        except BackupErro:
            continue

        itens.append(
            (
                dados.get(
                    "criado_em",
                    "",
                ),
                arquivo,
                dados,
            )
        )

    itens.sort(
        key=lambda item: item[0],
        reverse=True,
    )
    return itens


def aplicar_retencao(
    diretorio,
    manter,
):
    if manter < 1:
        raise BackupErro(
            "A retenção deve manter pelo menos um backup."
        )

    removidos = []
    for _, arquivo, _ in listar_backups(
        diretorio
    )[manter:]:
        metadata = _metadata_path(
            arquivo
        )
        arquivo.unlink(
            missing_ok=True
        )
        metadata.unlink(
            missing_ok=True
        )
        removidos.append(
            arquivo
        )

    return removidos
