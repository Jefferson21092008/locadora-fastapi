from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from modulos.clientes import Cliente
from modulos.excecoes import (
    RegraDeNegocio,
)
from modulos.reservas import Reserva
from modulos.servicos.reserva_service import (
    ReservaService,
)
from modulos.veiculos import Carro


class ReservaRepositoryFake:
    def __init__(self):
        self.reservas = []
        self.proximo_id = 1

    def registrar(self, reserva):
        reserva.id = self.proximo_id
        self.proximo_id += 1
        self.reservas.append(reserva)
        return reserva.id

    def buscar_por_id(self, id_reserva):
        return next(
            (
                reserva
                for reserva
                in self.reservas
                if reserva.id
                == id_reserva
            ),
            None,
        )

    def listar_colecao(self):
        return list(self.reservas)

    def listar_do_cliente(
        self,
        cliente_id,
    ):
        return [
            reserva
            for reserva
            in self.reservas
            if reserva.cliente_id
            == cliente_id
        ]

    def buscar_conflitante(
        self,
        veiculo_id,
        data_inicio,
        data_fim,
        ignorar_id=None,
    ):
        for reserva in self.reservas:
            if (
                reserva.id
                == ignorar_id
            ):
                continue
            if not reserva.ativa:
                continue
            if (
                reserva.veiculo_id
                == veiculo_id
                and reserva.data_inicio
                < data_fim
                and reserva.data_fim
                > data_inicio
            ):
                return reserva

        return None

    def atualizar_status(
        self,
        reserva,
    ):
        return None

    def consultar(self, **_kwargs):
        return SimpleNamespace(
            items=list(
                self.reservas
            ),
            total=len(
                self.reservas
            ),
            resumo={
                "total": len(
                    self.reservas
                ),
                "ativas": sum(
                    1
                    for reserva
                    in self.reservas
                    if reserva.ativa
                ),
                "expiradas": 0,
                "canceladas": 0,
                "convertidas": 0,
            },
        )


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

    def buscar_por_id(
        self,
        id_veiculo,
    ):
        if (
            id_veiculo
            == self.veiculo.id
        ):
            return self.veiculo

        return None


class AluguelRepositoryFake:
    def __init__(self):
        self.alugueis = []

    def listar_ativos(self):
        return list(
            self.alugueis
        )


class ManutencaoRepositoryFake:
    def __init__(self):
        self.manutencao = None

    def buscar_ativa_por_veiculo(
        self,
        id_veiculo,
    ):
        if (
            self.manutencao is not None
            and self.manutencao.veiculo_id
            == id_veiculo
        ):
            return self.manutencao

        return None


@pytest.fixture
def contexto():
    reserva_repository = (
        ReservaRepositoryFake()
    )
    aluguel_repository = (
        AluguelRepositoryFake()
    )
    manutencao_repository = (
        ManutencaoRepositoryFake()
    )
    service = ReservaService(
        veiculo_service=(
            VeiculoServiceFake()
        ),
        reserva_repository=(
            reserva_repository
        ),
        aluguel_repository=(
            aluguel_repository
        ),
        manutencao_repository=(
            manutencao_repository
        ),
    )
    cliente = Cliente(
        id_cliente=1,
        nome="Ana Souza",
        usuario="ana123",
        email="ana@example.com",
    )

    return (
        service,
        cliente,
        reserva_repository,
        aluguel_repository,
        manutencao_repository,
    )


def periodo(
    inicio_em_dias=5,
    duracao=3,
):
    inicio = (
        date.today()
        + timedelta(
            days=inicio_em_dias
        )
    )
    fim = (
        inicio
        + timedelta(
            days=duracao
        )
    )
    return (
        inicio.isoformat(),
        fim.isoformat(),
    )


def test_criar_reserva_futura(
    contexto,
):
    service, cliente, repository, _, _ = contexto
    inicio, fim = periodo()

    reserva = service.criar(
        cliente=cliente,
        id_veiculo=10,
        data_inicio=inicio,
        data_fim=fim,
    )

    assert reserva.id == 1
    assert reserva.cliente_id == cliente.id
    assert reserva.veiculo_id == 10
    assert repository.reservas == [
        reserva
    ]


def test_nao_cria_reserva_para_hoje(
    contexto,
):
    service, cliente, _, _, _ = contexto

    with pytest.raises(
        RegraDeNegocio,
        match="data futura",
    ):
        service.criar(
            cliente=cliente,
            id_veiculo=10,
            data_inicio=(
                date.today()
                .isoformat()
            ),
            data_fim=(
                (
                    date.today()
                    + timedelta(days=2)
                )
                .isoformat()
            ),
        )


def test_nao_permite_reservas_sobrepostas(
    contexto,
):
    service, cliente, _, _, _ = contexto
    inicio, fim = periodo()

    service.criar(
        cliente,
        10,
        inicio,
        fim,
    )

    with pytest.raises(
        RegraDeNegocio,
        match="já possui uma reserva",
    ):
        service.criar(
            cliente,
            10,
            (
                date.fromisoformat(
                    inicio
                )
                + timedelta(days=1)
            ).isoformat(),
            (
                date.fromisoformat(
                    fim
                )
                + timedelta(days=1)
            ).isoformat(),
        )


def test_nao_permite_conflito_com_aluguel_ativo(
    contexto,
):
    (
        service,
        cliente,
        _,
        aluguel_repository,
        _,
    ) = contexto
    inicio, fim = periodo()

    aluguel_repository.alugueis.append(
        SimpleNamespace(
            veiculo_id=10,
            data_inicio=(
                date.today()
                .isoformat()
            ),
            data_prevista=(
                date.fromisoformat(
                    fim
                )
                .isoformat()
            ),
        )
    )

    with pytest.raises(
        RegraDeNegocio,
        match="aluguel",
    ):
        service.criar(
            cliente,
            10,
            inicio,
            fim,
        )


def test_manutencao_sem_previsao_bloqueia_reserva(
    contexto,
):
    (
        service,
        cliente,
        _,
        _,
        manutencao_repository,
    ) = contexto
    inicio, fim = periodo()

    manutencao_repository.manutencao = (
        SimpleNamespace(
            veiculo_id=10,
            data_inicio=(
                date.today()
                .isoformat()
            ),
            data_prevista=None,
        )
    )

    with pytest.raises(
        RegraDeNegocio,
        match="manutenção",
    ):
        service.criar(
            cliente,
            10,
            inicio,
            fim,
        )


def test_cliente_so_cancela_reserva_propria(
    contexto,
):
    (
        service,
        cliente,
        repository,
        _,
        _,
    ) = contexto
    inicio, fim = periodo()
    reserva = Reserva(
        id_reserva=1,
        cliente_id=999,
        cliente_usuario="outro",
        cliente_nome="Outro",
        veiculo_id=10,
        veiculo_tipo="Carro",
        veiculo_modelo="Civic",
        data_inicio=inicio,
        data_fim=fim,
    )
    repository.reservas.append(
        reserva
    )

    with pytest.raises(
        RegraDeNegocio,
        match="não pertence",
    ):
        service.cancelar_do_cliente(
            1,
            cliente,
        )


def test_reserva_do_cliente_pode_ser_convertida_no_inicio(
    contexto,
):
    (
        service,
        cliente,
        repository,
        _,
        _,
    ) = contexto

    hoje = date.today()
    fim = (
        hoje
        + timedelta(days=3)
    )
    reserva = Reserva(
        id_reserva=1,
        cliente_id=cliente.id,
        cliente_usuario=(
            cliente.usuario
        ),
        cliente_nome=cliente.nome,
        veiculo_id=10,
        veiculo_tipo="Carro",
        veiculo_modelo="Civic",
        data_inicio=hoje.isoformat(),
        data_fim=fim.isoformat(),
    )
    repository.reservas.append(
        reserva
    )

    encontrada = (
        service.validar_inicio_aluguel(
            cliente=cliente,
            id_veiculo=10,
            data_inicio=(
                hoje.isoformat()
            ),
            data_fim=(
                (
                    hoje
                    + timedelta(days=2)
                )
                .isoformat()
            ),
        )
    )

    assert encontrada is reserva

    service.converter_para_aluguel(
        reserva
    )
    assert reserva.status == "convertida"
