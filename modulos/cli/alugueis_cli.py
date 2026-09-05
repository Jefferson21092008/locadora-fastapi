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


from modulos.excecoes import (
    ErroAplicacao,
)


class AluguelCLI:
    """Interface de terminal para operações com aluguéis."""

    def __init__(
        self,
        aluguel_service,
        veiculo_cli,
    ):
        self.service = aluguel_service
        self.veiculo_cli = veiculo_cli

    # ================================================================
    # ALUGAR
    # ================================================================

    def alugar(
        self,
        cliente,
    ):
        print(
            f"\n{AZUL}"
            "--- NOVO ALUGUEL ---"
            f"{RESET}"
        )

        disponiveis = (
            self.service
            .listar_veiculos_disponiveis()
        )

        if not disponiveis:
            print(
                f"{AMARELO}"
                "Nenhum veículo disponível."
                f"{RESET}"
            )
            return

        self.veiculo_cli.mostrar_disponiveis()

        id_veiculo = leia_int(
            f"\n{BRANCO}"
            "Digite o ID do veículo: "
            f"{RESET}"
        )

        try:
            veiculo = (
                self.service
                .obter_veiculo_disponivel(
                    id_veiculo
                )
            )

        except ErroAplicacao as erro:
            print(
                f"{VERMELHO}"
                f"{erro.mensagem}"
                f"{RESET}"
            )
            return

        anos_habilitacao = None

        if (
            veiculo.ANOS_MINIMOS_HABILITACAO
            > 0
        ):
            anos_habilitacao = leia_int(
                f"{BRANCO}"
                "Quantos anos possui "
                "de habilitação? "
                f"{RESET}"
            )

        dias = leia_int(
            f"{BRANCO}"
            "Quantidade de dias: "
            f"{RESET}"
        )

        try:
            aluguel = (
                self.service.alugar(
                    cliente=cliente,
                    id_veiculo=id_veiculo,
                    dias=dias,
                    anos_habilitacao=(
                        anos_habilitacao
                    ),
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
            f"\n{VERDE}"
            "Aluguel iniciado com sucesso!"
            f"{RESET}"
        )

        print(
            f"Aluguel ID: {aluguel.id}"
        )

        print(
            f"Veículo: "
            f"{aluguel.veiculo_tipo} - "
            f"{aluguel.veiculo_modelo}"
        )

        print(
            f"Dias contratados: "
            f"{aluguel.dias}"
        )

        print(
            f"Data prevista para devolução: "
            f"{aluguel.data_prevista}"
        )

    # ================================================================
    # DEVOLVER
    # ================================================================

    def devolver(
        self,
        cliente,
    ):
        print(
            f"\n{AZUL}"
            "--- DEVOLVER VEÍCULO ---"
            f"{RESET}"
        )

        ativos = (
            self.service
            .listar_ativos_cliente(
                cliente
            )
        )

        if not ativos:
            print(
                f"{AMARELO}"
                "Você não possui "
                "veículos alugados."
                f"{RESET}"
            )
            return

        for aluguel in ativos:
            print(
                f"{CIANO}"
                f"[ {aluguel.veiculo_id} ] "
                f"{aluguel.veiculo_tipo} - "
                f"{aluguel.veiculo_modelo}"
                f"{RESET}"
            )

        id_veiculo = leia_int(
            f"\n{BRANCO}"
            "Digite o ID do veículo: "
            f"{RESET}"
        )

        km = leia_float(
            f"{BRANCO}"
            "Quilômetros percorridos: "
            f"{RESET}"
        )

        forma_pagamento, parcelas = (
            self._escolher_pagamento()
        )

        try:
            resultado = (
                self.service.devolver(
                    cliente=cliente,
                    id_veiculo=id_veiculo,
                    km=km,
                    forma_pagamento=(
                        forma_pagamento
                    ),
                    parcelas=parcelas,
                )
            )

        except ErroAplicacao as erro:
            print(
                f"{VERMELHO}"
                f"{erro.mensagem}"
                f"{RESET}"
            )
            return

        aluguel = resultado[
            "aluguel"
        ]

        pagamento = resultado[
            "pagamento"
        ]

        print(
            f"\n{AZUL}"
            "--- RESUMO DA DEVOLUÇÃO ---"
            f"{RESET}"
        )

        print(
            f"Veículo: "
            f"{aluguel.veiculo_tipo} - "
            f"{aluguel.veiculo_modelo}"
        )

        print(
            f"Dias: {aluguel.dias}"
        )

        print(
            f"Km: {aluguel.km:.1f}"
        )

        print(
            f"Valor inicial: "
            f"R$ "
            f"{resultado['valor_inicial']:.2f}"
        )

        print(
            f"Data prevista: "
            f"{aluguel.data_prevista}"
        )

        print(
            f"Valor do aluguel: "
            f"R$ {resultado['valor_aluguel']:.2f}"
        )

        if resultado["dias_atraso"] > 0:
            print(
                f"{VERMELHO}"
                f"Atraso: "
                f"{resultado['dias_atraso']} dia(s)"
                f"{RESET}"
            )

            print(
                f"{VERMELHO}"
                f"Multa: "
                f"R$ {resultado['multa']:.2f}"
                f"{RESET}"
            )

        print(
            f"Total antes do pagamento: "
            f"R$ {resultado['valor_inicial']:.2f}"
        )

        print(
            f"Pagamento: "
            f"{pagamento['forma']}"
        )

        if pagamento["parcelas"] > 1:
            print(
                f"Parcelas: "
                f"{pagamento['parcelas']}x "
                f"de R$ "
                f"{pagamento['valor_parcela']:.2f}"
            )

        print(
            f"{VERDE}"
            f"Valor final: "
            f"R$ {aluguel.valor:.2f}"
            f"{RESET}"
        )

        print(
            f"{VERDE}"
            "Devolução realizada com sucesso!"
            f"{RESET}"
        )

    # ================================================================
    # PAGAMENTO
    # ================================================================

    @staticmethod
    def _escolher_pagamento():
        while True:
            print(
                f"""
{AZUL}--- FORMAS DE PAGAMENTO ---{RESET}

{BRANCO}[ 1 ] Dinheiro
[ 2 ] Pix
[ 3 ] Cartão de débito
[ 4 ] Crédito à vista
[ 5 ] Crédito parcelado
[ 6 ] Boleto
[ 7 ] Transferência bancária{RESET}
"""
            )

            opcao = leia_int(
                f"{BRANCO}"
                "Escolha: "
                f"{RESET}"
            )

            if not 1 <= opcao <= 7:
                print(
                    f"{VERMELHO}"
                    "Forma de pagamento inválida."
                    f"{RESET}"
                )
                continue

            parcelas = None

            if opcao == 5:
                while True:
                    parcelas = leia_int(
                        f"{BRANCO}"
                        "Parcelas [2 até 12]: "
                        f"{RESET}"
                    )

                    if 2 <= parcelas <= 12:
                        break

                    print(
                        f"{VERMELHO}"
                        "Quantidade de parcelas "
                        "inválida."
                        f"{RESET}"
                    )

            return opcao, parcelas

    # ================================================================
    # ALUGUÉIS DO CLIENTE
    # ================================================================

    def mostrar_do_cliente(
        self,
        cliente,
    ):
        alugueis = (
            self.service.listar_do_cliente(
                cliente
            )
        )

        print(
            f"\n{AZUL}"
            "--- MEUS ALUGUÉIS ---"
            f"{RESET}"
        )

        if not alugueis:
            print(
                f"{AMARELO}"
                "Nenhum aluguel encontrado."
                f"{RESET}"
            )
            return

        for aluguel in alugueis:
            print(
                f"\n{CIANO}"
                f"Aluguel #{aluguel.id}"
                f"{RESET}"
            )

            print(
                f"Veículo: "
                f"{aluguel.veiculo_tipo} - "
                f"{aluguel.veiculo_modelo}"
            )

            print(
                f"Dias: {aluguel.dias}"
            )

            print(
                f"Status: "
                f"{aluguel.status.upper()}"
            )

            print(
                f"Data de início: "
                f"{aluguel.data_inicio}"
            )

            print(
                f"Data prevista: "
                f"{aluguel.data_prevista}"
            )

            if aluguel.dias_atraso > 0:
                print(
                    f"Dias de atraso: "
                    f"{aluguel.dias_atraso}"
                )

                print(
                    f"Multa: "
                    f"R$ {aluguel.multa:.2f}"
                )

            if aluguel.ativo:
                print(
                    "Pagamento: "
                    "aguardando devolução"
                )

                print(
                    "Valor: "
                    "aguardando devolução"
                )

            else:
                print(
                    f"Km: "
                    f"{aluguel.km:.1f}"
                )

                print(
                    f"Pagamento: "
                    f"{aluguel.pagamento}"
                )

                print(
                    f"Valor: "
                    f"R$ {aluguel.valor:.2f}"
                )

                if aluguel.data_fim:
                    print(
                        f"Data de devolução: "
                        f"{aluguel.data_fim}"
                    )