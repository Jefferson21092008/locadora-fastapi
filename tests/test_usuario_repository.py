import pytest

from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.models import (
    Base,
)
from modulos.repositories.usuario_repository import (
    UsuarioRepository,
)
from modulos.usuarios import (
    Role,
    Usuario,
)


@pytest.fixture
def repository(tmp_path):
    caminho = (
        tmp_path
        / "usuarios_unitario.db"
    )

    banco = BancoSQLAlchemy(
        f"sqlite:///{caminho.as_posix()}"
    )

    Base.metadata.create_all(
        banco.engine
    )

    repository = UsuarioRepository(
        banco_sqlalchemy=banco,
    )

    try:
        yield repository

    finally:
        banco.fechar()


def criar_usuario(
    nome_usuario="lucas",
):
    return Usuario.criar(
        id_usuario=0,
        usuario=nome_usuario,
        senha="senha123",
        role=Role.CLIENTE,
    )


def test_repository_exige_banco_sqlalchemy():
    with pytest.raises(
        ValueError,
        match="BancoSQLAlchemy é obrigatório",
    ):
        UsuarioRepository(
            banco_sqlalchemy=None,
        )


def test_inserir_usuario(repository):
    usuario = criar_usuario()

    novo_id = repository.inserir(
        usuario
    )

    assert novo_id == 1


def test_buscar_por_id(repository):
    usuario = criar_usuario()
    usuario.id = repository.inserir(
        usuario
    )

    resultado = repository.buscar_por_id(
        usuario.id
    )

    assert resultado is not None
    assert resultado.id == usuario.id
    assert resultado.usuario == "lucas"


def test_buscar_id_inexistente(repository):
    assert (
        repository.buscar_por_id(
            999
        )
        is None
    )


def test_buscar_por_usuario(repository):
    repository.inserir(
        criar_usuario()
    )

    resultado = (
        repository
        .buscar_por_usuario(
            "LUCAS"
        )
    )

    assert resultado is not None
    assert resultado.usuario == "lucas"


def test_buscar_usuario_inexistente(repository):
    assert (
        repository
        .buscar_por_usuario(
            "naoexiste"
        )
        is None
    )


def test_buscar_usuario_ignora_espacos(repository):
    repository.inserir(
        criar_usuario()
    )

    resultado = (
        repository
        .buscar_por_usuario(
            "   LUCAS   "
        )
    )

    assert resultado is not None
    assert resultado.usuario == "lucas"


def test_atualizar_usuario(repository):
    usuario = criar_usuario()
    usuario.id = repository.inserir(
        usuario
    )

    usuario.desativar()
    repository.atualizar(
        usuario
    )

    carregado = repository.buscar_por_id(
        usuario.id
    )

    assert carregado.ativo is False


def test_listar_e_adicionar_na_colecao_nao_duplica(repository):
    usuario = criar_usuario()
    usuario.id = repository.inserir(
        usuario
    )

    repository.adicionar_na_colecao(
        usuario
    )

    resultado = repository.listar_colecao()

    assert len(resultado) == 1
    assert resultado[0].usuario == "lucas"
