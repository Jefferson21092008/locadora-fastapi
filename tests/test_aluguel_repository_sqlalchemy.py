import pytest

from sqlalchemy.exc import (
    IntegrityError,
)

from modulos.alugueis import (
    Aluguel,
)
from modulos.clientes import (
    Cliente,
)
from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.models import (
    AluguelModel,
    Base,
    ClienteModel,
    VeiculoModel,
)
from modulos.repositories.aluguel_repository import (
    AluguelRepository,
)
from modulos.veiculos import (
    Carro,
    StatusVeiculo,
)


@pytest.fixture
def banco_orm(tmp_path):
    caminho = (
        tmp_path
        / "aluguel_repository.db"
    )

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


@pytest.fixture
def contexto(banco_orm):
    cliente_model = ClienteModel(
        id=1,
        nome="Lucas Silva",
        usuario="lucas",
        email="lucas@email.com",
        senha_hash="",
        ativo=True,
        usuario_id=None,
    )

    veiculo_model = VeiculoModel(
        id=10,
        tipo="Carro",
        modelo="Civic",
        ano=2024,
        diaria=100,
        preco_km=2,
        quilometragem=1000,
        status="disponivel",
        disponivel=True,
        alugado_por=None,
        ativo=True,
    )

    with banco_orm.criar_sessao() as sessao:
        sessao.add_all(
            [
                cliente_model,
                veiculo_model,
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
        ano=2024,
        diaria=100,
        preco_km=2,
        quilometragem=1000,
        status="disponivel",
    )

    repository = AluguelRepository(
        banco_sqlalchemy=banco_orm,
    )

    return (
        repository,
        cliente,
        veiculo,
    )


def criar_aluguel(
    cliente,
    veiculo,
    id_aluguel=0,
):
    return Aluguel(
        id_aluguel=id_aluguel,
        cliente_id=cliente.id,
        cliente_usuario=cliente.usuario,
        cliente_nome=cliente.nome,
        veiculo_id=veiculo.id,
        veiculo_tipo=veiculo.tipo,
        veiculo_modelo=veiculo.modelo,
        dias=3,
        data_inicio="2026-08-31",
        data_prevista="2026-09-03",
    )


def registrar_aluguel_ativo(
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


def test_registrar_aluguel_persiste_e_aluga_veiculo(
    banco_orm,
    contexto,
):
    repository, cliente, veiculo = contexto

    aluguel = registrar_aluguel_ativo(
        repository,
        cliente,
        veiculo,
    )

    assert aluguel.id > 0

    with banco_orm.criar_sessao() as sessao:
        model_aluguel = sessao.get(
            AluguelModel,
            aluguel.id,
        )
        model_veiculo = sessao.get(
            VeiculoModel,
            veiculo.id,
        )

        assert model_aluguel is not None
        assert model_aluguel.status == "ativo"
        assert model_aluguel.cliente_id == cliente.id
        assert model_aluguel.veiculo_id == veiculo.id

        assert model_veiculo.status == "alugado"
        assert model_veiculo.disponivel is False
        assert model_veiculo.alugado_por == "lucas"


def test_listar_ativos_cliente_consulta_banco(
    contexto,
):
    repository, cliente, veiculo = contexto

    aluguel = registrar_aluguel_ativo(
        repository,
        cliente,
        veiculo,
    )

    resultado = repository.listar_ativos_cliente(
        cliente
    )

    assert len(resultado) == 1
    assert resultado[0].id == aluguel.id
    assert resultado[0].ativo is True


def test_buscar_ativo_por_veiculo_consulta_banco(
    contexto,
):
    repository, cliente, veiculo = contexto

    aluguel = registrar_aluguel_ativo(
        repository,
        cliente,
        veiculo,
    )

    encontrado = repository.buscar_ativo(
        cliente,
        id_veiculo=veiculo.id,
    )

    assert encontrado is not None
    assert encontrado.id == aluguel.id
    assert encontrado.veiculo_id == veiculo.id


def test_registrar_devolucao_atualiza_aluguel_e_veiculo(
    banco_orm,
    contexto,
):
    repository, cliente, veiculo = contexto

    aluguel = registrar_aluguel_ativo(
        repository,
        cliente,
        veiculo,
    )

    aluguel.finalizar(
        km=50,
        valor=400,
        forma_pagamento="Pix",
        dias_atraso=1,
        multa=20,
    )

    veiculo.adicionar_quilometragem(
        50
    )
    assert veiculo.devolver() is True

    repository.registrar_devolucao(
        aluguel,
        veiculo,
    )

    with banco_orm.criar_sessao() as sessao:
        model_aluguel = sessao.get(
            AluguelModel,
            aluguel.id,
        )
        model_veiculo = sessao.get(
            VeiculoModel,
            veiculo.id,
        )

        assert model_aluguel.status == "finalizado"
        assert model_aluguel.km == 50
        assert model_aluguel.pagamento == "Pix"
        assert model_aluguel.valor == 400
        assert model_aluguel.dias_atraso == 1
        assert model_aluguel.multa == 20
        assert model_aluguel.data_fim is not None

        assert model_veiculo.quilometragem == 1050
        assert model_veiculo.status == "disponivel"
        assert model_veiculo.disponivel is True
        assert model_veiculo.alugado_por is None


def test_listar_do_cliente_inclui_finalizados(
    contexto,
):
    repository, cliente, veiculo = contexto

    aluguel = registrar_aluguel_ativo(
        repository,
        cliente,
        veiculo,
    )

    aluguel.finalizar(
        km=10,
        valor=320,
        forma_pagamento="Dinheiro",
    )
    veiculo.adicionar_quilometragem(
        10
    )
    veiculo.devolver()

    repository.registrar_devolucao(
        aluguel,
        veiculo,
    )

    resultado = repository.listar_do_cliente(
        cliente
    )

    assert len(resultado) == 1
    assert resultado[0].id == aluguel.id
    assert resultado[0].ativo is False


def test_listar_colecao_e_listar_ativos_usam_banco(
    contexto,
):
    repository, cliente, veiculo = contexto

    aluguel = registrar_aluguel_ativo(
        repository,
        cliente,
        veiculo,
    )

    todos = repository.listar_colecao()
    ativos = repository.listar_ativos()

    assert [item.id for item in todos] == [
        aluguel.id
    ]
    assert [item.id for item in ativos] == [
        aluguel.id
    ]


def test_repository_sqlalchemy_nao_tem_modo_legado(
    banco_orm,
):
    repository = AluguelRepository(
        banco_sqlalchemy=banco_orm,
    )

    assert not hasattr(repository, "dados")
    assert not hasattr(repository, "alugueis")
    assert not hasattr(repository, "usa_sqlalchemy")
    assert not hasattr(repository, "adicionar_na_colecao")


def test_repository_sqlalchemy_exige_banco():
    with pytest.raises(
        ValueError,
        match="BancoSQLAlchemy é obrigatório.",
    ):
        AluguelRepository(None)


def test_registrar_faz_rollback_se_cliente_nao_existir(
    banco_orm,
    contexto,
):
    repository, _, veiculo = contexto

    cliente_inexistente = Cliente(
        id_cliente=999,
        nome="Cliente Inexistente",
        usuario="fantasma",
        email="fantasma@email.com",
    )

    veiculo.alugar(
        cliente_inexistente.usuario
    )

    aluguel = criar_aluguel(
        cliente_inexistente,
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
        alugueis = (
            sessao.query(
                AluguelModel
            )
            .all()
        )

        model_veiculo = sessao.get(
            VeiculoModel,
            veiculo.id,
        )

        assert alugueis == []
        assert model_veiculo.status == "disponivel"
        assert model_veiculo.disponivel is True
        assert model_veiculo.alugado_por is None
