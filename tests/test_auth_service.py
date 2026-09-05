import pytest

from modulos.servicos.auth_service import (
    AuthService,
)

from modulos.usuarios import (
    Role,
)

from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)


class UsuarioRepositoryFake:
    def __init__(self):
        self.usuarios = []
        self.ultimo_id = 0

    def buscar_por_usuario(
        self,
        nome_usuario,
    ):
        nome_usuario = (
            str(nome_usuario)
            .strip()
            .lower()
        )

        for usuario in self.usuarios:
            if (
                usuario.usuario.lower()
                == nome_usuario
            ):
                return usuario

        return None

    def buscar_por_id(
        self,
        id_usuario,
    ):
        for usuario in self.usuarios:
            if usuario.id == id_usuario:
                return usuario

        return None

    def inserir(
        self,
        usuario,
    ):
        self.ultimo_id += 1
        self.usuarios.append(
            usuario
        )
        return self.ultimo_id

    def atualizar(
        self,
        usuario,
    ):
        return None

    def listar(self):
        return list(
            self.usuarios
        )

    def listar_colecao(self):
        return self.listar()

    def adicionar_na_colecao(
        self,
        usuario,
    ):
        if usuario not in self.usuarios:
            self.usuarios.append(
                usuario
            )


class UsuarioRepositoryFakeComFalha(
    UsuarioRepositoryFake
):
    def atualizar(
        self,
        usuario,
    ):
        raise RuntimeError(
            "Falha simulada no banco."
        )


def test_falha_ao_atualizar_senha_restaura_hash():
    service = AuthService(
        usuario_repository=(
            UsuarioRepositoryFakeComFalha()
        ),
    )

    service.criar_usuario(
        "admin",
        "senha123",
        Role.ADMIN,
    )

    with pytest.raises(
        RuntimeError,
        match="Falha simulada no banco.",
    ):
        service.alterar_senha(
            nome_usuario="admin",
            senha_atual="senha123",
            nova_senha="nova1234",
            role=Role.ADMIN,
        )

    assert (
        service.autenticar(
            "admin",
            "senha123",
            Role.ADMIN,
        )
        is True
    )

    assert (
        service.autenticar(
            "admin",
            "nova1234",
            Role.ADMIN,
        )
        is False
    )


def criar_service():
    return AuthService(
        usuario_repository=(
            UsuarioRepositoryFake()
        ),
    )


def test_criar_admin():
    service = criar_service()

    admin = (
        service.criar_usuario(
            nome_usuario="admin",
            senha="senha123",
            role=Role.ADMIN,
        )
    )

    assert admin.id == 1
    assert admin.role == Role.ADMIN


def test_nao_criar_usuario_repetido():
    service = criar_service()

    service.criar_usuario(
        "admin",
        "senha123",
        Role.ADMIN,
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.criar_usuario(
            "ADMIN",
            "outrasenha",
            Role.ADMIN,
        )

    assert (
        erro.value.mensagem
        == "Esse usuário já existe."
    )


def test_autenticar_admin():
    service = criar_service()

    service.criar_usuario(
        "admin",
        "senha123",
        Role.ADMIN,
    )

    assert (
        service.autenticar(
            "admin",
            "senha123",
            Role.ADMIN,
        )
        is True
    )


def test_rejeitar_senha_incorreta():
    service = criar_service()

    service.criar_usuario(
        "admin",
        "senha123",
        Role.ADMIN,
    )

    assert (
        service.autenticar(
            "admin",
            "errada123",
            Role.ADMIN,
        )
        is False
    )


def test_cliente_nao_autentica_como_admin():
    service = criar_service()

    service.criar_usuario(
        "lucas",
        "senha123",
        Role.CLIENTE,
    )

    assert (
        service.autenticar(
            "lucas",
            "senha123",
            Role.ADMIN,
        )
        is False
    )


def test_alterar_senha():
    service = criar_service()

    service.criar_usuario(
        "admin",
        "admin123",
        Role.ADMIN,
    )

    mensagem = (
        service.alterar_senha(
            nome_usuario="admin",
            senha_atual="admin123",
            nova_senha="nova1234",
            role=Role.ADMIN,
        )
    )

    assert (
        mensagem
        == "Senha alterada com sucesso."
    )

    assert (
        service.autenticar(
            "admin",
            "admin123",
            Role.ADMIN,
        )
        is False
    )

    assert (
        service.autenticar(
            "admin",
            "nova1234",
            Role.ADMIN,
        )
        is True
    )


def test_nao_alterar_com_senha_atual_errada():
    service = criar_service()

    service.criar_usuario(
        "admin",
        "admin123",
        Role.ADMIN,
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.alterar_senha(
            nome_usuario="admin",
            senha_atual="errada123",
            nova_senha="nova123",
            role=Role.ADMIN,
        )

    assert (
        erro.value.mensagem
        == "Senha atual incorreta."
    )

    assert (
        service.autenticar(
            "admin",
            "admin123",
            Role.ADMIN,
        )
        is True
    )


def test_nao_reutilizar_mesma_senha():
    service = criar_service()

    service.criar_usuario(
        "admin",
        "admin123",
        Role.ADMIN,
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.alterar_senha(
            nome_usuario="admin",
            senha_atual="admin123",
            nova_senha="admin123",
            role=Role.ADMIN,
        )

    assert (
        erro.value.mensagem
        == (
            "A nova senha deve ser "
            "diferente da senha atual."
        )
    )


def test_nao_criar_usuario_com_senha_invalida():
    service = criar_service()

    with pytest.raises(
        RegraDeNegocio
    ):
        service.criar_usuario(
            nome_usuario="admin",
            senha="12345678",
            role=Role.ADMIN,
        )

    assert service.listar_usuarios() == []


def test_usuario_inexistente_nao_autentica():
    service = criar_service()

    resultado = service.autenticar(
        "naoexiste",
        "senha123",
        Role.ADMIN,
    )

    assert resultado is False


def test_usuario_desativado_nao_autentica():
    service = criar_service()

    usuario = (
        service.criar_usuario(
            "admin",
            "senha123",
            Role.ADMIN,
        )
    )

    usuario.desativar()

    assert (
        service.autenticar(
            "admin",
            "senha123",
            Role.ADMIN,
        )
        is False
    )


def test_nao_alterar_senha_usuario_inexistente():
    service = criar_service()

    with pytest.raises(
        RecursoNaoEncontrado
    ) as erro:
        service.alterar_senha(
            nome_usuario="naoexiste",
            senha_atual="senha123",
            nova_senha="nova1234",
            role=Role.ADMIN,
        )

    assert (
        erro.value.mensagem
        == "Usuário não encontrado."
    )


def test_usuario_desativado_nao_altera_senha():
    service = criar_service()

    usuario = (
        service.criar_usuario(
            "admin",
            "senha123",
            Role.ADMIN,
        )
    )

    usuario.desativar()

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.alterar_senha(
            nome_usuario="admin",
            senha_atual="senha123",
            nova_senha="nova1234",
            role=Role.ADMIN,
        )

    assert (
        erro.value.mensagem
        == "Usuário desativado."
    )


def test_nao_alterar_senha_com_role_incorreta():
    service = criar_service()

    service.criar_usuario(
        "lucas",
        "senha123",
        Role.CLIENTE,
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.alterar_senha(
            nome_usuario="lucas",
            senha_atual="senha123",
            nova_senha="nova1234",
            role=Role.ADMIN,
        )

    assert (
        erro.value.mensagem
        == "Usuário sem permissão."
    )


def test_nao_alterar_para_nova_senha_invalida():
    service = criar_service()

    service.criar_usuario(
        "admin",
        "senha123",
        Role.ADMIN,
    )

    with pytest.raises(
        RegraDeNegocio
    ):
        service.alterar_senha(
            nome_usuario="admin",
            senha_atual="senha123",
            nova_senha="12345678",
            role=Role.ADMIN,
        )

    assert (
        service.autenticar(
            "admin",
            "senha123",
            Role.ADMIN,
        )
        is True
    )
