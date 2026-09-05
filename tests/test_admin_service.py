from modulos.servicos.admin_service import (
    AdminService,
)

from modulos.servicos.auth_service import (
    AuthService,
)

from modulos.usuarios import (
    Role,
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


def criar_service():
    auth_service = AuthService(
        usuario_repository=(
            UsuarioRepositoryFake()
        ),
    )

    admin = (
        auth_service.criar_usuario(
            nome_usuario="admin",
            senha="admin123",
            role=Role.ADMIN,
        )
    )

    return AdminService(
        auth_service
    )

def test_admin_autentica():
    service = criar_service()

    assert (
        service.autenticar(
            "admin",
            "admin123",
        )
        is True
    )


def test_admin_rejeita_senha_errada():
    service = criar_service()

    assert (
        service.autenticar(
            "admin",
            "errada123",
        )
        is False
    )


def test_admin_rejeita_usuario_errado():
    service = criar_service()

    assert (
        service.autenticar(
            "outro",
            "admin123",
        )
        is False
    )

def test_admin_pode_alterar_senha():
    service = criar_service()

    mensagem = (
        service.alterar_senha(
            usuario="admin",
            senha_atual="admin123",
            nova_senha="nova1234",
        )
    )

    assert (
        mensagem
        == "Senha alterada com sucesso."
    )

    # Senha antiga não funciona mais
    assert (
        service.autenticar(
            "admin",
            "admin123",
        )
        is False
    )

    # Senha nova funciona
    assert (
        service.autenticar(
            "admin",
            "nova1234",
        )
        is True
    )