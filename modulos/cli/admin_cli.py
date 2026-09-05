from modulos.interface import (
    AZUL,
    BRANCO,
    RESET,
    VERDE,
    VERMELHO,
)


from modulos.excecoes import (
    ErroAplicacao,
)

class AdminCLI:
    """Interface de terminal do administrador."""
    def __init__(
        self,
        service,
        veiculo_service,
        manutencao_service,
    ):
        self.service = service
        self.veiculo_service = veiculo_service
        self.manutencao_service = manutencao_service

    def login(self):
        print(
            f"\n{AZUL}"
            "--- LOGIN DO ADMINISTRADOR ---"
            f"{RESET}"
        )

        usuario = input(
            f"{BRANCO}"
            "Usuário: "
            f"{RESET}"
        ).strip()

        senha = input(
            f"{BRANCO}"
            "Senha: "
            f"{RESET}"
        )

        sucesso = (
            self.service.autenticar(
                usuario,
                senha,
            )
        )

        if sucesso:
            print(
                f"{VERDE}"
                "Acesso de administrador "
                "liberado!"
                f"{RESET}"
            )

            return True

        print(
            f"{VERMELHO}"
            "Usuário ou senha incorretos."
            f"{RESET}"
        )

        return False

    def mostrar_veiculos_em_manutencao(
        self,
    ):
        manutencoes = (
            self.manutencao_service
            .listar_ativas()
        )

        if not manutencoes:
            print(
                "\nNenhuma manutenção ativa."
            )
            return

        print(
            "\n=== MANUTENÇÕES ATIVAS ==="
        )

        for manutencao in manutencoes:
            veiculo = (
                self.veiculo_service
                .buscar_por_id(
                    manutencao.veiculo_id
                )
            )

            if veiculo is None:
                continue

            print(
                "\n--------------------------"
                f"\nManutenção: "
                f"#{manutencao.id}"
                f"\nVeículo: "
                f"#{veiculo.id} "
                f"{veiculo.tipo} - "
                f"{veiculo.modelo}"
                f"\nMotivo: "
                f"{manutencao.motivo}"
                f"\nQuilometragem: "
                f"{manutencao.quilometragem:.1f} km"
                f"\nData de início: "
                f"{manutencao.data_inicio}"
                f"\nStatus: "
                f"{manutencao.status}"
            )

    def enviar_veiculo_para_manutencao(
        self,
    ):
        try:
            id_veiculo = int(
                input(
                    "\nID do veículo: "
                )
            )

        except ValueError:
            print(
                "\nID inválido."
            )
            return

        veiculo = (
            self.veiculo_service
            .buscar_por_id(
                id_veiculo
            )
        )

        if veiculo is None:
            print(
                "\nVeículo não encontrado."
            )
            return

        motivo = input(
            "Motivo da manutenção: "
        ).strip()

        try:
            manutencao = (
                self.manutencao_service
                .abrir(
                    id_veiculo=id_veiculo,
                    motivo=motivo,
                )
            )

        except ErroAplicacao as erro:
            print(
                f"\n{erro.mensagem}"
            )
            return

        print(
            "\nManutenção aberta "
            "com sucesso."
        )

        print(
            f"\nID da manutenção: "
            f"{manutencao.id}"
            f"\nVeículo: "
            f"{veiculo.tipo} - "
            f"{veiculo.modelo}"
            f"\nMotivo: "
            f"{manutencao.motivo}"
            f"\nQuilometragem: "
            f"{manutencao.quilometragem:.1f} km"
            f"\nData de início: "
            f"{manutencao.data_inicio}"
        )

    def finalizar_manutencao_veiculo(
        self,
    ):
        manutencoes = (
            self.manutencao_service
            .listar_ativas()
        )

        if not manutencoes:
            print(
                "\nNenhuma manutenção ativa."
            )
            return

        print(
            "\n=== MANUTENÇÕES ATIVAS ==="
        )

        for manutencao in manutencoes:
            veiculo = (
                self.veiculo_service
                .buscar_por_id(
                    manutencao.veiculo_id
                )
            )

            if veiculo is None:
                continue

            print(
                f"\nVeículo ID: "
                f"{veiculo.id}"
                f"\n{veiculo.tipo}: "
                f"{veiculo.modelo}"
                f"\nMotivo: "
                f"{manutencao.motivo}"
                f"\nInício: "
                f"{manutencao.data_inicio}"
            )

        try:
            id_veiculo = int(
                input(
                    "\nID do veículo: "
                )
            )

        except ValueError:
            print(
                "\nID inválido."
            )
            return

        try:
            custo = float(
                input(
                    "Custo da manutenção: R$ "
                )
                .strip()
                .replace(
                    ",",
                    ".",
                )
            )

        except ValueError:
            print(
                "\nCusto inválido."
            )
            return

        try:
            manutencao = (
                self.manutencao_service
                .finalizar(
                    id_veiculo=id_veiculo,
                    custo=custo,
                )
            )

        except ErroAplicacao as erro:
            print(
                f"\n{erro.mensagem}"
            )
            return

        print(
            "\nManutenção finalizada "
            "com sucesso."
        )

        print(
            f"\nCusto: "
            f"R$ {manutencao.custo:.2f}"
            f"\nData de conclusão: "
            f"{manutencao.data_fim}"
        )

    def mostrar_historico_manutencao(
        self,
    ):
        try:
            id_veiculo = int(
                input(
                    "\nID do veículo: "
                )
            )

        except ValueError:
            print(
                "\nID inválido."
            )
            return

        veiculo = (
            self.veiculo_service
            .buscar_por_id(
                id_veiculo
            )
        )

        if veiculo is None:
            print(
                "\nVeículo não encontrado."
            )
            return

        historico = (
            self.manutencao_service
            .listar_por_veiculo(
                id_veiculo
            )
        )

        if not historico:
            print(
                "\nEsse veículo ainda não "
                "possui histórico de manutenção."
            )
            return

        print(
            "\n=== HISTÓRICO DE MANUTENÇÃO ==="
        )

        print(
            f"\nVeículo: "
            f"{veiculo.tipo} - "
            f"{veiculo.modelo}"
        )

        for manutencao in historico:
            print(
                "\n--------------------------"
                f"\nManutenção: "
                f"#{manutencao.id}"
                f"\nMotivo: "
                f"{manutencao.motivo}"
                f"\nQuilometragem: "
                f"{manutencao.quilometragem:.1f} km"
                f"\nInício: "
                f"{manutencao.data_inicio}"
                f"\nFim: "
                f"{manutencao.data_fim or '-'}"
                f"\nCusto: "
                f"R$ {manutencao.custo:.2f}"
                f"\nStatus: "
                f"{manutencao.status}"
            )

    def alterar_senha(
        self,
    ):
        print(
            f"\n{AZUL}"
            "--- ALTERAR SENHA DO ADMINISTRADOR ---"
            f"{RESET}"
        )

        usuario = input(
            f"{BRANCO}"
            "Usuário: "
            f"{RESET}"
        ).strip()

        senha_atual = input(
            f"{BRANCO}"
            "Senha atual: "
            f"{RESET}"
        )

        nova_senha = input(
            f"{BRANCO}"
            "Nova senha: "
            f"{RESET}"
        )

        confirmar_senha = input(
            f"{BRANCO}"
            "Confirme a nova senha: "
            f"{RESET}"
        )

        if nova_senha != confirmar_senha:
            print(
                f"\n{VERMELHO}"
                "As novas senhas não coincidem."
                f"{RESET}"
            )
            return

        try:
            mensagem = (
                self.service.alterar_senha(
                    usuario=usuario,
                    senha_atual=senha_atual,
                    nova_senha=nova_senha,
                )
            )

        except ErroAplicacao as erro:
            print(
                f"\n{VERMELHO}"
                f"{erro.mensagem}"
                f"{RESET}"
            )
            return

        print(
            f"\n{VERDE}"
            f"{mensagem}"
            f"{RESET}"
        )
