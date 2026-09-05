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


class RelatorioCLI:
    """Interface de terminal dos relatórios."""

    def __init__(
        self,
        relatorio_service,
    ):
        self.service = relatorio_service

    # ================================================================
    # HISTÓRICO DE ALUGUÉIS
    # ================================================================

    def mostrar_historico(self):
        alugueis = (
            self.service.listar_historico()
        )

        print(
            f"\n{AZUL}"
            "--- HISTÓRICO DE ALUGUÉIS ---"
            f"{RESET}"
        )

        if not alugueis:
            print(
                f"{AMARELO}"
                "Nenhum aluguel registrado."
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
                f"Cliente: "
                f"{aluguel.cliente_nome} "
                f"(@{aluguel.cliente_usuario})"
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

    # ================================================================
    # TOTAL ARRECADADO
    # ================================================================

    def mostrar_total_arrecadado(self):
        total = (
            self.service
            .calcular_total_arrecadado()
        )

        print(
            f"\n{VERDE}"
            f"Total arrecadado: "
            f"R$ {total:.2f}"
            f"{RESET}"
        )

    # ================================================================
    # RESUMO
    # ================================================================

    def mostrar_resumo(self):
        resumo = (
            self.service.gerar_resumo()
        )

        print(
            f"\n{AZUL}"
            "--- RESUMO DA LOCADORA ---"
            f"{RESET}"
        )

        print(
            "Clientes ativos: "
            f"{resumo['clientes_ativos']}"
        )

        print(
            "Veículos ativos: "
            f"{resumo['veiculos_ativos']}"
        )

        print(
            "Aluguéis ativos: "
            f"{resumo['alugueis_ativos']}"
        )

        print(
            "Aluguéis finalizados: "
            f"{resumo['alugueis_finalizados']}"
        )

        print(
            "Total arrecadado: "
            f"R$ "
            f"{resumo['total_arrecadado']:.2f}"
        )

    # ================================================================
    # VEÍCULOS MAIS ALUGADOS
    # ================================================================

    def mostrar_veiculos_mais_alugados(
        self,
    ):
        resultado = (
            self.service
            .veiculos_mais_alugados()
        )

        if not resultado:
            print(
                f"\n{AMARELO}"
                "Nenhum aluguel registrado."
                f"{RESET}"
            )
            return

        print(
            f"\n{AZUL}"
            "=== VEÍCULOS MAIS ALUGADOS ==="
            f"{RESET}"
        )

        for posicao, item in enumerate(
            resultado,
            start=1,
        ):
            print(
                f"\n{CIANO}"
                f"{posicao}º lugar"
                f"{RESET}"
            )

            print(
                f"ID: {item['id']}"
            )

            print(
                f"Tipo: {item['tipo']}"
            )

            print(
                f"Modelo: {item['modelo']}"
            )

            print(
                "Total de aluguéis: "
                f"{item['total_alugueis']}"
            )

    # ================================================================
    # FATURAMENTO POR TIPO
    # ================================================================

    def mostrar_faturamento_por_tipo(
        self,
    ):
        resultado = (
            self.service
            .faturamento_por_tipo()
        )

        if not resultado:
            print(
                f"\n{AMARELO}"
                "Nenhum faturamento registrado."
                f"{RESET}"
            )
            return

        print(
            f"\n{AZUL}"
            "=== FATURAMENTO POR TIPO ==="
            f"{RESET}"
        )

        total_geral = 0

        for item in resultado:
            faturamento = float(
                item["faturamento"]
            )

            total_geral += faturamento

            print(
                f"\n{CIANO}"
                f"{item['tipo']}"
                f"{RESET}"
            )

            print(
                "Aluguéis finalizados: "
                f"{item['total_alugueis']}"
            )

            print(
                "Faturamento: "
                f"R$ {faturamento:.2f}"
            )

        print(
            f"\n{VERDE}"
            "Total geral: "
            f"R$ {total_geral:.2f}"
            f"{RESET}"
        )

    # ================================================================
    # CUSTOS DE MANUTENÇÃO
    # ================================================================

    def mostrar_custos_manutencao(
        self,
    ):
        resultado = (
            self.service
            .custos_manutencao()
        )

        if not resultado:
            print(
                f"\n{AMARELO}"
                "Nenhuma manutenção registrada."
                f"{RESET}"
            )
            return

        print(
            f"\n{AZUL}"
            "=== CUSTOS DE MANUTENÇÃO ==="
            f"{RESET}"
        )

        total_geral = 0

        for item in resultado:
            custo = float(
                item["custo_total"]
            )

            total_geral += custo

            print(
                f"\n{CIANO}"
                f"Veículo #{item['id']}"
                f"{RESET}"
            )

            print(
                f"Veículo: "
                f"{item['tipo']} - "
                f"{item['modelo']}"
            )

            print(
                "Manutenções: "
                f"{item['total_manutencoes']}"
            )

            print(
                "Custo total: "
                f"R$ {custo:.2f}"
            )

        print(
            f"\n{VERDE}"
            "Total gasto em manutenção: "
            f"R$ {total_geral:.2f}"
            f"{RESET}"
        )

    def mostrar_clientes_mais_alugam(
        self,
    ):
        resultado = (
            self.service
            .clientes_mais_alugam()
        )

        if not resultado:
            print(
                "\nNenhum aluguel registrado."
            )
            return

        print(
            "\n=== CLIENTES QUE MAIS ALUGAM ==="
        )

        for posicao, item in enumerate(
            resultado,
            start=1,
        ):
            print(
                f"\n{posicao}º lugar"
                f"\nCliente: "
                f"{item['cliente_nome']}"
                f"\nUsuário: "
                f"@{item['cliente_usuario']}"
                f"\nAluguéis: "
                f"{item['total_alugueis']}"
                f"\nTotal gasto: "
                f"R$ {item['total_gasto']:.2f}"
            )

    def mostrar_resumo_financeiro(
        self,
    ):
        resultado = (
            self.service
            .resumo_financeiro()
        )

        receita = float(
            resultado[
                "receita_alugueis"
            ]
        )

        custos = float(
            resultado[
                "custos_manutencao"
            ]
        )

        bruto = float(
            resultado[
                "resultado_bruto"
            ]
        )

        print(
            "\n=== RESUMO FINANCEIRO ==="
        )

        print(
            f"\nReceita com aluguéis: "
            f"R$ {receita:.2f}"

            f"\nCustos de manutenção: "
            f"R$ {custos:.2f}"

            f"\nResultado bruto: "
            f"R$ {bruto:.2f}"
        )

    def mostrar_resultado_por_veiculo(
        self,
    ):
        resultado = (
            self.service
            .resultado_por_veiculo()
        )

        if not resultado:
            print(
                "\nNenhum dado financeiro "
                "de veículo registrado."
            )
            return

        print(
            "\n=== RESULTADO POR VEÍCULO ==="
        )

        for item in resultado:
            print(
                "\n----------------------------"

                f"\nVeículo #{item['id']}"

                f"\n{item['tipo']} - "
                f"{item['modelo']}"

                f"\nAluguéis finalizados: "
                f"{item['total_alugueis']}"

                f"\nReceita: "
                f"R$ {item['receita']:.2f}"

                f"\nManutenções: "
                f"{item['total_manutencoes']}"

                f"\nCusto de manutenção: "
                f"R$ "
                f"{item['custo_manutencao']:.2f}"

                f"\nResultado bruto: "
                f"R$ "
                f"{item['resultado_bruto']:.2f}"
            )

    # ================================================================
    # MENU
    # ================================================================

    def menu_relatorios(self):
        while True:
            print(
                f"""
{AZUL}=========== RELATÓRIOS ==========={RESET}

{BRANCO}[ 1 ] Histórico de aluguéis
[ 2 ] Total arrecadado
[ 3 ] Resumo da locadora
[ 4 ] Veículos mais alugados
[ 5 ] Faturamento por tipo
[ 6 ] Custos de manutenção
[ 7 ] Clientes que mais alugam
[ 8 ] Resumo financeiro
[ 9 ] Resultado por veículo
[ 10 ] Voltar{RESET}
"""
            )

            opcao = leia_int(
                f"{BRANCO}"
                "Escolha uma opção: "
                f"{RESET}"
            )

            if opcao == 1:
                self.mostrar_historico()

            elif opcao == 2:
                self.mostrar_total_arrecadado()

            elif opcao == 3:
                self.mostrar_resumo()

            elif opcao == 4:
                self.mostrar_veiculos_mais_alugados()

            elif opcao == 5:
                self.mostrar_faturamento_por_tipo()

            elif opcao == 6:
                self.mostrar_custos_manutencao()

            elif opcao == 7:
                self.mostrar_clientes_mais_alugam()

            elif opcao == 8:
                self.mostrar_resumo_financeiro()

            elif opcao == 9:
                self.mostrar_resultado_por_veiculo()

            elif opcao == 10:
                break
            else:
                print(
                    f"\n{VERMELHO}"
                    "Opção inválida."
                    f"{RESET}"
                )