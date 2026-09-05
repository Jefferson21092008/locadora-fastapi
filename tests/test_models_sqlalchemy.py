import pytest

from sqlalchemy import (
    inspect,
)

from sqlalchemy.exc import (
    IntegrityError,
)

from modulos.database import (
    BancoSQLAlchemy,
)

from modulos.models import (
    Base,
    TokenRecuperacaoModel,
    UsuarioModel,
)


# ================================================================
# BANCO TEMPORÁRIO
# ================================================================


@pytest.fixture
def banco_orm(tmp_path):
    caminho = (
        tmp_path
        / "teste_models.db"
    )

    banco = BancoSQLAlchemy(
        f"sqlite:///{caminho.as_posix()}"
    )

    Base.metadata.create_all(
        banco.engine
    )

    try:
        yield banco

    finally:
        banco.fechar()


# ================================================================
# METADATA
# ================================================================


def test_base_registra_primeiros_models():
    assert "usuarios" in Base.metadata.tables

    assert (
        "tokens_recuperacao_senha"
        in Base.metadata.tables
    )


def test_models_criam_tabelas_esperadas(
    banco_orm,
):
    inspetor = inspect(
        banco_orm.engine
    )

    tabelas = set(
        inspetor.get_table_names()
    )

    assert "usuarios" in tabelas

    assert (
        "tokens_recuperacao_senha"
        in tabelas
    )


# ================================================================
# USUÁRIO
# ================================================================


def test_usuario_model_persiste_no_sqlite(
    banco_orm,
):
    usuario = UsuarioModel(
        usuario="lucas123",
        senha_hash="hash-seguro",
        role="cliente",
        ativo=True,
        criado_em="2026-08-31T19:30:00",
    )

    with banco_orm.criar_sessao() as sessao:
        sessao.add(
            usuario
        )

        sessao.commit()
        sessao.refresh(
            usuario
        )

        assert usuario.id is not None
        assert usuario.usuario == "lucas123"
        assert usuario.ativo is True


def test_usuario_model_valida_role_no_banco(
    banco_orm,
):
    usuario = UsuarioModel(
        usuario="usuario_invalido",
        senha_hash="hash-seguro",
        role="superadmin",
        ativo=True,
        criado_em="2026-08-31T19:30:00",
    )

    with banco_orm.criar_sessao() as sessao:
        sessao.add(
            usuario
        )

        with pytest.raises(
            IntegrityError
        ):
            sessao.commit()


# ================================================================
# TOKEN DE RECUPERAÇÃO
# ================================================================


def test_token_recuperacao_se_relaciona_ao_usuario(
    banco_orm,
):
    usuario = UsuarioModel(
        usuario="maria123",
        senha_hash="hash-seguro",
        role="cliente",
        ativo=True,
        criado_em="2026-08-31T19:30:00",
    )

    token = TokenRecuperacaoModel(
        token_hash="a" * 64,
        expira_em="2026-08-31T19:45:00",
        usado=False,
        criado_em="2026-08-31T19:30:00",
        usado_em=None,
    )

    usuario.tokens_recuperacao.append(
        token
    )

    with banco_orm.criar_sessao() as sessao:
        sessao.add(
            usuario
        )

        sessao.commit()
        sessao.refresh(
            token
        )

        assert token.id is not None
        assert token.usuario_id == usuario.id
        assert token.usuario.usuario == "maria123"


def test_token_recuperacao_exige_usuario_existente(
    banco_orm,
):
    token = TokenRecuperacaoModel(
        usuario_id=999,
        token_hash="b" * 64,
        expira_em="2026-08-31T19:45:00",
        usado=False,
        criado_em="2026-08-31T19:30:00",
        usado_em=None,
    )

    with banco_orm.criar_sessao() as sessao:
        sessao.add(
            token
        )

        with pytest.raises(
            IntegrityError
        ):
            sessao.commit()
