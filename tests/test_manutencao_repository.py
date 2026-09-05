import pytest

from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.manutencoes import (
    Manutencao,
)
from modulos.models import (
    Base,
    ManutencaoModel,
    VeiculoModel,
)
from modulos.repositories.manutencao_repository import (
    ManutencaoRepository,
)
from modulos.veiculos import (
    Carro,
)


@pytest.fixture
def banco_orm(tmp_path):
    caminho = (
        tmp_path
        / "manutencao_repository_unit.db"
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


def criar_contexto(
    banco,
):
    with banco.criar_sessao() as sessao:
        sessao.add(
            VeiculoModel(
                id=10,
                tipo="Carro",
                modelo="Civic",
                ano=2025,
                diaria=100,
                preco_km=0.5,
                quilometragem=50000,
                status="disponivel",
                disponivel=True,
                alugado_por=None,
                ativo=True,
            )
        )
        sessao.commit()

    veiculo = Carro(
        id_veiculo=10,
        modelo="Civic",
        ano=2025,
        diaria=100,
        preco_km=0.5,
        quilometragem=50000,
        status="disponivel",
    )

    repository = ManutencaoRepository(
        banco_sqlalchemy=banco,
    )

    return repository, veiculo


def criar_manutencao(
    veiculo,
    id_manutencao=0,
    motivo="Troca de óleo",
):
    return Manutencao(
        id_manutencao=id_manutencao,
        veiculo_id=veiculo.id,
        motivo=motivo,
        quilometragem=veiculo.quilometragem,
    )


def abrir_manutencao(
    repository,
    veiculo,
    motivo="Troca de óleo",
):
    manutencao = criar_manutencao(
        veiculo,
        motivo=motivo,
    )

    assert veiculo.enviar_para_manutencao() is True

    manutencao.id = repository.registrar(
        manutencao,
        veiculo,
    )

    return manutencao


def test_repository_exige_banco_sqlalchemy():
    with pytest.raises(
        ValueError,
        match="BancoSQLAlchemy é obrigatório.",
    ):
        ManutencaoRepository(None)


def test_repository_nao_possui_estado_legado(
    banco_orm,
):
    repository = ManutencaoRepository(
        banco_orm
    )

    assert not hasattr(repository, "dados")
    assert not hasattr(repository, "manutencoes")
    assert not hasattr(repository, "usa_sqlalchemy")
    assert not hasattr(repository, "adicionar_na_colecao")


def test_buscar_ativa_por_veiculo(
    banco_orm,
):
    repository, veiculo = criar_contexto(
        banco_orm
    )
    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    resultado = repository.buscar_ativa_por_veiculo(
        veiculo.id
    )

    assert resultado.id == manutencao.id
    assert resultado.ativa is True


def test_buscar_ativa_ignora_finalizada(
    banco_orm,
):
    repository, veiculo = criar_contexto(
        banco_orm
    )
    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    manutencao.finalizar(
        custo=200,
        data_fim="2026-09-02",
    )
    veiculo.finalizar_manutencao()
    repository.registrar_finalizacao(
        manutencao,
        veiculo,
    )

    assert repository.buscar_ativa_por_veiculo(
        veiculo.id
    ) is None


def test_listar_por_veiculo(
    banco_orm,
):
    repository, veiculo = criar_contexto(
        banco_orm
    )
    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    resultado = repository.listar_por_veiculo(
        veiculo.id
    )

    assert [item.id for item in resultado] == [
        manutencao.id
    ]


def test_listar_ativas(
    banco_orm,
):
    repository, veiculo = criar_contexto(
        banco_orm
    )
    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    resultado = repository.listar_ativas()

    assert [item.id for item in resultado] == [
        manutencao.id
    ]


def test_registrar_manutencao(
    banco_orm,
):
    repository, veiculo = criar_contexto(
        banco_orm
    )

    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    assert manutencao.id > 0

    with banco_orm.criar_sessao() as sessao:
        model = sessao.get(
            ManutencaoModel,
            manutencao.id,
        )
        veiculo_model = sessao.get(
            VeiculoModel,
            veiculo.id,
        )

        assert model is not None
        assert model.status == "ativa"
        assert veiculo_model.status == "manutencao"


def test_registrar_finalizacao(
    banco_orm,
):
    repository, veiculo = criar_contexto(
        banco_orm
    )
    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    manutencao.finalizar(
        custo=350,
        data_fim="2026-09-02",
    )
    veiculo.finalizar_manutencao()

    repository.registrar_finalizacao(
        manutencao,
        veiculo,
    )

    with banco_orm.criar_sessao() as sessao:
        model = sessao.get(
            ManutencaoModel,
            manutencao.id,
        )
        veiculo_model = sessao.get(
            VeiculoModel,
            veiculo.id,
        )

        assert model.status == "finalizada"
        assert model.custo == 350
        assert veiculo_model.status == "disponivel"


def test_listar_colecao(
    banco_orm,
):
    repository, veiculo = criar_contexto(
        banco_orm
    )
    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    resultado = repository.listar_colecao()

    assert [item.id for item in resultado] == [
        manutencao.id
    ]


def test_buscar_ativa_veiculo_inexistente(
    banco_orm,
):
    repository, _ = criar_contexto(
        banco_orm
    )

    assert repository.buscar_ativa_por_veiculo(
        999
    ) is None


def test_listar_por_veiculo_sem_resultados(
    banco_orm,
):
    repository, _ = criar_contexto(
        banco_orm
    )

    assert repository.listar_por_veiculo(
        999
    ) == []


def test_listar_ativas_com_todas_finalizadas(
    banco_orm,
):
    repository, veiculo = criar_contexto(
        banco_orm
    )
    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    manutencao.finalizar(
        custo=250,
        data_fim="2026-09-02",
    )
    veiculo.finalizar_manutencao()
    repository.registrar_finalizacao(
        manutencao,
        veiculo,
    )

    assert repository.listar_ativas() == []
