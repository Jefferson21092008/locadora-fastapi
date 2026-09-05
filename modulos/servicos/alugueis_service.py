from modulos.alugueis import Aluguel
from modulos.pagamentos import Pagamento

from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)


class AluguelService:
    """Regras e operações relacionadas aos aluguéis."""

    def __init__(
        self,
        veiculo_service,
        aluguel_repository,
    ):
        """Recebe as dependências prontas por injeção."""
        if veiculo_service is None:
            raise ValueError(
                "VeiculoService é obrigatório."
            )

        if aluguel_repository is None:
            raise ValueError(
                "AluguelRepository é obrigatório."
            )

        self.veiculo_service = veiculo_service
        self.aluguel_repository = aluguel_repository

    # ================================================================
    # CONSULTAS
    # ================================================================

    def listar_veiculos_disponiveis(self):
        return (
            self.veiculo_service
            .listar_disponiveis()
        )

    def obter_veiculo_disponivel(
        self,
        id_veiculo,
    ):
        return (
            self.veiculo_service
            .obter_disponivel(
                id_veiculo
            )
        )

    def listar_ativos_cliente(
        self,
        cliente,
    ):
        return (
            self.aluguel_repository
            .listar_ativos_cliente(
                cliente
            )
        )

    def listar_do_cliente(
        self,
        cliente,
    ):
        return (
            self.aluguel_repository
            .listar_do_cliente(
                cliente
            )
        )

    def buscar_ativo(
        self,
        cliente,
        id_veiculo=None,
    ):
        return (
            self.aluguel_repository
            .buscar_ativo(
                cliente,
                id_veiculo,
            )
        )

    # ================================================================
    # NOVO ALUGUEL
    # ================================================================

    def alugar(
        self,
        cliente,
        id_veiculo,
        dias,
        anos_habilitacao=None,
    ):
        if dias <= 0:
            raise RegraDeNegocio(
                "A quantidade de dias "
                "deve ser maior que zero."
            )

        veiculo = (
            self.veiculo_service
            .obter_disponivel(
                id_veiculo
            )
        )

        # Veículos como bicicleta podem exigir 0 anos.
        if (
            veiculo.ANOS_MINIMOS_HABILITACAO
            > 0
        ):
            if anos_habilitacao is None:
                raise RegraDeNegocio(
                    "Informe os anos de habilitação."
                )

            if anos_habilitacao < 0:
                raise RegraDeNegocio(
                    "Anos de habilitação inválidos."
                )

            if not veiculo.pode_ser_alugado(
                anos_habilitacao
            ):
                raise RegraDeNegocio(
                    "Tempo de habilitação insuficiente. "
                    "São necessários pelo menos "
                    f"{veiculo.ANOS_MINIMOS_HABILITACAO} "
                    "anos."
                )

        if not veiculo.alugar(
            cliente.usuario
        ):
            raise RegraDeNegocio(
                "Não foi possível alugar "
                "esse veículo."
            )

        aluguel = Aluguel(
            id_aluguel=0,
            cliente_id=cliente.id,
            cliente_usuario=cliente.usuario,
            cliente_nome=cliente.nome,
            veiculo_id=veiculo.id,
            veiculo_tipo=veiculo.tipo,
            veiculo_modelo=veiculo.modelo,
            dias=dias,
        )

        try:
            novo_id = (
                self.aluguel_repository
                .registrar(
                    aluguel,
                    veiculo,
                )
            )

        except Exception:
            # O SQLite fez rollback.
            # Precisamos desfazer também a mudança
            # no objeto que está na memória.
            veiculo.devolver()

            raise

        aluguel.id = novo_id

        return aluguel

    # ================================================================
    # DEVOLUÇÃO
    # ================================================================

    def devolver(
        self,
        cliente,
        id_veiculo,
        km,
        forma_pagamento,
        parcelas=None,
        data_referencia=None,
    ):
        if km < 0:
            raise RegraDeNegocio(
                "A quilometragem não pode "
                "ser negativa."
            )

        aluguel = self.buscar_ativo(
            cliente,
            id_veiculo,
        )

        if aluguel is None:
            raise RegraDeNegocio(
                "Esse veículo não pertence "
                "aos seus aluguéis ativos."
            )

        veiculo = (
            self.veiculo_service
            .buscar_por_id(
                id_veiculo
            )
        )

        if veiculo is None:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        valor_aluguel = veiculo.calcular_valor(
            aluguel.dias,
            km,
        )

        dias_atraso = (
            aluguel.calcular_dias_atraso(
                data_referencia
            )
        )

        multa = aluguel.calcular_multa(
            veiculo.diaria,
            data_referencia,
        )

        total = valor_aluguel + multa

        if (
            forma_pagamento == 5
            and (
                parcelas is None
                or not 2 <= parcelas <= 12
            )
        ):
            raise RegraDeNegocio(
                "A quantidade de parcelas "
                "deve estar entre 2 e 12."
            )

        resultado_pagamento = (
            Pagamento.calcular(
                total,
                forma_pagamento,
                parcelas,
            )
        )

        if resultado_pagamento is None:
            raise RegraDeNegocio(
                "Forma de pagamento inválida."
            )

        estado_aluguel = vars(
            aluguel
        ).copy()

        estado_veiculo = vars(
            veiculo
        ).copy()

        aluguel.finalizar(
            km=km,
            valor=(
                resultado_pagamento[
                    "valor_final"
                ]
            ),
            forma_pagamento=(
                resultado_pagamento[
                    "forma"
                ]
            ),
            dias_atraso=dias_atraso,
            multa=multa,
        )

        veiculo.adicionar_quilometragem(
            km
        )

        # Libera o veículo também na memória.
        veiculo.devolver()

        try:
            (
                self.aluguel_repository
                .registrar_devolucao(
                    aluguel,
                    veiculo,
                )
            )

        except Exception:
            aluguel.__dict__.clear()
            aluguel.__dict__.update(
                estado_aluguel
            )

            veiculo.__dict__.clear()
            veiculo.__dict__.update(
                estado_veiculo
            )

            raise

        return {
            "aluguel": aluguel,
            "veiculo": veiculo,
            "valor_aluguel": valor_aluguel,
            "dias_atraso": dias_atraso,
            "multa": multa,
            "valor_inicial": total,
            "pagamento": resultado_pagamento,
        }

    # ================================================================
    # LISTAGENS
    # ================================================================

    def listar_alugueis(self):
        return (
            self.aluguel_repository
            .listar_colecao()
        )

    def listar_ativos(self):
        return (
            self.aluguel_repository
            .listar_ativos()
        )
