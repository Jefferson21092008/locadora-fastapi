from datetime import date, timedelta

import pytest

from modulos.database import BancoSQLAlchemy
from modulos.models import (
    Base,
    ClienteModel,
    ReservaModel,
    VeiculoModel,
)
from modulos.repositories.reserva_repository import (
    ReservaRepository,
)
from modulos.reservas import Reserva


@pytest.fixture
def banco_orm(tmp_path):
    caminho = tmp_path / "reservas.db"
    banco = BancoSQLAlchemy(
        f"sqlite:///{caminho.as_posix()}"
    )
    Base.metadata.create_all(
        banco.engine
    )

    with banco.criar_sessao() as sessao:
        sessao.add(
            ClienteModel(
                id=1,
                nome="Ana Souza",
                usuario="ana123",
                email="ana@example.com",
                senha_hash="",
                ativo=True,
            )
        )
        sessao.add(
            VeiculoModel(
                id=10,
                tipo="Carro",
                modelo="Civic",
                ano=2025,
                diaria=150,
                preco_km=1.5,
                quilometragem=1000,
                status="disponivel",
                disponivel=True,
                alugado_por=None,
                ativo=True,
            )
        )
        sessao.commit()

    try:
        yield banco
    finally:
        banco.fechar()


@pytest.fixture
def repository(banco_orm):
    return ReservaRepository(
        banco_sqlalchemy=banco_orm
    )


def criar_reserva(
    inicio,
    fim,
):
    return Reserva(
        id_reserva=0,
        cliente_id=1,
        cliente_usuario="ana123",
        cliente_nome="Ana Souza",
        veiculo_id=10,
        veiculo_tipo="Carro",
        veiculo_modelo="Civic",
        data_inicio=inicio,
        data_fim=fim,
    )


def test_registrar_e_buscar_reserva(
    repository,
    banco_orm,
):
    inicio = (
        date.today()
        + timedelta(days=5)
    )
    reserva = criar_reserva(
        inicio.isoformat(),
        (
            inicio
            + timedelta(days=3)
        ).isoformat(),
    )

    reserva.id = repository.registrar(
        reserva
    )
    encontrada = repository.buscar_por_id(
        reserva.id
    )

    assert reserva.id > 0
    assert encontrada is not None
    assert encontrada.cliente_id == 1
    assert encontrada.veiculo_id == 10
    assert encontrada.status == "ativa"

    with banco_orm.criar_sessao() as sessao:
        model = sessao.get(
            ReservaModel,
            reserva.id,
        )
        assert model is not None


def test_buscar_conflitante_detecta_sobreposicao(
    repository,
):
    inicio = (
        date.today()
        + timedelta(days=10)
    )
    reserva = criar_reserva(
        inicio.isoformat(),
        (
            inicio
            + timedelta(days=5)
        ).isoformat(),
    )
    reserva.id = repository.registrar(
        reserva
    )

    conflito = repository.buscar_conflitante(
        veiculo_id=10,
        data_inicio=(
            inicio
            + timedelta(days=2)
        ).isoformat(),
        data_fim=(
            inicio
            + timedelta(days=4)
        ).isoformat(),
    )

    assert conflito is not None
    assert conflito.id == reserva.id


def test_buscar_conflitante_permite_periodos_encostados(
    repository,
):
    inicio = (
        date.today()
        + timedelta(days=10)
    )
    fim = (
        inicio
        + timedelta(days=5)
    )
    repository.registrar(
        criar_reserva(
            inicio.isoformat(),
            fim.isoformat(),
        )
    )

    conflito = repository.buscar_conflitante(
        veiculo_id=10,
        data_inicio=fim.isoformat(),
        data_fim=(
            fim
            + timedelta(days=2)
        ).isoformat(),
    )

    assert conflito is None


def test_atualizar_status_persiste_cancelamento(
    repository,
):
    inicio = (
        date.today()
        + timedelta(days=5)
    )
    reserva = criar_reserva(
        inicio.isoformat(),
        (
            inicio
            + timedelta(days=2)
        ).isoformat(),
    )
    reserva.id = repository.registrar(
        reserva
    )

    reserva.cancelar()
    repository.atualizar_status(
        reserva
    )

    encontrada = repository.buscar_por_id(
        reserva.id
    )
    assert encontrada.status == "cancelada"
    assert encontrada.cancelada_em is not None


def test_consulta_paginada_retorna_resumo(
    repository,
):
    inicio = (
        date.today()
        + timedelta(days=3)
    )

    primeira = criar_reserva(
        inicio.isoformat(),
        (
            inicio
            + timedelta(days=2)
        ).isoformat(),
    )
    primeira.id = repository.registrar(
        primeira
    )

    segunda = criar_reserva(
        (
            inicio
            + timedelta(days=3)
        ).isoformat(),
        (
            inicio
            + timedelta(days=5)
        ).isoformat(),
    )
    segunda.id = repository.registrar(
        segunda
    )
    segunda.cancelar()
    repository.atualizar_status(
        segunda
    )

    resultado = repository.consultar(
        pagina=1,
        por_pagina=1,
        status="todos",
    )

    assert resultado.total == 2
    assert len(resultado.items) == 1
    assert resultado.resumo["total"] == 2
    assert resultado.resumo["ativas"] == 1
    assert resultado.resumo["canceladas"] == 1
