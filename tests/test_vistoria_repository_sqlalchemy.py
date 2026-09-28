import pytest

from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.models import (
    AluguelModel,
    Base,
    ClienteModel,
    VeiculoModel,
)
from modulos.repositories.vistoria_repository import (
    VistoriaRepository,
)
from modulos.vistorias import (
    CaucaoAluguel,
    DanoAluguel,
    InspecaoAluguel,
    MultaTransito,
)


@pytest.fixture
def ambiente(tmp_path):
    caminho = (
        tmp_path
        / "vistoria_repository.db"
    )

    banco = BancoSQLAlchemy(
        f"sqlite:///{caminho.as_posix()}"
    )

    Base.metadata.create_all(
        banco.engine
    )

    with banco.criar_sessao() as sessao:
        cliente = ClienteModel(
            nome="Lucas",
            usuario="lucas-vistoria",
            email="lucas-vistoria@example.com",
            senha_hash="",
            ativo=True,
        )
        veiculo = VeiculoModel(
            tipo="carro",
            modelo="Civic",
            ano=2025,
            diaria=150,
            preco_km=0.5,
            quilometragem=15000,
            status="alugado",
            disponivel=False,
            alugado_por="lucas-vistoria",
            ativo=True,
        )
        sessao.add_all(
            [
                cliente,
                veiculo,
            ]
        )
        sessao.flush()

        aluguel = AluguelModel(
            cliente_id=cliente.id,
            veiculo_id=veiculo.id,
            cliente_usuario=cliente.usuario,
            cliente_nome=cliente.nome,
            veiculo_tipo=veiculo.tipo,
            veiculo_modelo=veiculo.modelo,
            dias=3,
            status="ativo",
            km=0,
            pagamento=None,
            valor=0,
            data_inicio="2026-09-28",
            data_prevista="2026-10-01",
            data_fim=None,
            dias_atraso=0,
            multa=0,
        )
        sessao.add(
            aluguel
        )
        sessao.commit()
        aluguel_id = aluguel.id

    repository = (
        VistoriaRepository(
            banco
        )
    )

    try:
        yield (
            repository,
            aluguel_id,
        )
    finally:
        banco.fechar()


def test_repository_registra_e_lista_inspecoes(
    ambiente,
):
    repository, aluguel_id = ambiente

    inspecao = InspecaoAluguel(
        id_inspecao=0,
        aluguel_id=aluguel_id,
        tipo="retirada",
        quilometragem=15000,
        combustivel_percentual=90,
        observacoes="Sem avarias aparentes.",
    )

    inspecao.id = (
        repository.registrar_inspecao(
            inspecao
        )
    )

    encontrada = (
        repository.buscar_inspecao(
            aluguel_id,
            "retirada",
        )
    )
    lista = (
        repository.listar_inspecoes(
            aluguel_id
        )
    )

    assert inspecao.id > 0
    assert encontrada.id == inspecao.id
    assert encontrada.combustivel_percentual == 90
    assert len(lista) == 1


def test_repository_persiste_cancelamento_de_dano(
    ambiente,
):
    repository, aluguel_id = ambiente

    dano = DanoAluguel(
        id_dano=0,
        aluguel_id=aluguel_id,
        descricao="Amassado na porta",
        valor_estimado=700,
    )
    dano.id = repository.registrar_dano(
        dano
    )

    dano.cancelar()
    repository.atualizar_dano(
        dano
    )

    persistido = repository.buscar_dano(
        dano.id
    )

    assert persistido.status == "cancelado"
    assert persistido.cancelada_em is not None


def test_repository_persiste_e_lista_multa(
    ambiente,
):
    repository, aluguel_id = ambiente

    multa = MultaTransito(
        id_multa=0,
        aluguel_id=aluguel_id,
        descricao="Estacionamento irregular",
        valor=130.16,
        data_ocorrencia="2026-09-28",
    )
    multa.id = repository.registrar_multa(
        multa
    )

    multas = repository.listar_multas(
        aluguel_id
    )

    assert len(multas) == 1
    assert multas[0].id == multa.id
    assert multas[0].valor == 130.16


def test_repository_faz_upsert_da_caucao(
    ambiente,
):
    repository, aluguel_id = ambiente

    caucao = CaucaoAluguel(
        id_caucao=0,
        aluguel_id=aluguel_id,
        valor=1000,
    )

    primeira = repository.salvar_caucao(
        caucao
    )

    primeira.atualizar(
        valor=1000,
        valor_liberado=400,
        observacoes="Liberação parcial.",
    )

    atualizada = repository.salvar_caucao(
        primeira
    )
    buscada = repository.buscar_caucao(
        aluguel_id
    )

    assert atualizada.id == primeira.id
    assert buscada.status == "parcial"
    assert buscada.valor_retido == 600
