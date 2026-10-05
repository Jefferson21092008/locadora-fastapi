from __future__ import annotations

import argparse
import os
import sys

from pathlib import Path

from dotenv import load_dotenv

from modulos.backup import (
    BackupErro,
    aplicar_retencao,
    criar_backup,
    listar_backups,
    restaurar_backup,
    verificar_backup,
)
from modulos.config import (
    DATABASE_URL_PADRAO,
    normalizar_database_url,
)


load_dotenv()


def _database_url_origem(args):
    valor = (
        args.database_url
        or os.getenv(
            "LOCADORA_BACKUP_DATABASE_URL"
        )
        or os.getenv(
            "LOCADORA_DATABASE_URL"
        )
        or DATABASE_URL_PADRAO
    )
    return normalizar_database_url(
        valor
    )


def _diretorio(args):
    return Path(
        args.diretorio
        or os.getenv(
            "LOCADORA_BACKUP_DIRETORIO",
            "backups",
        )
    )


def _manter(args):
    if args.manter is not None:
        return args.manter

    valor = os.getenv(
        "LOCADORA_BACKUP_MANTER",
        "7",
    )
    try:
        return max(
            int(valor),
            1,
        )
    except ValueError:
        return 7


def _parser():
    parser = argparse.ArgumentParser(
        prog="python -m modulos.backup_cli",
        description=(
            "Backup, verificação e recuperação do banco da Locadora."
        ),
    )
    subparsers = parser.add_subparsers(
        dest="comando",
        required=True,
    )

    criar = subparsers.add_parser(
        "criar",
        help="Cria backup consistente e metadata com checksum.",
    )
    criar.add_argument(
        "--database-url",
    )
    criar.add_argument(
        "--diretorio",
    )
    criar.add_argument(
        "--manter",
        type=int,
    )
    criar.add_argument(
        "--pg-dump",
        default=os.getenv(
            "LOCADORA_PG_DUMP"
        ),
    )

    verificar = subparsers.add_parser(
        "verificar",
        help="Confere checksum e integridade estrutural do backup.",
    )
    verificar.add_argument(
        "arquivo",
    )
    verificar.add_argument(
        "--pg-restore",
        default=os.getenv(
            "LOCADORA_PG_RESTORE"
        ),
    )

    restaurar = subparsers.add_parser(
        "restaurar",
        help=(
            "Restaura um backup em um banco de destino explícito."
        ),
    )
    restaurar.add_argument(
        "arquivo",
    )
    restaurar.add_argument(
        "--destino-url",
        required=True,
    )
    restaurar.add_argument(
        "--confirmar",
        action="store_true",
        help=(
            "Confirma a operação destrutiva sobre o banco de destino."
        ),
    )
    restaurar.add_argument(
        "--pg-restore",
        default=os.getenv(
            "LOCADORA_PG_RESTORE"
        ),
    )

    listar = subparsers.add_parser(
        "listar",
        help="Lista backups com metadata válida.",
    )
    listar.add_argument(
        "--diretorio",
    )

    limpar = subparsers.add_parser(
        "limpar",
        help="Aplica retenção local aos backups mais antigos.",
    )
    limpar.add_argument(
        "--diretorio",
    )
    limpar.add_argument(
        "--manter",
        type=int,
    )
    limpar.add_argument(
        "--confirmar",
        action="store_true",
    )

    return parser


def _executar(args):
    if args.comando == "criar":
        resultado = criar_backup(
            _database_url_origem(args),
            _diretorio(args),
            executavel_pg_dump=(
                args.pg_dump
            ),
        )
        aplicar_retencao(
            _diretorio(args),
            _manter(args),
        )
        print(
            f"Backup criado: {resultado.arquivo}"
        )
        print(
            f"SHA-256: {resultado.sha256}"
        )
        print(
            "Revisão Alembic: "
            f"{resultado.revisao_alembic or 'não identificada'}"
        )
        return 0

    if args.comando == "verificar":
        metadata = verificar_backup(
            args.arquivo,
            executavel_pg_restore=(
                args.pg_restore
            ),
        )
        print(
            "Backup válido: "
            f"{Path(args.arquivo).name}"
        )
        print(
            f"Backend: {metadata['backend']}"
        )
        print(
            f"SHA-256: {metadata['sha256']}"
        )
        return 0

    if args.comando == "restaurar":
        restaurar_backup(
            args.arquivo,
            normalizar_database_url(
                args.destino_url
            ),
            confirmar=args.confirmar,
            executavel_pg_restore=(
                args.pg_restore
            ),
        )
        print(
            "Restore concluído no destino informado."
        )
        return 0

    if args.comando == "listar":
        itens = listar_backups(
            _diretorio(args)
        )
        if not itens:
            print(
                "Nenhum backup encontrado."
            )
            return 0

        for _, arquivo, metadata in itens:
            print(
                f"{arquivo.name} | "
                f"{metadata['backend']} | "
                f"{metadata['criado_em']} | "
                f"{metadata['tamanho_bytes']} bytes"
            )
        return 0

    if args.comando == "limpar":
        if not args.confirmar:
            raise BackupErro(
                "Limpeza exige --confirmar."
            )
        removidos = aplicar_retencao(
            _diretorio(args),
            _manter(args),
        )
        print(
            f"Backups removidos: {len(removidos)}"
        )
        return 0

    raise BackupErro(
        "Comando de backup desconhecido."
    )


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)

    try:
        return _executar(args)
    except BackupErro as exc:
        print(
            f"Erro: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
