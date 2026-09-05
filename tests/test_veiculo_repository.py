import pytest

from modulos.database import BancoSQLAlchemy
from modulos.models import Base
from modulos.repositories.veiculo_repository import (
    VeiculoRepository,
)
from modulos.veiculos import (
    StatusVeiculo,
    criar_veiculo_por_tipo,
)


@pytest.fixture
def banco_sqlalchemy(tmp_path):
    caminho = tmp_path / "veiculo_repository.db"
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
def repository(banco_sqlalchemy):
    return VeiculoRepository(
        banco_sqlalchemy=banco_sqlalchemy,
    )


def criar_veiculo(
    tipo="carro",
    modelo="Civic",
):
    veiculo = criar_veiculo_por_tipo(
        tipo=tipo,
        id_veiculo=0,
        modelo=modelo,
        ano=2025,
        diaria=100,
        preco_km=0.50,
    )

    assert veiculo is not None
    return veiculo


def persistir(repository, veiculo):
    veiculo.id = repository.inserir(
        veiculo
    )
    return veiculo


def test_buscar_por_id(repository):
    carro = persistir(
        repository,
        criar_veiculo(),
    )

    resultado = repository.buscar_por_id(
        carro.id
    )

    assert resultado.id == carro.id
    assert resultado.modelo == carro.modelo


def test_buscar_id_inexistente(repository):
    assert repository.buscar_por_id(
        999
    ) is None


def test_buscar_por_modelo(repository):
    persistir(
        repository,
        criar_veiculo(
            modelo="Honda Civic"
        ),
    )
    persistir(
        repository,
        criar_veiculo(
            tipo="moto",
            modelo="Honda CG",
        ),
    )

    resultado = repository.buscar(
        "Civic"
    )

    assert len(resultado) == 1
    assert resultado[0].modelo == "Honda Civic"


def test_listar_colecao(repository):
    persistir(
        repository,
        criar_veiculo(),
    )
    persistir(
        repository,
        criar_veiculo(
            tipo="moto",
            modelo="CB 500",
        ),
    )

    resultado = repository.listar_colecao()

    assert len(resultado) == 2


def test_listar_disponiveis(repository):
    carro = persistir(
        repository,
        criar_veiculo(),
    )
    moto = criar_veiculo(
        tipo="moto",
        modelo="CB 500",
    )
    assert moto.enviar_para_manutencao() is True
    persistir(repository, moto)

    resultado = repository.listar_disponiveis()

    assert [v.id for v in resultado] == [carro.id]


def test_listar_ativos(repository):
    carro = persistir(
        repository,
        criar_veiculo(),
    )
    moto = criar_veiculo(
        tipo="moto",
        modelo="CB 500",
    )
    sucesso, _ = moto.desativar()
    assert sucesso is True
    persistir(repository, moto)

    resultado = repository.listar_ativos()

    assert [v.id for v in resultado] == [carro.id]


def test_listar_desativados(repository):
    carro = criar_veiculo()
    sucesso, _ = carro.desativar()
    assert sucesso is True
    persistir(repository, carro)

    resultado = repository.listar_desativados()

    assert len(resultado) == 1
    assert resultado[0].id == carro.id


def test_listar_em_manutencao(repository):
    carro = criar_veiculo()
    assert carro.enviar_para_manutencao() is True
    persistir(repository, carro)

    resultado = repository.listar_em_manutencao()

    assert len(resultado) == 1
    assert resultado[0].id == carro.id


def test_inserir_veiculo(repository):
    novo_id = repository.inserir(
        criar_veiculo()
    )

    assert novo_id == 1
    assert repository.buscar_por_id(
        novo_id
    ) is not None


def test_atualizar_veiculo(repository):
    carro = persistir(
        repository,
        criar_veiculo(),
    )
    carro.modelo = "Civic Touring"

    repository.atualizar(
        carro
    )

    atualizado = repository.buscar_por_id(
        carro.id
    )
    assert atualizado.modelo == "Civic Touring"


def test_listar_alugados(repository):
    carro = criar_veiculo()
    assert carro.alugar("lucas") is True
    persistir(repository, carro)

    resultado = repository.listar_alugados()

    assert len(resultado) == 1
    assert resultado[0].status == StatusVeiculo.ALUGADO


def test_buscar_termo_vazio(repository):
    persistir(
        repository,
        criar_veiculo(),
    )

    assert repository.buscar(
        "   "
    ) == []


def test_buscar_ignora_veiculo_desativado(repository):
    carro = criar_veiculo()
    sucesso, _ = carro.desativar()
    assert sucesso is True
    persistir(repository, carro)

    assert repository.buscar(
        "Civic"
    ) == []


def test_listar_colecao_retorna_novas_entidades(repository):
    carro = persistir(
        repository,
        criar_veiculo(),
    )

    primeira = repository.listar_colecao()
    segunda = repository.listar_colecao()

    assert primeira[0].id == carro.id
    assert segunda[0].id == carro.id
    assert primeira is not segunda
    assert primeira[0] is not segunda[0]


def test_repository_exige_banco_sqlalchemy():
    with pytest.raises(
        ValueError,
        match="BancoSQLAlchemy é obrigatório",
    ):
        VeiculoRepository(
            banco_sqlalchemy=None,
        )
