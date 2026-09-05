import pytest

from sqlalchemy.exc import IntegrityError

from modulos.alugueis import Aluguel
from modulos.clientes import Cliente
from modulos.database import BancoSQLAlchemy
from modulos.models import (
    AluguelModel,
    Base,
    ClienteModel,
    VeiculoModel,
)
from modulos.repositories.aluguel_repository import AluguelRepository
from modulos.veiculos import Carro


@pytest.fixture
def banco_orm(tmp_path):
    caminho = tmp_path / "aluguel_repository_unit.db"

    banco = BancoSQLAlchemy(
        f"sqlite:///{caminho.as_posix()}"
    )

    Base.metadata.create_all(
        banco.engine
    )

    try:
        yield banco
    finally:
        banco.fechar()


def criar_contexto(
    banco,
):
    with banco.criar_sessao() as sessao:
        sessao.add_all(
            [
                ClienteModel(
                    id=1,
                    nome="Lucas Silva",
                    usuario="lucas",
                    email="lucas@email.com",
                    senha_hash="",
                    ativo=True,
                    usuario_id=None,
                ),
                VeiculoModel(
                    id=10,
                    tipo="Carro",
                    modelo="Civic",
                    ano=2025,
                    diaria=100,
                    preco_km=0.5,
                    quilometragem=0,
                    status="disponivel",
                    disponivel=True,
                    alugado_por=None,
                    ativo=True,
                ),
            ]
        )
        sessao.commit()

    cliente = Cliente(
        id_cliente=1,
        nome="Lucas Silva",
        usuario="lucas",
        email="lucas@email.com",
    )

    veiculo = Carro(
        id_veiculo=10,
        modelo="Civic",
        ano=2025,
        diaria=100,
        preco_km=0.5,
    )

    repository = AluguelRepository(
        banco_sqlalchemy=banco,
    )

    return repository, cliente, veiculo


def criar_aluguel(
    cliente,
    veiculo,
):
    return Aluguel(
        id_aluguel=0,
        cliente_id=cliente.id,
        cliente_usuario=cliente.usuario,
        cliente_nome=cliente.nome,
        veiculo_id=veiculo.id,
        veiculo_tipo=veiculo.tipo,
        veiculo_modelo=veiculo.modelo,
        dias=3,
        data_inicio="2026-09-01",
        data_prevista="2026-09-04",
    )


def registrar_ativo(
    repository,
    cliente,
    veiculo,
):
    assert veiculo.alugar(
        cliente.usuario
    ) is True

    aluguel = criar_aluguel(
        cliente,
        veiculo,
    )

    aluguel.id = repository.registrar(
        aluguel,
        veiculo,
    )

    return aluguel


def test_repository_exige_banco_sqlalchemy():
    with pytest.raises(
        ValueError,
        match="BancoSQLAlchemy é obrigatório.",
    ):
        AluguelRepository(None)


def test_repository_nao_possui_estado_legado(
    banco_orm,
):
    repository = AluguelRepository(
        banco_orm
    )

    assert not hasattr(
        repository,
        "dados",
    )
    assert not hasattr(
        repository,
        "alugueis",
    )
    assert not hasattr(
        repository,
        "usa_sqlalchemy",
    )
    assert not hasattr(
        repository,
        "adicionar_na_colecao",
    )


def test_registrar_aluguel(
    banco_orm,
):
    repository, cliente, veiculo = criar_contexto(
        banco_orm
    )

    aluguel = registrar_ativo(
        repository,
        cliente,
        veiculo,
    )

    assert aluguel.id > 0


def test_listar_ativos_cliente(
    banco_orm,
):
    repository, cliente, veiculo = criar_contexto(
        banco_orm
    )
    aluguel = registrar_ativo(
        repository,
        cliente,
        veiculo,
    )

    resultado = repository.listar_ativos_cliente(
        cliente
    )

    assert [item.id for item in resultado] == [
        aluguel.id
    ]


def test_listar_do_cliente(
    banco_orm,
):
    repository, cliente, veiculo = criar_contexto(
        banco_orm
    )
    aluguel = registrar_ativo(
        repository,
        cliente,
        veiculo,
    )

    resultado = repository.listar_do_cliente(
        cliente
    )

    assert [item.id for item in resultado] == [
        aluguel.id
    ]


def test_buscar_ativo(
    banco_orm,
):
    repository, cliente, veiculo = criar_contexto(
        banco_orm
    )
    aluguel = registrar_ativo(
        repository,
        cliente,
        veiculo,
    )

    resultado = repository.buscar_ativo(
        cliente
    )

    assert resultado.id == aluguel.id


def test_buscar_ativo_por_veiculo(
    banco_orm,
):
    repository, cliente, veiculo = criar_contexto(
        banco_orm
    )
    aluguel = registrar_ativo(
        repository,
        cliente,
        veiculo,
    )

    resultado = repository.buscar_ativo(
        cliente,
        id_veiculo=veiculo.id,
    )

    assert resultado.id == aluguel.id


def test_buscar_ativo_inexistente(
    banco_orm,
):
    repository, cliente, _ = criar_contexto(
        banco_orm
    )

    assert repository.buscar_ativo(
        cliente
    ) is None


def test_listar_colecao(
    banco_orm,
):
    repository, cliente, veiculo = criar_contexto(
        banco_orm
    )
    aluguel = registrar_ativo(
        repository,
        cliente,
        veiculo,
    )

    resultado = repository.listar_colecao()

    assert [item.id for item in resultado] == [
        aluguel.id
    ]


def test_listar_ativos(
    banco_orm,
):
    repository, cliente, veiculo = criar_contexto(
        banco_orm
    )
    aluguel = registrar_ativo(
        repository,
        cliente,
        veiculo,
    )

    resultado = repository.listar_ativos()

    assert [item.id for item in resultado] == [
        aluguel.id
    ]


def test_devolucao_remove_aluguel_da_lista_de_ativos(
    banco_orm,
):
    repository, cliente, veiculo = criar_contexto(
        banco_orm
    )
    aluguel = registrar_ativo(
        repository,
        cliente,
        veiculo,
    )

    aluguel.finalizar(
        km=50,
        valor=350,
        forma_pagamento="Pix",
    )
    veiculo.adicionar_quilometragem(
        50
    )
    veiculo.devolver()

    repository.registrar_devolucao(
        aluguel,
        veiculo,
    )

    assert repository.listar_ativos() == []
    assert len(
        repository.listar_colecao()
    ) == 1


def test_registrar_faz_rollback_com_cliente_inexistente(
    banco_orm,
):
    repository, _, veiculo = criar_contexto(
        banco_orm
    )

    cliente = Cliente(
        id_cliente=999,
        nome="Fantasma",
        usuario="fantasma",
        email="fantasma@email.com",
    )

    veiculo.alugar(
        cliente.usuario
    )
    aluguel = criar_aluguel(
        cliente,
        veiculo,
    )

    with pytest.raises(
        IntegrityError
    ):
        repository.registrar(
            aluguel,
            veiculo,
        )

    with banco_orm.criar_sessao() as sessao:
        assert sessao.query(
            AluguelModel
        ).count() == 0

        model_veiculo = sessao.get(
            VeiculoModel,
            veiculo.id,
        )
        assert model_veiculo.disponivel is True
