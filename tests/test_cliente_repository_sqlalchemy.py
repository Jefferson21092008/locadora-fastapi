import pytest

from sqlalchemy.exc import (
    IntegrityError,
)

from modulos.clientes import (
    Cliente,
)
from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.models import (
    Base,
    ClienteModel,
    UsuarioModel,
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
        / "clientes_sqlalchemy.db"
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


def criar_repository(
    banco_sqlalchemy,
):
    return ClienteRepository(
        banco_sqlalchemy=(
            banco_sqlalchemy
        )
    )


def criar_cliente(
    usuario="lucas",
    email="lucas@email.com",
    usuario_id=None,
):
    cliente, mensagem = Cliente.criar(
        id_cliente=0,
        nome="Lucas Silva",
        usuario=usuario,
        email=email,
        usuario_id=usuario_id,
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


def test_inserir_e_buscar_cliente_com_sqlalchemy(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    cliente = criar_cliente()

    novo_id = repository.inserir(
        cliente
    )

    encontrado = repository.buscar_por_id(
        novo_id
    )

    assert novo_id == 1
    assert encontrado is not None
    assert encontrado.nome == "Lucas Silva"
    assert encontrado.usuario == "lucas"
    assert encontrado.email == "lucas@email.com"
    assert encontrado.ativo is True


def test_buscas_por_usuario_e_email_ignoram_maiusculas(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    repository.inserir(
        criar_cliente()
    )

    por_usuario = (
        repository
        .buscar_por_usuario(
            "  LUCAS  "
        )
    )

    por_email = (
        repository
        .buscar_por_email(
            "  LUCAS@EMAIL.COM  "
        )
    )

    assert por_usuario is not None
    assert por_usuario.usuario == "lucas"

    assert por_email is not None
    assert por_email.email == "lucas@email.com"


def test_registrar_cliente_e_usuario_na_mesma_transacao(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    cliente = criar_cliente()
    usuario = criar_usuario()

    cliente_id, usuario_id = (
        repository.registrar_com_usuario(
            cliente,
            usuario,
        )
    )

    encontrado = (
        repository
        .buscar_por_usuario_id(
            usuario_id
        )
    )

    assert cliente_id == 1
    assert usuario_id == 1
    assert encontrado is not None
    assert encontrado.id == cliente_id
    assert encontrado.usuario_id == usuario_id

    with banco_sqlalchemy.criar_sessao() as sessao:
        usuario_model = sessao.get(
            UsuarioModel,
            usuario_id,
        )

        cliente_model = sessao.get(
            ClienteModel,
            cliente_id,
        )

        assert usuario_model is not None
        assert cliente_model is not None
        assert cliente_model.senha_hash == ""


def test_registro_conjunto_faz_rollback_se_cliente_falhar(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    repository.inserir(
        criar_cliente(
            usuario="existente",
            email="duplicado@email.com",
        )
    )

    cliente = criar_cliente(
        usuario="novo-perfil",
        email="duplicado@email.com",
    )

    usuario = criar_usuario(
        usuario="novo-usuario"
    )

    with pytest.raises(
        IntegrityError
    ):
        repository.registrar_com_usuario(
            cliente,
            usuario,
        )

    with banco_sqlalchemy.criar_sessao() as sessao:
        usuarios = (
            sessao.query(
                UsuarioModel
            )
            .all()
        )

        assert usuarios == []


def test_atualizar_cliente_com_sqlalchemy(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    cliente = criar_cliente()
    cliente.id = repository.inserir(
        cliente
    )

    cliente.nome = "Lucas Atualizado"
    cliente.email = "novo@email.com"

    repository.atualizar(
        cliente
    )

    atualizado = repository.buscar_por_id(
        cliente.id
    )

    assert atualizado.nome == "Lucas Atualizado"
    assert atualizado.email == "novo@email.com"


def test_atualizar_status_de_cliente_e_usuario_juntos(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    cliente = criar_cliente()
    usuario = criar_usuario()

    cliente_id, usuario_id = (
        repository.registrar_com_usuario(
            cliente,
            usuario,
        )
    )

    repository.atualizar_status_com_usuario(
        cliente_id=cliente_id,
        usuario_id=usuario_id,
        ativo=False,
    )

    cliente_atualizado = (
        repository.buscar_por_id(
            cliente_id
        )
    )

    with banco_sqlalchemy.criar_sessao() as sessao:
        usuario_model = sessao.get(
            UsuarioModel,
            usuario_id,
        )

        assert cliente_atualizado.ativo is False
        assert usuario_model.ativo is False


def test_listagens_usam_banco_no_modo_sqlalchemy(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    primeiro = criar_cliente(
        usuario="lucas",
        email="lucas@email.com",
    )

    segundo = criar_cliente(
        usuario="maria",
        email="maria@email.com",
    )

    primeiro.id = repository.inserir(
        primeiro
    )
    segundo.id = repository.inserir(
        segundo
    )

    segundo.desativar()
    repository.atualizar(
        segundo
    )

    todos = repository.listar_colecao()
    ativos = repository.listar_ativos()
    desativados = repository.listar_desativados()

    assert [cliente.id for cliente in todos] == [1, 2]
    assert [cliente.id for cliente in ativos] == [1]
    assert [cliente.id for cliente in desativados] == [2]


def test_repository_nao_possui_estado_legado(
    banco_sqlalchemy,
):
    repository = ClienteRepository(
        banco_sqlalchemy=banco_sqlalchemy,
    )

    assert not hasattr(
        repository,
        "dados",
    )
    assert not hasattr(
        repository,
        "clientes",
    )
    assert not hasattr(
        repository,
        "usa_sqlalchemy",
    )
    assert not hasattr(
        repository,
        "adicionar_na_colecao",
    )
