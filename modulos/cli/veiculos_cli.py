from modulos.interface import (
    AMARELO,
    AZUL,
    BRANCO,
    CIANO,
    RESET,
    VERDE,
    VERMELHO,
    leia_float,
    leia_int,
)

from modulos.veiculos import (
    StatusVeiculo,
)

from modulos.excecoes import (
    ErroAplicacao,
)


class VeiculoCLI:
    """Interface de terminal para operações com veículos."""

    def __init__(
        self,
        veiculo_service,
    ):
        self.service = veiculo_service

    # ================================================================
    # EXIBIÇÃO
    # ================================================================

    @staticmethod
    def _mostrar_veiculo(
        veiculo,
    ):
        status_textos = {
            StatusVeiculo.DISPONIVEL: (
                "DISPONÍVEL"
            ),
            StatusVeiculo.ALUGADO: (
                "ALUGADO"
            ),
            StatusVeiculo.MANUTENCAO: (
                "MANUTENÇÃO"
            ),
            StatusVeiculo.DESATIVADO: (
                "DESATIVADO"
            ),
        }

        status = status_textos.get(
            veiculo.status,
            str(
                veiculo.status
            ),
        )

        frota = (
            "ATIVO"
            if veiculo.ativo
            else "DESATIVADO"
        )

        print(
            f"\n{CIANO}"
            f"[ {veiculo.id} ] "
            f"{veiculo.tipo} - "
            f"{veiculo.modelo}"
            f"{RESET}"
        )

        print(
            f"Ano: {veiculo.ano}"
        )

        print(
            f"Diária: "
            f"R$ {veiculo.diaria:.2f}"
        )

        print(
            f"Preço por km: "
            f"R$ {veiculo.preco_km:.2f}"
        )

        print(
            f"Status: {status}"
        )

        print(
            f"Frota: {frota}"
        )

    # ================================================================
    # LISTAGENS
    # ================================================================

    def mostrar_disponiveis(
        self,
    ):
        veiculos = (
            self.service
            .listar_disponiveis()
        )

        print(
            f"\n{AZUL}"
            "--- VEÍCULOS DISPONÍVEIS ---"
            f"{RESET}"
        )

        if not veiculos:
            print(
                f"{AMARELO}"
                "Nenhum veículo disponível."
                f"{RESET}"
            )
            return

        for veiculo in veiculos:
            self._mostrar_veiculo(
                veiculo
            )

    def mostrar_frota(
        self,
    ):
        veiculos = (
            self.service
            .listar_todos()
        )

        if not veiculos:
            print(
                "\nNenhum veículo "
                "cadastrado."
            )
            return

        print(
            "\n--- FROTA COMPLETA ---"
        )

        for veiculo in veiculos:
            self._mostrar_veiculo(
                veiculo
            )

    def mostrar_alugados(
        self,
    ):
        veiculos = (
            self.service
            .listar_alugados()
        )

        print(
            f"\n{AZUL}"
            "--- VEÍCULOS ALUGADOS ---"
            f"{RESET}"
        )

        if not veiculos:
            print(
                f"{AMARELO}"
                "Nenhum veículo alugado."
                f"{RESET}"
            )
            return

        for veiculo in veiculos:
            self._mostrar_veiculo(
                veiculo
            )

            print(
                "Alugado por: "
                f"{veiculo.alugado_por}"
            )

    # ================================================================
    # BUSCA
    # ================================================================

    def buscar(
        self,
    ):
        print(
            f"\n{AZUL}"
            "--- BUSCAR VEÍCULO ---"
            f"{RESET}"
        )

        termo = input(
            f"{BRANCO}"
            "Modelo ou tipo: "
            f"{RESET}"
        ).strip()

        veiculos = (
            self.service.buscar(
                termo
            )
        )

        if not veiculos:
            print(
                f"{AMARELO}"
                "Nenhum veículo encontrado."
                f"{RESET}"
            )
            return

        print(
            f"\n{AZUL}"
            "--- RESULTADOS ---"
            f"{RESET}"
        )

        for veiculo in veiculos:
            self._mostrar_veiculo(
                veiculo
            )

    # ================================================================
    # CADASTRO
    # ================================================================

    def cadastrar(
        self,
    ):
        print(
            f"\n{AZUL}"
            "--- CADASTRAR VEÍCULO ---"
            f"{RESET}"
        )

        print(
            "Tipos: Carro, Moto, "
            "Caminhão e Bicicleta"
        )

        tipo = input(
            f"{BRANCO}"
            "Tipo: "
            f"{RESET}"
        ).strip()

        modelo = input(
            f"{BRANCO}"
            "Modelo: "
            f"{RESET}"
        ).strip()

        ano = leia_int(
            f"{BRANCO}"
            "Ano: "
            f"{RESET}"
        )

        diaria = leia_float(
            f"{BRANCO}"
            "Diária: R$ "
            f"{RESET}"
        )

        preco_km = leia_float(
            f"{BRANCO}"
            "Preço por km: R$ "
            f"{RESET}"
        )

        try:
            veiculo = (
                self.service.cadastrar(
                    tipo,
                    modelo,
                    ano,
                    diaria,
                    preco_km,
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
            f"{veiculo.modelo} "
            "cadastrado com sucesso!"
            f"{RESET}"
        )

    # ================================================================
    # EDIÇÃO
    # ================================================================

    def editar(
        self,
    ):
        self.mostrar_frota()

        id_veiculo = leia_int(
            f"\n{BRANCO}"
            "ID do veículo: "
            f"{RESET}"
        )

        print(
            f"""
{AZUL}--- EDITAR VEÍCULO ---{RESET}

{BRANCO}[ 1 ] Modelo
[ 2 ] Ano
[ 3 ] Diária
[ 4 ] Preço por km
[ 5 ] Cancelar{RESET}
"""
        )

        opcao = leia_int(
            f"{BRANCO}"
            "Escolha: "
            f"{RESET}"
        )

        try:
            if opcao == 1:
                modelo = input(
                    "Novo modelo: "
                ).strip()

                self.service.editar(
                    id_veiculo,
                    modelo=modelo,
                )

            elif opcao == 2:
                ano = leia_int(
                    "Novo ano: "
                )

                self.service.editar(
                    id_veiculo,
                    ano=ano,
                )

            elif opcao == 3:
                diaria = leia_float(
                    "Nova diária: R$ "
                )

                self.service.editar(
                    id_veiculo,
                    diaria=diaria,
                )

            elif opcao == 4:
                preco_km = leia_float(
                    "Novo preço por km: "
                    "R$ "
                )

                self.service.editar(
                    id_veiculo,
                    preco_km=preco_km,
                )

            elif opcao == 5:
                print(
                    f"{AMARELO}"
                    "Edição cancelada."
                    f"{RESET}"
                )
                return

            else:
                print(
                    f"{VERMELHO}"
                    "Opção inválida."
                    f"{RESET}"
                )
                return

        except ErroAplicacao as erro:
            print(
                f"{VERMELHO}"
                f"{erro.mensagem}"
                f"{RESET}"
            )
            return

        print(
            f"{VERDE}"
            "Veículo atualizado "
            "com sucesso!"
            f"{RESET}"
        )

    # ================================================================
    # DESATIVAÇÃO
    # ================================================================

    def desativar(
        self,
    ):
        self.mostrar_frota()

        id_veiculo = leia_int(
            f"\n{BRANCO}"
            "ID do veículo que deseja "
            "desativar: "
            f"{RESET}"
        )

        try:
            self.service.desativar(
                id_veiculo
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
            "Veículo desativado "
            "com sucesso!"
            f"{RESET}"
        )

    # ================================================================
    # REATIVAÇÃO
    # ================================================================

    def reativar(
        self,
    ):
        desativados = (
            self.service
            .listar_desativados()
        )

        print(
            f"\n{AZUL}"
            "--- VEÍCULOS DESATIVADOS ---"
            f"{RESET}"
        )

        if not desativados:
            print(
                f"{AMARELO}"
                "Nenhum veículo "
                "desativado."
                f"{RESET}"
            )
            return

        for veiculo in desativados:
            self._mostrar_veiculo(
                veiculo
            )

        id_veiculo = leia_int(
            f"\n{BRANCO}"
            "ID do veículo: "
            f"{RESET}"
        )

        try:
            self.service.reativar(
                id_veiculo
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
            "Veículo reativado "
            "com sucesso!"
            f"{RESET}"
        )