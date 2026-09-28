from sqlalchemy import select

from modulos.models.pagamento_model import (
    PagamentoFinanceiroModel,
)
from modulos.pagamentos import PagamentoFinanceiro


class PagamentoRepository:
    def __init__(self, banco_sqlalchemy):
        self.banco_sqlalchemy = banco_sqlalchemy

    @staticmethod
    def _para_entidade(model):
        if model is None:
            return None

        return PagamentoFinanceiro(
            id_pagamento=model.id,
            aluguel_id=model.aluguel_id,
            valor=model.valor,
            forma=model.forma,
            parcelas=model.parcelas,
            observacoes=model.observacoes,
            status=model.status,
            criado_em=model.criado_em,
            estornado_em=model.estornado_em,
        )

    def listar_por_aluguel(self, aluguel_id):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            models = sessao.scalars(
                select(PagamentoFinanceiroModel)
                .where(
                    PagamentoFinanceiroModel.aluguel_id
                    == aluguel_id
                )
                .order_by(
                    PagamentoFinanceiroModel.id.desc()
                )
            ).all()

        return [
            self._para_entidade(model)
            for model in models
        ]

    def buscar_por_id(self, id_pagamento):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.get(
                PagamentoFinanceiroModel,
                id_pagamento,
            )

        return self._para_entidade(model)

    def registrar(self, pagamento):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = PagamentoFinanceiroModel(
                aluguel_id=pagamento.aluguel_id,
                valor=pagamento.valor,
                forma=pagamento.forma,
                parcelas=pagamento.parcelas,
                observacoes=pagamento.observacoes,
                status=pagamento.status,
                criado_em=pagamento.criado_em,
                estornado_em=pagamento.estornado_em,
            )
            sessao.add(model)
            sessao.commit()
            sessao.refresh(model)

        return self._para_entidade(model)

    def atualizar(self, pagamento):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.get(
                PagamentoFinanceiroModel,
                pagamento.id,
            )

            if model is None:
                return None

            model.valor = pagamento.valor
            model.forma = pagamento.forma
            model.parcelas = pagamento.parcelas
            model.observacoes = pagamento.observacoes
            model.status = pagamento.status
            model.estornado_em = pagamento.estornado_em

            sessao.commit()
            sessao.refresh(model)

        return self._para_entidade(model)
