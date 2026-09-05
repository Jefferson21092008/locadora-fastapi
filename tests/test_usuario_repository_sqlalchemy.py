import pytest

from sqlalchemy.exc import (
    IntegrityError,
)

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
def repository_sqlalchemy(tmp_path):
    caminho = (
        tmp_path
        / "usuarios_repository.db"
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
    nome="lucas",
    senha="senha123",
    role=Role.CLIENTE,
):
    return Usuario.criar(
        id_usuario=0,
        usuario=nome,
        senha=senha,
        role=role,
    )


def test_inserir_e_buscar_por_id_com_sqlalchemy(
    repository_sqlalchemy,
):
    usuario = criar_usuario()

    novo_id = (
        repository_sqlalchemy
        .inserir(
            usuario
        )
    )

    resultado = (
        repository_sqlalchemy
        .buscar_por_id(
            novo_id
        )
    )

    assert novo_id == 1
    assert resultado.id == 1
    assert resultado.usuario == "lucas"
    assert resultado.role == Role.CLIENTE


def test_buscar_por_usuario_ignora_maiusculas_e_espacos_sqlalchemy(
    repository_sqlalchemy,
):
    usuario = criar_usuario(
        nome="Lucas"
    )

    repository_sqlalchemy.inserir(
        usuario
    )

    resultado = (
        repository_sqlalchemy
        .buscar_por_usuario(
            "   LUCAS   "
        )
    )

    assert resultado is not None
    assert resultado.usuario == "Lucas"


def test_buscar_usuario_inexistente_sqlalchemy(
    repository_sqlalchemy,
):
    resultado = (
        repository_sqlalchemy
        .buscar_por_usuario(
            "naoexiste"
        )
    )

    assert resultado is None


def test_atualizar_usuario_com_sqlalchemy(
    repository_sqlalchemy,
):
    usuario = criar_usuario()

    usuario.id = (
        repository_sqlalchemy
        .inserir(
            usuario
        )
    )

    usuario.ativo = False

    repository_sqlalchemy.atualizar(
        usuario
    )

    carregado = (
        repository_sqlalchemy
        .buscar_por_id(
            usuario.id
        )
    )

    assert carregado.ativo is False


def test_listar_colecao_le_do_banco_no_modo_sqlalchemy(
    repository_sqlalchemy,
):
    repository_sqlalchemy.inserir(
        criar_usuario(
            nome="ana"
        )
    )

    repository_sqlalchemy.inserir(
        criar_usuario(
            nome="bruno"
        )
    )

    resultado = (
        repository_sqlalchemy
        .listar_colecao()
    )

    assert [
        usuario.usuario
        for usuario in resultado
    ] == [
        "ana",
        "bruno",
    ]


def test_adicionar_na_colecao_nao_duplica_usuario_no_modo_sqlalchemy(
    repository_sqlalchemy,
):
    usuario = criar_usuario()

    usuario.id = (
        repository_sqlalchemy
        .inserir(
            usuario
        )
    )

    repository_sqlalchemy.adicionar_na_colecao(
        usuario
    )

    resultado = (
        repository_sqlalchemy
        .listar_colecao()
    )

    assert len(resultado) == 1


def test_usuario_repetido_respeita_unique_do_banco(
    repository_sqlalchemy,
):
    repository_sqlalchemy.inserir(
        criar_usuario(
            nome="lucas"
        )
    )

    with pytest.raises(
        IntegrityError
    ):
        repository_sqlalchemy.inserir(
            criar_usuario(
                nome="lucas"
            )
        )


def test_repository_nao_possui_estado_legado(
    repository_sqlalchemy,
):
    assert not hasattr(
        repository_sqlalchemy,
        "dados",
    )
    assert not hasattr(
        repository_sqlalchemy,
        "usuarios",
    )
    assert not hasattr(
        repository_sqlalchemy,
        "usa_sqlalchemy",
    )


def test_repository_usa_apenas_banco_sqlalchemy(
    repository_sqlalchemy,
):
    assert (
        repository_sqlalchemy
        .banco_sqlalchemy
        is not None
    )
