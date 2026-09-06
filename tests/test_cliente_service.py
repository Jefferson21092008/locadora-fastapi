import pytest

from modulos.clientes import (
    Cliente,
)
from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)
from modulos.servicos.auth_service import (
    AuthService,
)
from modulos.servicos.clientes_service import (
    ClienteService,
)
from modulos.usuarios import (
    Role,
)


class UsuarioRepositoryFake:
    def __init__(self):
        self.usuarios = []
        self.proximo_id = 1

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
        usuario.id = self.proximo_id
        self.proximo_id += 1
        self.usuarios.append(
            usuario
        )
        return usuario.id

    def atualizar(
        self,
        usuario,
    ):
        return None

    def listar(self):
        return list(
            self.usuarios
        )


class ClienteRepositoryFake:
    def __init__(
        self,
        usuario_repository,
    ):
        self.usuario_repository = (
            usuario_repository
        )
        self.clientes = []
        self.proximo_id = 1
        self.falhar_status = False
        self.falhar_renomeacao = False

    def buscar_por_id(
        self,
        id_cliente,
    ):
        for cliente in self.clientes:
            if cliente.id == id_cliente:
                return cliente

        return None

    def buscar_por_usuario_id(
        self,
        usuario_id,
    ):
        for cliente in self.clientes:
            if cliente.usuario_id == usuario_id:
                return cliente

        return None

    def buscar_por_usuario(
        self,
        usuario,
    ):
        usuario = (
            str(usuario)
            .strip()
            .lower()
        )

        for cliente in self.clientes:
            if cliente.usuario.lower() == usuario:
                return cliente

        return None

    def buscar_por_email(
        self,
        email,
    ):
        if not email:
            return None

        email = (
            str(email)
            .strip()
            .lower()
        )

        for cliente in self.clientes:
            if cliente.email.lower() == email:
                return cliente

        return None

    def registrar_com_usuario(
        self,
        cliente,
        usuario,
    ):
        cliente.id = self.proximo_id
        self.proximo_id += 1

        usuario.id = (
            self.usuario_repository
            .proximo_id
        )
        self.usuario_repository.proximo_id += 1

        cliente.usuario_id = usuario.id

        self.clientes.append(
            cliente
        )
        self.usuario_repository.usuarios.append(
            usuario
        )

        return (
            cliente.id,
            usuario.id,
        )

    def atualizar_status_com_usuario(
        self,
        cliente_id,
        usuario_id,
        ativo,
    ):
        if self.falhar_status:
            raise RuntimeError(
                "Falha simulada no banco."
            )

        cliente = self.buscar_por_id(
            cliente_id
        )
        usuario = (
            self.usuario_repository
            .buscar_por_id(
                usuario_id
            )
        )

        if cliente is not None:
            cliente.ativo = bool(
                ativo
            )

        if usuario is not None:
            usuario.ativo = bool(
                ativo
            )

    def renomear_usuario_com_conta(
        self,
        usuario_id,
        novo_usuario,
    ):
        if self.falhar_renomeacao:
            raise RuntimeError(
                "Falha simulada na renomeação."
            )

        cliente = (
            self.buscar_por_usuario_id(
                usuario_id
            )
        )

        usuario = (
            self.usuario_repository
            .buscar_por_id(
                usuario_id
            )
        )

        if (
            cliente is None
            or usuario is None
        ):
            raise RuntimeError(
                "Cliente ou usuário "
                "não encontrado."
            )

        cliente.usuario = novo_usuario
        usuario.usuario = novo_usuario

    def listar(self):
        return list(
            self.clientes
        )

    def listar_ativos(self):
        return [
            cliente
            for cliente in self.clientes
            if cliente.ativo
        ]

    def listar_desativados(self):
        return [
            cliente
            for cliente in self.clientes
            if not cliente.ativo
        ]


class AluguelRepositoryFake:
    def __init__(
        self,
        alugueis=None,
    ):
        self.alugueis = (
            alugueis
            if alugueis is not None
            else []
        )

    def buscar_ativo(
        self,
        cliente,
    ):
        for aluguel in self.alugueis:
            if (
                aluguel.ativo
                and aluguel.pertence_ao_cliente(
                    cliente
                )
            ):
                return aluguel

        return None


class AluguelFake:
    def __init__(
        self,
        cliente,
        ativo=True,
    ):
        self.cliente = cliente
        self.ativo = ativo

    def pertence_ao_cliente(
        self,
        cliente,
    ):
        return self.cliente.id == cliente.id


def criar_service(
    alugueis=None,
    auth_service_configurado=True,
):
    usuario_repository = (
        UsuarioRepositoryFake()
    )

    auth_service = (
        AuthService(
            usuario_repository=(
                usuario_repository
            ),
        )
        if auth_service_configurado
        else None
    )

    cliente_repository = (
        ClienteRepositoryFake(
            usuario_repository
        )
    )

    aluguel_repository = (
        AluguelRepositoryFake(
            alugueis
        )
    )

    service = ClienteService(
        auth_service=auth_service,
        cliente_repository=(
            cliente_repository
        ),
        aluguel_repository=(
            aluguel_repository
        ),
    )

    return service


def cadastrar_cliente(
    service,
):
    return service.criar_conta(
        nome="Lucas Silva",
        usuario="lucas",
        email="lucas@email.com",
        senha="lucas123",
    )


def test_criar_conta():
    service = criar_service()

    resultado = cadastrar_cliente(
        service
    )

    assert isinstance(
        resultado,
        Cliente,
    )
    assert resultado.id == 1
    assert resultado.nome == "Lucas Silva"
    assert resultado.usuario == "lucas"
    assert resultado.email == "lucas@email.com"
    assert resultado.usuario_id == 1

    assert len(
        service.cliente_repository.listar()
    ) == 1
    assert len(
        service.auth_service.listar_usuarios()
    ) == 1

    conta = service.auth_service.buscar_por_id(
        resultado.usuario_id
    )

    assert conta.id == 1
    assert conta.usuario == "lucas"
    assert conta.role == Role.CLIENTE
    assert conta.validar_senha(
        "lucas123"
    )


def test_nao_permitir_usuario_repetido():
    service = criar_service()
    cadastrar_cliente(
        service
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.criar_conta(
            nome="Outro Lucas",
            usuario="lucas",
            email="outro@email.com",
            senha="senha123",
        )

    assert erro.value.mensagem == (
        "Esse usuário já está cadastrado."
    )
    assert len(
        service.cliente_repository.listar()
    ) == 1
    assert len(
        service.auth_service.listar_usuarios()
    ) == 1


def test_nao_permitir_email_repetido():
    service = criar_service()
    cadastrar_cliente(
        service
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.criar_conta(
            nome="João Silva",
            usuario="joao",
            email="lucas@email.com",
            senha="joao1234",
        )

    assert erro.value.mensagem == (
        "Esse e-mail já está cadastrado."
    )
    assert len(
        service.cliente_repository.listar()
    ) == 1


def test_buscar_cliente_por_id():
    service = criar_service()
    cliente = cadastrar_cliente(
        service
    )

    encontrado = service.buscar_por_id(
        cliente.id
    )

    assert encontrado is cliente


def test_login_correto():
    service = criar_service()
    cliente = cadastrar_cliente(
        service
    )

    resultado = service.login(
        "lucas",
        "lucas123",
    )

    assert resultado is cliente


def test_login_usuario_inexistente():
    service = criar_service()
    cadastrar_cliente(
        service
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.login(
            "naoexiste",
            "lucas123",
        )

    assert erro.value.mensagem == (
        "Usuário ou senha incorretos."
    )


def test_login_senha_errada():
    service = criar_service()
    cadastrar_cliente(
        service
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.login(
            "lucas",
            "senhaerrada",
        )

    assert erro.value.mensagem == (
        "Usuário ou senha incorretos."
    )


def test_cliente_desativado_nao_pode_fazer_login():
    service = criar_service()
    cliente = cadastrar_cliente(
        service
    )
    service.desativar(
        cliente.id
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.login(
            "lucas",
            "lucas123",
        )

    assert erro.value.mensagem == (
        "Usuário ou senha incorretos."
    )


def test_alterar_senha():
    service = criar_service()
    cliente = cadastrar_cliente(
        service
    )

    conta = service.buscar_conta_do_cliente(
        cliente
    )

    mensagem = service.alterar_senha(
        cliente,
        senha_atual="lucas123",
        nova_senha="nova1234",
    )

    assert mensagem == (
        "Senha alterada com sucesso."
    )
    assert conta.validar_senha(
        "nova1234"
    )
    assert not conta.validar_senha(
        "lucas123"
    )

    with pytest.raises(
        RegraDeNegocio
    ):
        service.login(
            "lucas",
            "lucas123",
        )

    assert service.login(
        "lucas",
        "nova1234",
    ) is cliente


def test_desativar_cliente():
    service = criar_service()
    cliente = cadastrar_cliente(
        service
    )
    conta = service.buscar_conta_do_cliente(
        cliente
    )

    resultado = service.desativar(
        cliente.id
    )

    assert resultado is cliente
    assert cliente.ativo is False
    assert conta.ativo is False


def test_reativar_cliente():
    service = criar_service()
    cliente = cadastrar_cliente(
        service
    )
    conta = service.buscar_conta_do_cliente(
        cliente
    )

    service.desativar(
        cliente.id
    )
    resultado = service.reativar(
        cliente.id
    )

    assert resultado is cliente
    assert cliente.ativo is True
    assert conta.ativo is True


def test_nao_desativar_cliente_com_aluguel_ativo():
    alugueis = []
    service = criar_service(
        alugueis=alugueis
    )
    cliente = cadastrar_cliente(
        service
    )
    conta = service.buscar_conta_do_cliente(
        cliente
    )

    alugueis.append(
        AluguelFake(
            cliente=cliente,
            ativo=True,
        )
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.desativar(
            cliente.id
        )

    assert cliente.ativo is True
    assert conta.ativo is True
    assert erro.value.mensagem == (
        "Não é possível desativar "
        "um cliente com aluguel ativo."
    )


def test_nao_permitir_email_vazio():
    service = criar_service()

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.criar_conta(
            nome="Lucas Silva",
            usuario="lucas",
            email="",
            senha="lucas123",
        )

    assert erro.value.mensagem == (
        "O e-mail não pode ficar vazio."
    )


def test_nao_permitir_email_invalido():
    service = criar_service()

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.criar_conta(
            nome="Lucas Silva",
            usuario="lucas",
            email="email-invalido",
            senha="lucas123",
        )

    assert erro.value.mensagem == (
        "E-mail inválido."
    )


def test_desativar_cliente_inexistente():
    service = criar_service()

    with pytest.raises(
        RecursoNaoEncontrado
    ) as erro:
        service.desativar(
            999
        )

    assert erro.value.mensagem == (
        "Cliente não encontrado."
    )


def test_reativar_cliente_inexistente():
    service = criar_service()

    with pytest.raises(
        RecursoNaoEncontrado
    ) as erro:
        service.reativar(
            999
        )

    assert erro.value.mensagem == (
        "Cliente não encontrado."
    )


def test_criar_conta_sem_auth_service():
    service = criar_service(
        auth_service_configurado=False
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.criar_conta(
            nome="Lucas Silva",
            usuario="lucas",
            email="lucas@email.com",
            senha="lucas123",
        )

    assert erro.value.mensagem == (
        "Serviço de autenticação não configurado."
    )


def test_login_sem_auth_service():
    service = criar_service(
        auth_service_configurado=False
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.login(
            "lucas",
            "lucas123",
        )

    assert erro.value.mensagem == (
        "Serviço de autenticação não configurado."
    )


def test_falha_ao_desativar_restaura_estado():
    service = criar_service()
    cliente = cadastrar_cliente(
        service
    )
    conta = service.buscar_conta_do_cliente(
        cliente
    )

    service.cliente_repository.falhar_status = True

    with pytest.raises(
        RuntimeError,
        match="Falha simulada no banco.",
    ):
        service.desativar(
            cliente.id
        )

    assert cliente.ativo is True
    assert conta.ativo is True


def test_falha_ao_reativar_restaura_estado():
    service = criar_service()
    cliente = cadastrar_cliente(
        service
    )
    conta = service.buscar_conta_do_cliente(
        cliente
    )

    service.desativar(
        cliente.id
    )
    assert cliente.ativo is False
    assert conta.ativo is False

    service.cliente_repository.falhar_status = True

    with pytest.raises(
        RuntimeError,
        match="Falha simulada no banco.",
    ):
        service.reativar(
            cliente.id
        )

    assert cliente.ativo is False
    assert conta.ativo is False


def test_service_exige_cliente_repository():
    with pytest.raises(
        ValueError,
        match="ClienteRepository é obrigatório",
    ):
        ClienteService(
            auth_service=None,
            cliente_repository=None,
            aluguel_repository=(
                AluguelRepositoryFake()
            ),
        )


def test_service_exige_aluguel_repository():
    usuario_repository = (
        UsuarioRepositoryFake()
    )

    with pytest.raises(
        ValueError,
        match="AluguelRepository é obrigatório",
    ):
        ClienteService(
            auth_service=None,
            cliente_repository=(
                ClienteRepositoryFake(
                    usuario_repository
                )
            ),
            aluguel_repository=None,
        )

def test_renomear_usuario():
    service = criar_service()
    cliente = cadastrar_cliente(
        service
    )

    resultado = service.renomear_usuario(
        cliente=cliente,
        novo_usuario="lucas.novo",
        senha_atual="lucas123",
    )

    conta = (
        service.buscar_conta_do_cliente(
            cliente
        )
    )

    assert resultado is cliente
    assert cliente.usuario == "lucas.novo"
    assert conta.usuario == "lucas.novo"

    assert (
        service.login(
            "lucas.novo",
            "lucas123",
        )
        is cliente
    )


def test_renomear_usuario_rejeita_senha_errada():
    service = criar_service()
    cliente = cadastrar_cliente(
        service
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.renomear_usuario(
            cliente=cliente,
            novo_usuario="lucas.novo",
            senha_atual="errada",
        )

    assert erro.value.mensagem == (
        "Senha atual incorreta."
    )


def test_renomear_usuario_rejeita_mesmo_nome():
    service = criar_service()
    cliente = cadastrar_cliente(
        service
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.renomear_usuario(
            cliente=cliente,
            novo_usuario="LUCAS",
            senha_atual="lucas123",
        )

    assert erro.value.mensagem == (
        "O novo usuário deve ser "
        "diferente do atual."
    )


def test_falha_ao_renomear_restaura_estado():
    service = criar_service()
    cliente = cadastrar_cliente(
        service
    )

    conta = (
        service.buscar_conta_do_cliente(
            cliente
        )
    )

    service.cliente_repository.falhar_renomeacao = (
        True
    )

    with pytest.raises(
        RuntimeError,
        match="Falha simulada na renomeação.",
    ):
        service.renomear_usuario(
            cliente=cliente,
            novo_usuario="lucas.novo",
            senha_atual="lucas123",
        )

    assert cliente.usuario == "lucas"
    assert conta.usuario == "lucas"