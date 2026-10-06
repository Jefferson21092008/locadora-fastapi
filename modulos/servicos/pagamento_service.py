from modulos.consultas import ResultadoPaginado
from modulos.eventos import publicar_evento
from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)
from modulos.pagamentos import PagamentoFinanceiro


class PagamentoService:
    """
    Consolida a liquidação financeira do aluguel.

    O valor já registrado no aluguel durante a devolução continua
    representando a liquidação legada do contrato. Esta etapa passa a
    controlar separadamente cobranças adicionais de danos e multas de
    trânsito, sem duplicar as regras operacionais da vistoria.
    """

    def __init__(
        self,
        aluguel_repository,
        pagamento_repository,
        vistoria_service,
        evento_barramento=None,
    ):
        self.aluguel_repository = aluguel_repository
        self.pagamento_repository = pagamento_repository
        self.vistoria_service = vistoria_service
        self.evento_barramento = evento_barramento

    def _obter_aluguel(self, id_aluguel):
        aluguel = (
            self.aluguel_repository
            .buscar_por_id(id_aluguel)
        )

        if aluguel is None:
            raise RecursoNaoEncontrado(
                "Aluguel não encontrado."
            )

        return aluguel

    def _obter_aluguel_finalizado(self, id_aluguel):
        aluguel = self._obter_aluguel(
            id_aluguel
        )

        if aluguel.status != "finalizado":
            raise RegraDeNegocio(
                "O financeiro só pode receber pagamentos "
                "de um aluguel finalizado."
            )

        return aluguel

    @staticmethod
    def _arredondar(valor):
        return round(float(valor or 0), 2)

    def obter_resumo(self, id_aluguel):
        aluguel = self._obter_aluguel(
            id_aluguel
        )
        vistoria = (
            self.vistoria_service
            .obter_resumo(id_aluguel)
        )
        pagamentos = (
            self.pagamento_repository
            .listar_por_aluguel(id_aluguel)
        )

        indicadores = vistoria["indicadores"]
        valor_devolucao = self._arredondar(
            aluguel.valor
        )
        danos_total = self._arredondar(
            indicadores["danos_ativos_total"]
        )
        multas_total = self._arredondar(
            indicadores["multas_ativas_total"]
        )

        total_devido = self._arredondar(
            valor_devolucao
            + danos_total
            + multas_total
        )

        # O fluxo anterior à Etapa 17 já registrava o pagamento do
        # contrato na própria devolução. Ele entra como valor liquidado
        # legado para que a nova camada não cobre o mesmo valor de novo.
        valor_legado_pago = (
            valor_devolucao
            if (
                aluguel.status == "finalizado"
                and aluguel.pagamento
            )
            else 0.0
        )

        pagamentos_confirmados = [
            pagamento
            for pagamento in pagamentos
            if pagamento.confirmado
        ]
        pagamentos_adicionais = self._arredondar(
            sum(
                pagamento.valor
                for pagamento
                in pagamentos_confirmados
            )
        )
        total_pago = self._arredondar(
            valor_legado_pago
            + pagamentos_adicionais
        )

        diferenca = self._arredondar(
            total_devido - total_pago
        )
        saldo_pendente = max(
            diferenca,
            0.0,
        )
        credito_cliente = max(
            -diferenca,
            0.0,
        )

        if credito_cliente > 0:
            status = "credito"
        elif saldo_pendente == 0:
            status = "liquidado"
        elif pagamentos_adicionais > 0:
            status = "parcial"
        else:
            status = "pendente"

        return {
            "aluguel": aluguel,
            "pagamentos": pagamentos,
            "valor_devolucao": valor_devolucao,
            "multa_atraso": self._arredondar(
                aluguel.multa
            ),
            "danos_total": danos_total,
            "multas_transito_total": multas_total,
            "total_devido": total_devido,
            "valor_legado_pago": valor_legado_pago,
            "pagamentos_adicionais": pagamentos_adicionais,
            "total_pago": total_pago,
            "saldo_pendente": saldo_pendente,
            "credito_cliente": credito_cliente,
            "caucao_retida_disponivel": self._arredondar(
                indicadores["caucao_retida"]
            ),
            "status_financeiro": status,
        }

    def registrar_pagamento(
        self,
        id_aluguel,
        valor,
        forma,
        parcelas=1,
        observacoes=None,
    ):
        self._obter_aluguel_finalizado(
            id_aluguel
        )
        resumo = self.obter_resumo(
            id_aluguel
        )

        if resumo["saldo_pendente"] <= 0:
            raise RegraDeNegocio(
                "Esse aluguel não possui saldo pendente."
            )

        pagamento = PagamentoFinanceiro(
            id_pagamento=0,
            aluguel_id=id_aluguel,
            valor=valor,
            forma=forma,
            parcelas=parcelas,
            observacoes=observacoes,
        )

        valido, mensagem = (
            pagamento.validar_dados()
        )
        if not valido:
            raise RegraDeNegocio(
                mensagem
            )

        if (
            pagamento.valor
            - resumo["saldo_pendente"]
            > 0.009
        ):
            raise RegraDeNegocio(
                "O pagamento não pode superar "
                "o saldo pendente."
            )

        limite_adicional = self._arredondar(
            resumo["pagamentos_adicionais"]
            + resumo["saldo_pendente"]
        )

        pagamento_registrado = (
            self.pagamento_repository
            .registrar(
                pagamento,
                limite_adicional=limite_adicional,
            )
        )

        publicar_evento(
            self.evento_barramento,
            "pagamento.registrado",
            agregado_tipo="pagamento",
            agregado_id=pagamento_registrado.id,
            dados={
                "aluguel_id": id_aluguel,
                "valor": pagamento_registrado.valor,
                "forma": pagamento_registrado.forma,
            },
        )
        return pagamento_registrado

    def estornar_pagamento(
        self,
        id_pagamento,
    ):
        pagamento = (
            self.pagamento_repository
            .buscar_por_id(id_pagamento)
        )

        if pagamento is None:
            raise RecursoNaoEncontrado(
                "Pagamento não encontrado."
            )

        sucesso, mensagem = (
            pagamento.estornar()
        )

        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        atualizado = (
            self.pagamento_repository
            .atualizar(pagamento)
        )

        if atualizado is None:
            raise RecursoNaoEncontrado(
                "Pagamento não encontrado."
            )

        publicar_evento(
            self.evento_barramento,
            "pagamento.estornado",
            agregado_tipo="pagamento",
            agregado_id=atualizado.id,
            dados={
                "aluguel_id": atualizado.aluguel_id,
                "valor": atualizado.valor,
            },
        )
        return atualizado

    def consultar_contas(
        self,
        pagina=1,
        por_pagina=12,
        busca="",
        ordenar="id",
        direcao="desc",
    ):
        resultado = (
            self.aluguel_repository
            .consultar(
                pagina=pagina,
                por_pagina=por_pagina,
                busca=busca,
                status="finalizado",
                ordenar=ordenar,
                direcao=direcao,
            )
        )

        return ResultadoPaginado(
            items=[
                self.obter_resumo(
                    aluguel.id
                )
                for aluguel
                in resultado.items
            ],
            total=resultado.total,
            resumo=resultado.resumo,
        )
