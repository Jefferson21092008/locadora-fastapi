import pytest

from sqlalchemy.exc import (
    IntegrityError,
)

from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.models import (
    Base,
    VeiculoModel,
)
from modulos.repositories.veiculo_repository import (
    VeiculoRepository,
)
from modulos.veiculos import (
    Bicicleta,
    Caminhao,
    Carro,
    Moto,
    StatusVeiculo,
    criar_veiculo_por_tipo,
)


@pytest.fixture
def banco_sqlalchemy(
    tmp_path,
):
    caminho = (
        tmp_path
        / "veiculos_sqlalchemy.db"
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


def criar_repository(
    banco_sqlalchemy,
):
    return VeiculoRepository(
        banco_sqlalchemy=(
            banco_sqlalchemy
        )
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


def test_inserir_e_buscar_veiculo_com_sqlalchemy(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    carro = criar_veiculo()

    novo_id = repository.inserir(
        carro
    )

    encontrado = repository.buscar_por_id(
        novo_id
    )

    assert novo_id == 1
    assert isinstance(
        encontrado,
        Carro,
    )
    assert encontrado.modelo == "Civic"
    assert encontrado.status == StatusVeiculo.DISPONIVEL
    assert encontrado.disponivel is True
    assert encontrado.ativo is True


def test_mapeamento_preserva_tipos_de_veiculo(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    dados = [
        ("carro", "Civic", Carro),
        ("moto", "CB 500", Moto),
        ("caminhao", "Actros", Caminhao),
        ("bicicleta", "Caloi", Bicicleta),
    ]

    for tipo, modelo, _ in dados:
        repository.inserir(
            criar_veiculo(
                tipo=tipo,
                modelo=modelo,
            )
        )

    encontrados = (
        repository
        .listar_colecao()
    )

    assert len(encontrados) == 4

    for encontrado, (_, _, classe) in zip(
        encontrados,
        dados,
    ):
        assert isinstance(
            encontrado,
            classe,
        )


def test_atualizar_veiculo_com_sqlalchemy(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    carro = criar_veiculo()
    carro.id = repository.inserir(
        carro
    )

    carro.modelo = "Civic Touring"
    carro.diaria = 180
    carro.quilometragem = 1234.5
    carro.alugar(
        "lucas"
    )

    repository.atualizar(
        carro
    )

    atualizado = repository.buscar_por_id(
        carro.id
    )

    assert atualizado.modelo == "Civic Touring"
    assert atualizado.diaria == 180
    assert atualizado.quilometragem == 1234.5
    assert atualizado.status == StatusVeiculo.ALUGADO
    assert atualizado.alugado_por == "lucas"
    assert atualizado.disponivel is False


def test_listagens_por_status_usam_banco_sqlalchemy(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    disponivel = criar_veiculo(
        modelo="Disponível"
    )
    alugado = criar_veiculo(
        modelo="Alugado"
    )
    manutencao = criar_veiculo(
        modelo="Manutenção"
    )
    desativado = criar_veiculo(
        modelo="Desativado"
    )

    alugado.alugar(
        "lucas"
    )
    manutencao.enviar_para_manutencao()
    desativado.desativar()

    for veiculo in (
        disponivel,
        alugado,
        manutencao,
        desativado,
    ):
        repository.inserir(
            veiculo
        )

    assert [
        v.modelo
        for v in repository.listar_disponiveis()
    ] == ["Disponível"]

    assert [
        v.modelo
        for v in repository.listar_alugados()
    ] == ["Alugado"]

    assert [
        v.modelo
        for v in repository.listar_em_manutencao()
    ] == ["Manutenção"]

    assert [
        v.modelo
        for v in repository.listar_desativados()
    ] == ["Desativado"]

    assert [
        v.modelo
        for v in repository.listar_ativos()
    ] == [
        "Disponível",
        "Alugado",
        "Manutenção",
    ]


def test_buscar_reutiliza_normalizacao_do_dominio(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    repository.inserir(
        criar_veiculo(
            tipo="caminhao",
            modelo="Mercedes Actros",
        )
    )

    por_tipo = repository.buscar(
        "  CAMINHAO  "
    )

    por_modelo = repository.buscar(
        "actros"
    )

    assert len(por_tipo) == 1
    assert isinstance(
        por_tipo[0],
        Caminhao,
    )
    assert len(por_modelo) == 1
    assert por_modelo[0].modelo == "Mercedes Actros"


def test_buscar_termo_vazio_no_modo_sqlalchemy(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    repository.inserir(
        criar_veiculo()
    )

    assert repository.buscar(
        "   "
    ) == []


def test_repository_nao_possui_estado_legado(
    banco_sqlalchemy,
):
    repository = criar_repository(
        banco_sqlalchemy
    )

    assert not hasattr(
        repository,
        "dados",
    )
    assert not hasattr(
        repository,
        "veiculos",
    )
    assert not hasattr(
        repository,
        "usa_sqlalchemy",
    )
    assert not hasattr(
        repository,
        "adicionar_na_colecao",
    )


def test_repository_exige_banco_sqlalchemy():
    with pytest.raises(
        ValueError,
        match="BancoSQLAlchemy é obrigatório",
    ):
        VeiculoRepository(
            banco_sqlalchemy=None,
        )


def test_model_rejeita_status_invalido(
    banco_sqlalchemy,
):
    with banco_sqlalchemy.criar_sessao() as sessao:
        model = VeiculoModel(
            tipo="Carro",
            modelo="Civic",
            ano=2025,
            diaria=100,
            preco_km=0.5,
            quilometragem=0,
            status="voando",
            disponivel=True,
            alugado_por=None,
            ativo=True,
        )

        sessao.add(
            model
        )

        with pytest.raises(
            IntegrityError
        ):
            sessao.commit()

        sessao.rollback()
