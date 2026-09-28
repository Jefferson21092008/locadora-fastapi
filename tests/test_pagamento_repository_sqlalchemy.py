import pytest

from modulos.database import BancoSQLAlchemy
from modulos.models import (
    AluguelModel,
    Base,
    ClienteModel,
    VeiculoModel,
)
from modulos.pagamentos import (
    PagamentoFinanceiro,
)
from modulos.repositories.pagamento_repository import (
    PagamentoRepository,
)


@pytest.fixture
def ambiente(tmp_path):
    caminho = tmp_path / "pagamentos.db"
    banco = BancoSQLAlchemy(
        f"sqlite:///{caminho.as_posix()}"
    )
    Base.metadata.create_all(
        banco.engine
    )

    with banco.criar_sessao() as sessao:
        cliente = ClienteModel(
            nome="Lucas",
            usuario="lucas-fin",
            email="lucas-fin@example.com",
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
            status="disponivel",
            disponivel=True,
            alugado_por=None,
            ativo=True,
        )
        sessao.add_all([cliente, veiculo])
        sessao.flush()

        aluguel = AluguelModel(
            cliente_id=cliente.id,
            veiculo_id=veiculo.id,
            cliente_usuario=cliente.usuario,
            cliente_nome=cliente.nome,
            veiculo_tipo=veiculo.tipo,
            veiculo_modelo=veiculo.modelo,
            dias=3,
            status="finalizado",
            km=100,
            pagamento="Pix",
            valor=450,
            data_inicio="2026-09-20",
            data_prevista="2026-09-23",
            data_fim="2026-09-23",
            dias_atraso=0,
            multa=0,
        )
        sessao.add(aluguel)
        sessao.commit()
        aluguel_id = aluguel.id

    repository = PagamentoRepository(
        banco
    )

    try:
        yield repository, aluguel_id
    finally:
        banco.fechar()


def test_repository_registra_lista_e_estorna(
    ambiente,
):
    repository, aluguel_id = ambiente
    pagamento = PagamentoFinanceiro(
        id_pagamento=0,
        aluguel_id=aluguel_id,
        valor=200,
        forma="credito",
        parcelas=2,
        observacoes="Dano.",
    )

    registrado = repository.registrar(
        pagamento
    )

    assert registrado.id > 0
    assert registrado.valor == 200
    assert len(
        repository.listar_por_aluguel(
            aluguel_id
        )
    ) == 1

    registrado.estornar()
    atualizado = repository.atualizar(
        registrado
    )

    assert atualizado.status == "estornado"
    assert atualizado.estornado_em is not None
