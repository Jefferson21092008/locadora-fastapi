import pytest

from sqlalchemy.exc import (
    IntegrityError,
)

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
        / "manutencao_repository.db"
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
    veiculo_model = VeiculoModel(
        id=10,
        tipo="Carro",
        modelo="Civic",
        ano=2024,
        diaria=100,
        preco_km=2,
        quilometragem=50000,
        status="disponivel",
        disponivel=True,
        alugado_por=None,
        ativo=True,
    )

    with banco_orm.criar_sessao() as sessao:
        sessao.add(
            veiculo_model
        )
        sessao.commit()

    veiculo = Carro(
        id_veiculo=10,
        modelo="Civic",
        ano=2024,
        diaria=100,
        preco_km=2,
        quilometragem=50000,
        status="disponivel",
    )

    repository = ManutencaoRepository(
        banco_sqlalchemy=banco_orm,
    )

    return (
        repository,
        veiculo,
    )


def criar_manutencao(
    veiculo,
    id_manutencao=0,
    motivo="Troca de óleo",
):
    return Manutencao(
        id_manutencao=id_manutencao,
        veiculo_id=veiculo.id,
        motivo=motivo,
        quilometragem=(
            veiculo.quilometragem
        ),
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

    assert (
        veiculo.enviar_para_manutencao()
        is True
    )

    manutencao.id = repository.registrar(
        manutencao,
        veiculo,
    )

    return manutencao


def test_registrar_manutencao_persiste_e_altera_veiculo(
    banco_orm,
    contexto,
):
    repository, veiculo = contexto

    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    assert manutencao.id > 0

    with banco_orm.criar_sessao() as sessao:
        model_manutencao = sessao.get(
            ManutencaoModel,
            manutencao.id,
        )
        model_veiculo = sessao.get(
            VeiculoModel,
            veiculo.id,
        )

        assert model_manutencao is not None
        assert model_manutencao.status == "ativa"
        assert model_manutencao.veiculo_id == veiculo.id
        assert model_manutencao.quilometragem == 50000

        assert model_veiculo.status == "manutencao"
        assert model_veiculo.disponivel is False
        assert model_veiculo.alugado_por is None


def test_buscar_ativa_por_veiculo_consulta_banco(
    contexto,
):
    repository, veiculo = contexto

    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    encontrada = (
        repository
        .buscar_ativa_por_veiculo(
            veiculo.id
        )
    )

    assert encontrada is not None
    assert encontrada.id == manutencao.id
    assert encontrada.ativa is True


def test_listar_ativas_consulta_banco(
    contexto,
):
    repository, veiculo = contexto

    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    resultado = repository.listar_ativas()

    assert [item.id for item in resultado] == [
        manutencao.id
    ]


def test_finalizar_atualiza_manutencao_e_veiculo(
    banco_orm,
    contexto,
):
    repository, veiculo = contexto

    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    sucesso, _ = manutencao.finalizar(
        custo=350,
        data_fim="2026-08-31",
    )
    assert sucesso is True

    assert (
        veiculo.finalizar_manutencao()
        is True
    )

    repository.registrar_finalizacao(
        manutencao,
        veiculo,
    )

    with banco_orm.criar_sessao() as sessao:
        model_manutencao = sessao.get(
            ManutencaoModel,
            manutencao.id,
        )
        model_veiculo = sessao.get(
            VeiculoModel,
            veiculo.id,
        )

        assert model_manutencao.status == "finalizada"
        assert model_manutencao.custo == 350
        assert model_manutencao.data_fim == "2026-08-31"

        assert model_veiculo.status == "disponivel"
        assert model_veiculo.disponivel is True


def test_listar_por_veiculo_inclui_historico_finalizado(
    contexto,
):
    repository, veiculo = contexto

    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    manutencao.finalizar(
        custo=200,
        data_fim="2026-08-31",
    )
    veiculo.finalizar_manutencao()

    repository.registrar_finalizacao(
        manutencao,
        veiculo,
    )

    historico = repository.listar_por_veiculo(
        veiculo.id
    )

    assert len(historico) == 1
    assert historico[0].id == manutencao.id
    assert historico[0].ativa is False


def test_listar_colecao_consulta_banco(
    contexto,
):
    repository, veiculo = contexto

    manutencao = abrir_manutencao(
        repository,
        veiculo,
    )

    resultado = repository.listar_colecao()

    assert len(resultado) == 1
    assert resultado[0].id == manutencao.id


def test_repository_sqlalchemy_nao_tem_modo_legado(
    banco_orm,
):
    repository = ManutencaoRepository(
        banco_sqlalchemy=banco_orm,
    )

    assert not hasattr(repository, "dados")
    assert not hasattr(repository, "manutencoes")
    assert not hasattr(repository, "usa_sqlalchemy")
    assert not hasattr(repository, "adicionar_na_colecao")


def test_repository_sqlalchemy_exige_banco():
    with pytest.raises(
        ValueError,
        match="BancoSQLAlchemy é obrigatório.",
    ):
        ManutencaoRepository(None)


def test_registrar_faz_rollback_se_veiculo_nao_estiver_disponivel(
    banco_orm,
    contexto,
):
    repository, veiculo = contexto

    with banco_orm.criar_sessao() as sessao:
        model_veiculo = sessao.get(
            VeiculoModel,
            veiculo.id,
        )
        model_veiculo.status = "alugado"
        model_veiculo.disponivel = False
        model_veiculo.alugado_por = "lucas"
        sessao.commit()

    # O domínio foi alterado como aconteceria antes da
    # chamada ao repository, mas o banco rejeitará a operação.
    assert (
        veiculo.enviar_para_manutencao()
        is True
    )

    manutencao = criar_manutencao(
        veiculo
    )

    with pytest.raises(
        RuntimeError,
        match="Não foi possível alterar",
    ):
        repository.registrar(
            manutencao,
            veiculo,
        )

    with banco_orm.criar_sessao() as sessao:
        manutencoes = (
            sessao.query(
                ManutencaoModel
            )
            .all()
        )
        model_veiculo = sessao.get(
            VeiculoModel,
            veiculo.id,
        )

        assert manutencoes == []
        assert model_veiculo.status == "alugado"
        assert model_veiculo.alugado_por == "lucas"


def test_indice_impede_duas_manutencoes_ativas_no_mesmo_veiculo(
    banco_orm,
    contexto,
):
    _, veiculo = contexto

    manutencao_1 = ManutencaoModel(
        veiculo_id=veiculo.id,
        motivo="Óleo",
        quilometragem=50000,
        custo=0,
        data_inicio="2026-08-31",
        data_fim=None,
        status="ativa",
    )
    manutencao_2 = ManutencaoModel(
        veiculo_id=veiculo.id,
        motivo="Freios",
        quilometragem=50000,
        custo=0,
        data_inicio="2026-08-31",
        data_fim=None,
        status="ativa",
    )

    with banco_orm.criar_sessao() as sessao:
        sessao.add_all(
            [
                manutencao_1,
                manutencao_2,
            ]
        )

        with pytest.raises(
            IntegrityError
        ):
            sessao.commit()

        sessao.rollback()

    with banco_orm.criar_sessao() as sessao:
        quantidade = (
            sessao.query(
                ManutencaoModel
            )
            .count()
        )

        assert quantidade == 0
