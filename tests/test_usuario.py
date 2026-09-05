from modulos.usuarios import (
    Role,
    Usuario,
)


def test_criar_usuario_admin():
    usuario = Usuario.criar(
        id_usuario=1,
        usuario="admin",
        senha="senha123",
        role=Role.ADMIN,
    )

    assert usuario.id == 1

    assert (
        usuario.role
        == Role.ADMIN
    )

    assert usuario.eh_admin() is True

    assert (
        usuario.validar_senha(
            "senha123"
        )
        is True
    )


def test_usuario_admin_nao_e_cliente():
    usuario = Usuario.criar(
        id_usuario=1,
        usuario="admin",
        senha="senha123",
        role=Role.ADMIN,
    )

    assert usuario.eh_admin() is True
    assert usuario.eh_cliente() is False


def test_usuario_pode_ser_desativado():
    usuario = Usuario.criar(
        id_usuario=1,
        usuario="lucas",
        senha="senha123",
    )

    assert usuario.ativo is True

    sucesso = usuario.desativar()

    assert sucesso is True
    assert usuario.ativo is False