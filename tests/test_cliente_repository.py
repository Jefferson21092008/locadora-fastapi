import pytest

from modulos.clientes import (
    Cliente,
)
from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.models import (
    Base,
)
from modulos.repositories.cliente_repository import (
    ClienteRepository,
)
from modulos.usuarios import (
    Role,
    Usuario,
)


@pytest.fixture
def banco_sqlalchemy(
    tmp_path,
):
    caminho = (
        tmp_path
        / "cliente_repository.db"
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


@pytest.fixture
def repository(
    banco_sqlalchemy,
):
    return ClienteRepository(
        banco_sqlalchemy=banco_sqlalchemy,
    )


def criar_cliente(
    usuario="lucas",
    email="lucas@email.com",
    nome="Lucas Silva",
):
    cliente, mensagem = Cliente.criar(
        id_cliente=0,
        nome=nome,
        usuario=usuario,
        email=email,
    )

    assert cliente is not None, mensagem
    return cliente


def criar_usuario(
    usuario="lucas",
):
    return Usuario.criar(
        id_usuario=0,
        usuario=usuario,
        senha="Senha123",
        role=Role.CLIENTE,
    )


def test_buscar_cliente_por_id(
    repository,
):
    cliente = criar_cliente()
    cliente.id = repository.inserir(
        cliente
    )

    encontrado = repository.buscar_por_id(
        cliente.id
    )

    assert encontrado.id == cliente.id
    assert encontrado.usuario == "lucas"


def test_buscar_cliente_por_usuario_id(
    repository,
):
    cliente = criar_cliente()
    usuario = criar_usuario()

    cliente_id, usuario_id = (
        repository.registrar_com_usuario(
            cliente,
            usuario,
        )
    )

    encontrado = (
        repository.buscar_por_usuario_id(
            usuario_id
        )
    )

    assert encontrado.id == cliente_id
    assert encontrado.usuario_id == usuario_id


def test_buscar_cliente_por_usuario(
    repository,
):
    repository.inserir(
        criar_cliente()
    )

    encontrado = repository.buscar_por_usuario(
        "lucas"
    )

    assert encontrado is not None
    assert encontrado.email == "lucas@email.com"


def test_buscar_cliente_por_email(
    repository,
):
    repository.inserir(
        criar_cliente()
    )

    encontrado = repository.buscar_por_email(
        "lucas@email.com"
    )

    assert encontrado is not None
    assert encontrado.usuario == "lucas"


def test_repository_exige_banco_sqlalchemy():
    with pytest.raises(
        ValueError,
        match="BancoSQLAlchemy é obrigatório",
    ):
        ClienteRepository(
            banco_sqlalchemy=None,
        )


def test_registrar_cliente_com_usuario(
    repository,
):
    cliente = criar_cliente()
    usuario = criar_usuario()

    cliente_id, usuario_id = (
        repository.registrar_com_usuario(
            cliente,
            usuario,
        )
    )

    assert cliente_id == 1
    assert usuario_id == 1

    encontrado = repository.buscar_por_id(
        cliente_id
    )
    assert encontrado.usuario_id == usuario_id


def test_listar_clientes_do_banco(
    repository,
):
    repository.inserir(
        criar_cliente()
    )
    repository.inserir(
        criar_cliente(
            usuario="maria",
            email="maria@email.com",
            nome="Maria Silva",
        )
    )

    resultado = repository.listar()

    assert len(resultado) == 2
    assert [c.id for c in resultado] == [1, 2]


def test_inserir_cliente(
    repository,
):
    novo_id = repository.inserir(
        criar_cliente()
    )

    assert novo_id == 1
    assert repository.buscar_por_id(
        novo_id
    ) is not None


def test_atualizar_cliente(
    repository,
):
    cliente = criar_cliente()
    cliente.id = repository.inserir(
        cliente
    )

    cliente.nome = "Lucas Atualizado"
    repository.atualizar(
        cliente
    )

    atualizado = repository.buscar_por_id(
        cliente.id
    )

    assert atualizado.nome == "Lucas Atualizado"


def test_atualizar_status_com_usuario(
    repository,
):
    cliente = criar_cliente()
    usuario = criar_usuario()

    cliente_id, usuario_id = (
        repository.registrar_com_usuario(
            cliente,
            usuario,
        )
    )

    repository.atualizar_status_com_usuario(
        cliente_id,
        usuario_id,
        False,
    )

    assert repository.buscar_por_id(
        cliente_id
    ).ativo is False


def test_listar_colecao(
    repository,
):
    repository.inserir(
        criar_cliente()
    )

    resultado = repository.listar_colecao()

    assert len(resultado) == 1
    assert resultado[0].usuario == "lucas"


def test_listar_ativos(
    repository,
):
    repository.inserir(
        criar_cliente()
    )

    cliente = criar_cliente(
        usuario="maria",
        email="maria@email.com",
        nome="Maria Silva",
    )
    cliente.id = repository.inserir(
        cliente
    )
    cliente.desativar()
    repository.atualizar(
        cliente
    )

    ativos = repository.listar_ativos()

    assert len(ativos) == 1
    assert ativos[0].usuario == "lucas"


def test_listar_desativados(
    repository,
):
    cliente = criar_cliente()
    cliente.id = repository.inserir(
        cliente
    )
    cliente.desativar()
    repository.atualizar(
        cliente
    )

    desativados = repository.listar_desativados()

    assert len(desativados) == 1
    assert desativados[0].id == cliente.id


def test_buscar_cliente_id_inexistente(
    repository,
):
    assert repository.buscar_por_id(
        999
    ) is None


def test_buscar_usuario_ignora_espacos(
    repository,
):
    repository.inserir(
        criar_cliente()
    )

    encontrado = repository.buscar_por_usuario(
        "   LUCAS   "
    )

    assert encontrado is not None
    assert encontrado.usuario == "lucas"


def test_buscar_email_none(
    repository,
):
    assert repository.buscar_por_email(
        None
    ) is None


def test_listar_colecao_retorna_nova_lista(
    repository,
):
    repository.inserir(
        criar_cliente()
    )

    primeira = repository.listar_colecao()
    segunda = repository.listar_colecao()

    assert primeira is not segunda
    assert [c.id for c in primeira] == [c.id for c in segunda]
