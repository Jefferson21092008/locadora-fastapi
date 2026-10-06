from types import SimpleNamespace

import pytest

from modulos.consultas import ResultadoPaginado
from modulos.excecoes import RegraDeNegocio
from modulos.servicos.pagamento_service import (
    PagamentoService,
)


class AluguelRepositoryFake:
    def __init__(self):
        self.aluguel = SimpleNamespace(
            id=1,
            cliente_id=2,
            cliente_nome="Lucas",
            cliente_usuario="lucas",
            veiculo_id=3,
            veiculo_tipo="carro",
            veiculo_modelo="Civic",
            status="finalizado",
            data_inicio="2026-09-20",
            data_prevista="2026-09-23",
            data_fim="2026-09-23",
            pagamento="Pix",
            valor=450.0,
            multa=0.0,
        )

    def buscar_por_id(self, id_aluguel):
        if id_aluguel == 1:
            return self.aluguel
        return None

    def consultar(self, **kwargs):
        return ResultadoPaginado(
            items=[self.aluguel],
            total=1,
            resumo={
                "total": 1,
                "ativos": 0,
                "finalizados": 1,
                "atrasados": 0,
            },
        )


class PagamentoRepositoryFake:
    def __init__(self):
        self.items = []
        self.next_id = 1

    def listar_por_aluguel(self, aluguel_id):
        return [
            item
            for item in self.items
            if item.aluguel_id == aluguel_id
        ]

    def buscar_por_id(self, id_pagamento):
        return next(
            (
                item
                for item in self.items
                if item.id == id_pagamento
            ),
            None,
        )

    def registrar(
        self,
        pagamento,
        limite_adicional=None,
    ):
        pagamento.id = self.next_id
        self.next_id += 1
        self.items.append(pagamento)
        return pagamento

    def atualizar(self, pagamento):
        return pagamento


class VistoriaServiceFake:
    def obter_resumo(self, id_aluguel):
        return {
            "indicadores": {
                "danos_ativos_total": 300,
                "multas_ativas_total": 100,
                "caucao_retida": 500,
            }
        }


@pytest.fixture
def ambiente():
    repository = PagamentoRepositoryFake()
    service = PagamentoService(
        aluguel_repository=(
            AluguelRepositoryFake()
        ),
        pagamento_repository=(
            repository
        ),
        vistoria_service=(
            VistoriaServiceFake()
        ),
    )
    return service, repository


def test_resumo_nao_cobra_de_novo_pagamento_legado(
    ambiente,
):
    service, _ = ambiente

    resumo = service.obter_resumo(1)

    assert resumo["total_devido"] == 850
    assert resumo["valor_legado_pago"] == 450
    assert resumo["saldo_pendente"] == 400
    assert resumo[
        "caucao_retida_disponivel"
    ] == 500
    assert resumo["status_financeiro"] == "pendente"


def test_pagamento_parcial_e_liquidacao(
    ambiente,
):
    service, _ = ambiente

    primeiro = service.registrar_pagamento(
        id_aluguel=1,
        valor=150,
        forma="pix",
    )

    resumo = service.obter_resumo(1)
    assert primeiro.id == 1
    assert resumo["saldo_pendente"] == 250
    assert resumo["status_financeiro"] == "parcial"

    service.registrar_pagamento(
        id_aluguel=1,
        valor=250,
        forma="credito",
        parcelas=2,
    )

    resumo = service.obter_resumo(1)
    assert resumo["saldo_pendente"] == 0
    assert resumo["status_financeiro"] == "liquidado"


def test_rejeita_pagamento_acima_do_saldo(
    ambiente,
):
    service, _ = ambiente

    with pytest.raises(
        RegraDeNegocio,
        match="superar",
    ):
        service.registrar_pagamento(
            id_aluguel=1,
            valor=401,
            forma="pix",
        )


def test_estorno_reabre_saldo(
    ambiente,
):
    service, _ = ambiente
    pagamento = service.registrar_pagamento(
        id_aluguel=1,
        valor=400,
        forma="pix",
    )

    service.estornar_pagamento(
        pagamento.id
    )

    resumo = service.obter_resumo(1)
    assert resumo["saldo_pendente"] == 400
    assert resumo["status_financeiro"] == "pendente"
