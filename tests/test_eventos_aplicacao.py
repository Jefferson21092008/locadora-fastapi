from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from modulos.eventos import BarramentoEventos
from modulos.servicos.pagamento_service import PagamentoService
from modulos.servicos.reserva_service import ReservaService


class ColetorEventos:
    def __init__(self, barramento):
        self.eventos = []
        barramento.assinar("*", self.eventos.append)


class VeiculoServiceFake:
    def buscar_por_id(self, id_veiculo):
        return SimpleNamespace(
            id=id_veiculo,
            ativo=True,
            tipo="carro",
            modelo="Teste",
        )


class ReservaRepositoryFake:
    def __init__(self, falhar=False):
        self.falhar = falhar

    def buscar_conflitante(self, **_kwargs):
        return None

    def registrar(self, _reserva):
        if self.falhar:
            raise RuntimeError("falha controlada")
        return 17


class AluguelRepositorySemConflito:
    def listar_ativos(self):
        return []


class ManutencaoRepositorySemConflito:
    def buscar_ativa_por_veiculo(self, _id_veiculo):
        return None


def criar_reserva_service(barramento, falhar=False):
    return ReservaService(
        veiculo_service=VeiculoServiceFake(),
        reserva_repository=ReservaRepositoryFake(falhar=falhar),
        aluguel_repository=AluguelRepositorySemConflito(),
        manutencao_repository=ManutencaoRepositorySemConflito(),
        evento_barramento=barramento,
    )


def test_reserva_publica_evento_depois_de_persistir():
    barramento = BarramentoEventos()
    coletor = ColetorEventos(barramento)
    service = criar_reserva_service(barramento)
    inicio = date.today() + timedelta(days=2)
    fim = inicio + timedelta(days=3)
    cliente = SimpleNamespace(
        id=5,
        usuario="cliente",
        nome="Cliente Teste",
    )

    reserva = service.criar(
        cliente=cliente,
        id_veiculo=9,
        data_inicio=inicio.isoformat(),
        data_fim=fim.isoformat(),
    )

    assert reserva.id == 17
    assert len(coletor.eventos) == 1
    evento = coletor.eventos[0]
    assert evento.nome == "reserva.criada"
    assert evento.agregado_id == 17
    assert evento.dados == {
        "cliente_id": 5,
        "veiculo_id": 9,
        "data_inicio": inicio.isoformat(),
        "data_fim": fim.isoformat(),
    }


def test_reserva_nao_publica_evento_quando_persistencia_falha():
    barramento = BarramentoEventos()
    coletor = ColetorEventos(barramento)
    service = criar_reserva_service(
        barramento,
        falhar=True,
    )
    inicio = date.today() + timedelta(days=2)
    fim = inicio + timedelta(days=3)
    cliente = SimpleNamespace(
        id=5,
        usuario="cliente",
        nome="Cliente Teste",
    )

    with pytest.raises(RuntimeError):
        service.criar(
            cliente=cliente,
            id_veiculo=9,
            data_inicio=inicio.isoformat(),
            data_fim=fim.isoformat(),
        )

    assert coletor.eventos == []


class AluguelRepositoryFake:
    def __init__(self):
        self.aluguel = SimpleNamespace(
            id=3,
            status="finalizado",
            valor=0,
            pagamento=None,
            multa=0,
        )

    def buscar_por_id(self, _id_aluguel):
        return self.aluguel


class PagamentoRepositoryFake:
    def __init__(self):
        self.itens = []

    def listar_por_aluguel(self, _id_aluguel):
        return list(self.itens)

    def registrar(self, pagamento, limite_adicional=None):
        assert limite_adicional == 100.0
        pagamento.id = 21
        self.itens.append(pagamento)
        return pagamento

    def buscar_por_id(self, id_pagamento):
        return next(
            (
                item
                for item in self.itens
                if item.id == id_pagamento
            ),
            None,
        )

    def atualizar(self, pagamento):
        return pagamento


class VistoriaServiceFake:
    def obter_resumo(self, _id_aluguel):
        return {
            "indicadores": {
                "danos_ativos_total": 100,
                "multas_ativas_total": 0,
                "caucao_retida": 0,
            }
        }


def test_pagamento_publica_registro_e_estorno():
    barramento = BarramentoEventos()
    coletor = ColetorEventos(barramento)
    service = PagamentoService(
        aluguel_repository=AluguelRepositoryFake(),
        pagamento_repository=PagamentoRepositoryFake(),
        vistoria_service=VistoriaServiceFake(),
        evento_barramento=barramento,
    )

    pagamento = service.registrar_pagamento(
        id_aluguel=3,
        valor=40,
        forma="pix",
    )
    service.estornar_pagamento(pagamento.id)

    assert [evento.nome for evento in coletor.eventos] == [
        "pagamento.registrado",
        "pagamento.estornado",
    ]
    assert coletor.eventos[0].dados == {
        "aluguel_id": 3,
        "valor": 40.0,
        "forma": "pix",
    }
    assert coletor.eventos[1].dados == {
        "aluguel_id": 3,
        "valor": 40.0,
    }
