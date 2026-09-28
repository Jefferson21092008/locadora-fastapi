from datetime import date

import pytest

from modulos.clientes import Cliente
from modulos.excecoes import (
    RegraDeNegocio,
)
from modulos.servicos.alugueis_service import (
    AluguelService,
)
from modulos.veiculos import Carro


class VeiculoServiceFake:
    def __init__(self):
        self.veiculo = Carro(
            id_veiculo=10,
            modelo="Civic",
            ano=date.today().year,
            diaria=150,
            preco_km=1.5,
            status="disponivel",
        )

    def obter_disponivel(
        self,
        id_veiculo,
    ):
        if (
            id_veiculo
            != self.veiculo.id
        ):
            raise RegraDeNegocio(
                "Veículo indisponível."
            )

        return self.veiculo


class AluguelRepositoryFake:
    def __init__(self):
        self.registrados = []

    def registrar(
        self,
        aluguel,
        _veiculo,
    ):
        aluguel.id = 1
        self.registrados.append(
            aluguel
        )
        return aluguel.id


class ReservaServiceFake:
    def __init__(
        self,
        reserva=None,
        erro=None,
    ):
        self.reserva = reserva
        self.erro = erro
        self.convertida = None
        self.restaurada = None

    def validar_inicio_aluguel(
        self,
        **_kwargs,
    ):
        if self.erro is not None:
            raise self.erro

        return self.reserva

    def converter_para_aluguel(
        self,
        reserva,
    ):
        self.convertida = reserva

    def restaurar_apos_falha(
        self,
        reserva,
    ):
        self.restaurada = reserva


def cliente():
    return Cliente(
        id_cliente=1,
        nome="Ana Souza",
        usuario="ana123",
        email="ana@example.com",
    )


def test_aluguel_respeita_conflito_de_reserva():
    reserva_service = ReservaServiceFake(
        erro=RegraDeNegocio(
            "O veículo está reservado."
        )
    )
    service = AluguelService(
        veiculo_service=(
            VeiculoServiceFake()
        ),
        aluguel_repository=(
            AluguelRepositoryFake()
        ),
        reserva_service=(
            reserva_service
        ),
    )

    with pytest.raises(
        RegraDeNegocio,
        match="reservado",
    ):
        service.alugar(
            cliente=cliente(),
            id_veiculo=10,
            dias=2,
            anos_habilitacao=5,
        )


def test_aluguel_converte_reserva_do_proprio_cliente():
    reserva = object()
    reserva_service = (
        ReservaServiceFake(
            reserva=reserva
        )
    )
    repository = (
        AluguelRepositoryFake()
    )
    service = AluguelService(
        veiculo_service=(
            VeiculoServiceFake()
        ),
        aluguel_repository=(
            repository
        ),
        reserva_service=(
            reserva_service
        ),
    )

    aluguel = service.alugar(
        cliente=cliente(),
        id_veiculo=10,
        dias=2,
        anos_habilitacao=5,
    )

    assert aluguel.id == 1
    assert (
        reserva_service.convertida
        is reserva
    )
    assert len(
        repository.registrados
    ) == 1
