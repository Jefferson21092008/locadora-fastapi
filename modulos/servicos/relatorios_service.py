class RelatorioService:
    """Consultas e cálculos relacionados aos relatórios."""

    def __init__(
        self,
        aluguel_repository,
        veiculo_repository,
        cliente_repository,
        relatorio_repository,
    ):
        repositories = {
            "AluguelRepository": aluguel_repository,
            "VeiculoRepository": veiculo_repository,
            "ClienteRepository": cliente_repository,
            "RelatorioRepository": relatorio_repository,
        }

        for nome, repository in repositories.items():
            if repository is None:
                raise ValueError(
                    f"{nome} é obrigatório."
                )

        self.aluguel_repository = aluguel_repository
        self.veiculo_repository = veiculo_repository
        self.cliente_repository = cliente_repository
        self.relatorio_repository = relatorio_repository

    # ================================================================
    # HISTÓRICO
    # ================================================================

    def listar_historico(self):
        return (
            self.aluguel_repository
            .listar_colecao()
        )

    # ================================================================
    # FATURAMENTO
    # ================================================================

    def calcular_total_arrecadado(self):
        alugueis = (
            self.aluguel_repository
            .listar_colecao()
        )

        return sum(
            aluguel.valor
            for aluguel in alugueis
            if not aluguel.ativo
        )

    # ================================================================
    # RESUMO
    # ================================================================

    def gerar_resumo(self):
        clientes_ativos = (
            self.cliente_repository
            .listar_ativos()
        )

        veiculos_ativos = (
            self.veiculo_repository
            .listar_ativos()
        )

        alugueis = (
            self.aluguel_repository
            .listar_colecao()
        )

        alugueis_ativos = [
            aluguel
            for aluguel in alugueis
            if aluguel.ativo
        ]

        alugueis_finalizados = [
            aluguel
            for aluguel in alugueis
            if not aluguel.ativo
        ]

        return {
            "clientes_ativos": len(
                clientes_ativos
            ),
            "veiculos_ativos": len(
                veiculos_ativos
            ),
            "alugueis_ativos": len(
                alugueis_ativos
            ),
            "alugueis_finalizados": len(
                alugueis_finalizados
            ),
            "total_arrecadado": (
                self.calcular_total_arrecadado()
            ),
        }

    # ================================================================
    # RELATÓRIOS SQL
    # ================================================================

    def veiculos_mais_alugados(
        self,
        limite=10,
    ):
        return (
            self.relatorio_repository
            .veiculos_mais_alugados(
                limite
            )
        )

    def faturamento_por_tipo(self):
        return (
            self.relatorio_repository
            .faturamento_por_tipo()
        )

    def custos_manutencao(self):
        return (
            self.relatorio_repository
            .custos_manutencao()
        )

    def clientes_mais_alugam(
        self,
        limite=10,
    ):
        return (
            self.relatorio_repository
            .clientes_mais_alugam(
                limite
            )
        )

    def resumo_financeiro(self):
        return (
            self.relatorio_repository
            .resumo_financeiro()
        )

    def resultado_por_veiculo(self):
        return (
            self.relatorio_repository
            .resultado_por_veiculo()
        )
