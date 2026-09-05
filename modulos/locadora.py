from modulos.container import Container
from modulos.interface import (
    AMARELO,
    AZUL,
    RESET,
    VERMELHO,
    menu_admin,
    menu_cliente,
    menu_principal,
    titulo,
)

from modulos.cli.veiculos_cli import VeiculoCLI
from modulos.cli.clientes_cli import ClienteCLI
from modulos.cli.alugueis_cli import AluguelCLI
from modulos.cli.relatorios_cli import RelatorioCLI
from modulos.cli.admin_cli import AdminCLI

class Locadora:
    """Coordena os serviços e menus do sistema."""

    def __init__(
        self,
        container=None,
    ):
        self.container = (
            container
            or Container()
        )

        self.veiculo_cli = (
            VeiculoCLI(
                self.container
                .veiculo_service
            )
        )

        self.cliente_cli = (
            ClienteCLI(
                self.container
                .cliente_service
            )
        )

        self.aluguel_cli = (
            AluguelCLI(
                self.container
                .aluguel_service,
                self.veiculo_cli,
            )
        )

        self.relatorio_cli = (
            RelatorioCLI(
                self.container
                .relatorio_service
            )
        )

        self.admin_cli = (
            AdminCLI(
                self.container
                .admin_service,
                self.container
                .veiculo_service,
                self.container
                .manutencao_service,
            )
        )

    # ================================================================
    # PROGRAMA PRINCIPAL
    # ================================================================

    def executar(self):
        titulo(
            "SISTEMA DE ALUGUEL DE VEÍCULOS"
        )

        while True:
            opcao = menu_principal()

            if opcao == 1:
                cliente = (
                    self.cliente_cli.login()
                )

                if cliente is not None:
                    self.area_cliente(
                        cliente
                    )

            elif opcao == 2:
                self.cliente_cli.criar_conta()

            elif opcao == 3:
                if self.admin_cli.login():
                    self.area_admin()

            elif opcao == 4:
                print(
                    f"\n{AZUL}"
                    "Encerrando sistema..."
                    f"{RESET}"
                )
                break

            else:
                print(
                    f"{VERMELHO}"
                    "Opção inválida."
                    f"{RESET}"
                )

        titulo(
            "SISTEMA ENCERRADO"
        )

    # ================================================================
    # ÁREA DO CLIENTE
    # ================================================================

    def area_cliente(
        self,
        cliente,
    ):
        while True:
            opcao = menu_cliente()

            if opcao == 1:
                self.veiculo_cli.mostrar_disponiveis()

            elif opcao == 2:
                self.veiculo_cli.buscar()

            elif opcao == 3:
                self.aluguel_cli.alugar(
                    cliente
                )

            elif opcao == 4:
                self.aluguel_cli.devolver(
                    cliente
                )

            elif opcao == 5:
                self.aluguel_cli.mostrar_do_cliente(
                    cliente
                )

            elif opcao == 6:
                self.cliente_cli.mostrar_dados(
                    cliente
                )

            elif opcao == 7:
                self.cliente_cli.alterar_senha(
                    cliente
                )

            elif opcao == 8:
                print(
                    f"{AMARELO}"
                    "Saída realizada."
                    f"{RESET}"
                )
                break

            else:
                print(
                    f"{VERMELHO}"
                    "Opção inválida."
                    f"{RESET}"
                )

    # ================================================================
    # ÁREA DO ADMINISTRADOR
    # ================================================================

    def area_admin(self):
        while True:
            opcao = menu_admin()

            if opcao == 1:
                self.veiculo_cli.cadastrar()

            elif opcao == 2:
                self.veiculo_cli.editar()

            elif opcao == 3:
                self.veiculo_cli.desativar()

            elif opcao == 4:
                self.veiculo_cli.reativar()

            elif opcao == 5:
                self.veiculo_cli.mostrar_frota()

            elif opcao == 6:
                self.veiculo_cli.mostrar_alugados()

            elif opcao == 7:
                self.relatorio_cli.menu_relatorios()

            elif opcao == 8:
                self.cliente_cli.listar_clientes()

            elif opcao == 9:
                self.cliente_cli.desativar()

            elif opcao == 10:
                self.cliente_cli.reativar()

            elif opcao == 11:
                (
                    self.admin_cli
                    .enviar_veiculo_para_manutencao()
                )

            elif opcao == 12:
                (
                    self.admin_cli
                    .finalizar_manutencao_veiculo()
                )

            elif opcao == 13:
                (
                    self.admin_cli
                    .mostrar_veiculos_em_manutencao()
                )

            elif opcao == 14:
                (
                    self.admin_cli
                    .mostrar_historico_manutencao()
                )

            elif opcao == 15:
                self.admin_cli.alterar_senha()

            elif opcao == 16:
                print(
                    f"{AMARELO}"
                    "Saída do administrador realizada."
                    f"{RESET}"
                )
                break

            else:
                print(
                    f"{VERMELHO}"
                    "Opção inválida."
                    f"{RESET}"
                )
