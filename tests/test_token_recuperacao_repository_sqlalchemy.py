import pytest

from sqlalchemy.exc import (
    IntegrityError,
)

from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.models import (
    Base,
    UsuarioModel,
)
from modulos.repositories.token_recuperacao_repository import (
    TokenRecuperacaoRepository,
)


@pytest.fixture
def repository_sqlalchemy(tmp_path):
    caminho = (
        tmp_path
        / "tokens_repository.db"
    )

    banco = BancoSQLAlchemy(
        f"sqlite:///{caminho.as_posix()}"
    )

    Base.metadata.create_all(
        banco.engine
    )

    with banco.criar_sessao() as sessao:
        usuario = UsuarioModel(
            usuario="lucas",
            senha_hash="hash_teste",
            role="cliente",
            ativo=True,
            criado_em="2026-08-31T20:00:00",
        )

        sessao.add(
            usuario
        )
        sessao.commit()

    repository = TokenRecuperacaoRepository(
        banco_sqlalchemy=banco,
    )

    try:
        yield repository

    finally:
        banco.fechar()


def inserir_token(
    repository,
    token_hash="a" * 64,
):
    return repository.inserir(
        usuario_id=1,
        token_hash=token_hash,
        expira_em="2026-08-31T20:15:00",
        criado_em="2026-08-31T20:00:00",
    )


def test_inserir_e_buscar_token_com_sqlalchemy(
    repository_sqlalchemy,
):
    novo_id = inserir_token(
        repository_sqlalchemy
    )

    registro = (
        repository_sqlalchemy
        .buscar_por_hash(
            "a" * 64
        )
    )

    assert novo_id == 1
    assert registro == {
        "id": 1,
        "usuario_id": 1,
        "token_hash": "a" * 64,
        "expira_em": "2026-08-31T20:15:00",
        "usado": False,
        "criado_em": "2026-08-31T20:00:00",
        "usado_em": None,
    }


def test_buscar_token_inexistente_retorna_none_sqlalchemy(
    repository_sqlalchemy,
):
    resultado = (
        repository_sqlalchemy
        .buscar_por_hash(
            "nao-existe"
        )
    )

    assert resultado is None


def test_invalidar_tokens_do_usuario_com_sqlalchemy(
    repository_sqlalchemy,
):
    inserir_token(
        repository_sqlalchemy,
        token_hash="a" * 64,
    )
    inserir_token(
        repository_sqlalchemy,
        token_hash="b" * 64,
    )

    total = (
        repository_sqlalchemy
        .invalidar_do_usuario(
            usuario_id=1,
            usado_em="2026-08-31T20:05:00",
        )
    )

    token_a = (
        repository_sqlalchemy
        .buscar_por_hash(
            "a" * 64
        )
    )
    token_b = (
        repository_sqlalchemy
        .buscar_por_hash(
            "b" * 64
        )
    )

    assert total == 2
    assert token_a["usado"] is True
    assert token_b["usado"] is True
    assert token_a["usado_em"] == "2026-08-31T20:05:00"
    assert token_b["usado_em"] == "2026-08-31T20:05:00"


def test_invalidar_ignora_token_ja_usado_sqlalchemy(
    repository_sqlalchemy,
):
    id_token = inserir_token(
        repository_sqlalchemy
    )

    repository_sqlalchemy.marcar_como_usado(
        id_token=id_token,
        usado_em="2026-08-31T20:03:00",
    )

    total = (
        repository_sqlalchemy
        .invalidar_do_usuario(
            usuario_id=1,
            usado_em="2026-08-31T20:04:00",
        )
    )

    registro = (
        repository_sqlalchemy
        .buscar_por_hash(
            "a" * 64
        )
    )

    assert total == 0
    assert registro["usado_em"] == "2026-08-31T20:03:00"


def test_marcar_token_como_usado_com_sqlalchemy(
    repository_sqlalchemy,
):
    id_token = inserir_token(
        repository_sqlalchemy
    )

    resultado = (
        repository_sqlalchemy
        .marcar_como_usado(
            id_token=id_token,
            usado_em="2026-08-31T20:07:00",
        )
    )

    registro = (
        repository_sqlalchemy
        .buscar_por_hash(
            "a" * 64
        )
    )

    assert resultado is True
    assert registro["usado"] is True
    assert registro["usado_em"] == "2026-08-31T20:07:00"


def test_token_nao_pode_ser_consumido_duas_vezes_sqlalchemy(
    repository_sqlalchemy,
):
    id_token = inserir_token(
        repository_sqlalchemy
    )

    primeira = (
        repository_sqlalchemy
        .marcar_como_usado(
            id_token=id_token,
            usado_em="2026-08-31T20:07:00",
        )
    )

    segunda = (
        repository_sqlalchemy
        .marcar_como_usado(
            id_token=id_token,
            usado_em="2026-08-31T20:08:00",
        )
    )

    assert primeira is True
    assert segunda is False


def test_token_hash_repetido_respeita_unique_do_banco(
    repository_sqlalchemy,
):
    inserir_token(
        repository_sqlalchemy
    )

    with pytest.raises(
        IntegrityError
    ):
        inserir_token(
            repository_sqlalchemy
        )


def test_token_exige_usuario_existente_por_foreign_key(
    repository_sqlalchemy,
):
    with pytest.raises(
        IntegrityError
    ):
        repository_sqlalchemy.inserir(
            usuario_id=999,
            token_hash="c" * 64,
            expira_em="2026-08-31T20:15:00",
            criado_em="2026-08-31T20:00:00",
        )


def test_repository_nao_possui_mais_estado_legado(
    repository_sqlalchemy,
):
    assert not hasattr(
        repository_sqlalchemy,
        "dados",
    )
    assert not hasattr(
        repository_sqlalchemy,
        "usa_sqlalchemy",
    )


def test_repository_exige_banco_sqlalchemy():
    with pytest.raises(
        TypeError
    ):
        TokenRecuperacaoRepository()
