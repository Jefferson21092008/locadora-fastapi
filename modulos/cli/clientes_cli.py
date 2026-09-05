from modulos.interface import (
    AMARELO,
    AZUL,
    BRANCO,
    CIANO,
    RESET,
    VERDE,
    VERMELHO,
    leia_int,
)

from modulos.excecoes import (
    ErroAplicacao,
)


class ClienteCLI:
    """Interface de terminal para operações com clientes."""

    def __init__(
        self,
        cliente_service,
    ):
        self.service = cliente_service

    # ================================================================
    # CADASTRO
    # ================================================================

    def criar_conta(self):
        print(
            f"\n{AZUL}"
            "--- CRIAR CONTA ---"
            f"{RESET}"
        )

        nome = input(
            f"{BRANCO}Nome: {RESET}"
        ).strip()

        usuario = input(
            f"{BRANCO}Usuário: {RESET}"
        ).strip()

        email = input(
            f"{BRANCO}E-mail: {RESET}"
        ).strip()

        senha = input(
            f"{BRANCO}Senha: {RESET}"
        ).strip()

        try:
            cliente = (
                self.service.criar_conta(
                    nome,
                    usuario,
                    email,
                    senha,
                )
            )

        except ErroAplicacao as erro:
            print(
                f"{VERMELHO}"
                f"{erro.mensagem}"
                f"{RESET}"
            )
            return

        print(
            f"{VERDE}"
            "Conta criada com sucesso! "
            f"ID: {cliente.id}"
            f"{RESET}"
        )

    # ================================================================
    # LOGIN
    # ================================================================

    def login(self):
        print(
            f"\n{AZUL}"
            "--- LOGIN DO CLIENTE ---"
            f"{RESET}"
        )

        usuario = input(
            f"{BRANCO}Usuário: {RESET}"
        ).strip()

        senha = input(
            f"{BRANCO}Senha: {RESET}"
        ).strip()

        try:
            cliente = (
                self.service.login(
                    usuario,
                    senha,
                )
            )

        except ErroAplicacao as erro:
            print(
                f"{VERMELHO}"
                f"{erro.mensagem}"
                f"{RESET}"
            )
            return None

        print(
            f"{VERDE}"
            f"Bem-vindo, {cliente.nome}!"
            f"{RESET}"
        )

        return cliente

    # ================================================================
    # DADOS
    # ================================================================

    @staticmethod
    def mostrar_dados(
        cliente,
    ):
        print(
            f"\n{AZUL}"
            "--- MEUS DADOS ---"
            f"{RESET}"
        )

        print(
            f"ID: {cliente.id}"
        )

        print(
            f"Nome: {cliente.nome}"
        )

        print(
            f"Usuário: {cliente.usuario}"
        )

        print(
            f"E-mail: {cliente.email}"
        )

    def listar_clientes(self):
        clientes = (
            self.service
            .listar_clientes()
        )

        print(
            f"\n{AZUL}"
            "--- CLIENTES CADASTRADOS ---"
            f"{RESET}"
        )

        if not clientes:
            print(
                f"{AMARELO}"
                "Nenhum cliente cadastrado."
                f"{RESET}"
            )
            return

        for cliente in clientes:
            status = (
                "ATIVO"
                if cliente.ativo
                else "DESATIVADO"
            )

            print(
                f"\n{CIANO}"
                f"[ {cliente.id} ] "
                f"{cliente.nome}"
                f"{RESET}"
            )

            print(
                f"Usuário: "
                f"@{cliente.usuario}"
            )

            print(
                f"E-mail: "
                f"{cliente.email}"
            )

            print(
                f"Status: {status}"
            )

    # ================================================================
    # SENHA
    # ================================================================

    def alterar_senha(
        self,
        cliente,
    ):
        print(
            f"\n{AZUL}"
            "--- ALTERAR SENHA ---"
            f"{RESET}"
        )

        senha_atual = input(
            f"{BRANCO}"
            "Senha atual: "
            f"{RESET}"
        ).strip()

        nova_senha = input(
            f"{BRANCO}"
            "Nova senha: "
            f"{RESET}"
        ).strip()

        confirmacao = input(
            f"{BRANCO}"
            "Confirme a nova senha: "
            f"{RESET}"
        ).strip()

        if nova_senha != confirmacao:
            print(
                f"{VERMELHO}"
                "As senhas não coincidem."
                f"{RESET}"
            )
            return

        try:
            mensagem = (
                self.service
                .alterar_senha(
                    cliente,
                    senha_atual,
                    nova_senha,
                )
            )

        except ErroAplicacao as erro:
            print(
                f"{VERMELHO}"
                f"{erro.mensagem}"
                f"{RESET}"
            )
            return

        print(
            f"{VERDE}"
            f"{mensagem}"
            f"{RESET}"
        )

    # ================================================================
    # DESATIVAÇÃO
    # ================================================================

    def desativar(self):
        ativos = (
            self.service
            .listar_ativos()
        )

        print(
            f"\n{AZUL}"
            "--- DESATIVAR CLIENTE ---"
            f"{RESET}"
        )

        if not ativos:
            print(
                f"{AMARELO}"
                "Nenhum cliente ativo."
                f"{RESET}"
            )
            return

        for cliente in ativos:
            print(
                f"{CIANO}"
                f"[ {cliente.id} ] "
                f"{cliente.nome} "
                f"(@{cliente.usuario})"
                f"{RESET}"
            )

        id_cliente = leia_int(
            f"\n{BRANCO}"
            "ID do cliente: "
            f"{RESET}"
        )

        try:
            self.service.desativar(
                id_cliente
            )

        except ErroAplicacao as erro:
            print(
                f"{VERMELHO}"
                f"{erro.mensagem}"
                f"{RESET}"
            )
            return

        print(
            f"{VERDE}"
            "Cliente desativado com sucesso!"
            f"{RESET}"
        )

    def reativar(self):
        desativados = (
            self.service
            .listar_desativados()
        )

        print(
            f"\n{AZUL}"
            "--- REATIVAR CLIENTE ---"
            f"{RESET}"
        )

        if not desativados:
            print(
                f"{AMARELO}"
                "Nenhum cliente desativado."
                f"{RESET}"
            )
            return

        for cliente in desativados:
            print(
                f"{CIANO}"
                f"[ {cliente.id} ] "
                f"{cliente.nome}"
                f"{RESET}"
            )

        id_cliente = leia_int(
            f"{BRANCO}"
            "ID do cliente: "
            f"{RESET}"
        )

        try:
            self.service.reativar(
                id_cliente
            )

        except ErroAplicacao as erro:
            print(
                f"{VERMELHO}"
                f"{erro.mensagem}"
                f"{RESET}"
            )
            return

        print(
            f"{VERDE}"
            "Cliente reativado com sucesso!"
            f"{RESET}"
        )
