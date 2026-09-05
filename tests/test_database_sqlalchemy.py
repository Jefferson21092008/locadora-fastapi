from sqlalchemy import (
    text,
)

from modulos.database import (
    BancoSQLAlchemy,
)


# ================================================================
# CONEXÃO
# ================================================================


def criar_banco_temporario(
    tmp_path,
):
    caminho = (
        tmp_path
        / "teste_sqlalchemy.db"
    )

    database_url = (
        f"sqlite:///{caminho.as_posix()}"
    )

    return BancoSQLAlchemy(
        database_url
    )


def test_sqlalchemy_conecta_ao_sqlite(
    tmp_path,
):
    banco = criar_banco_temporario(
        tmp_path
    )

    try:
        assert (
            banco.testar_conexao()
            is True
        )

    finally:
        banco.fechar()


def test_sqlalchemy_cria_sessao(
    tmp_path,
):
    banco = criar_banco_temporario(
        tmp_path
    )

    try:
        with banco.criar_sessao() as sessao:
            resultado = sessao.scalar(
                text(
                    "SELECT 1"
                )
            )

        assert resultado == 1

    finally:
        banco.fechar()


def test_sqlite_mantem_foreign_keys_ativas(
    tmp_path,
):
    banco = criar_banco_temporario(
        tmp_path
    )

    try:
        with banco.engine.connect() as conexao:
            foreign_keys = conexao.scalar(
                text(
                    "PRAGMA foreign_keys"
                )
            )

        assert foreign_keys == 1

    finally:
        banco.fechar()
