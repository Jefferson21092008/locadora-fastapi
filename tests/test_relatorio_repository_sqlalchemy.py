import pytest

from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.models import (
    AluguelModel,
    Base,
    ClienteModel,
    ManutencaoModel,
    VeiculoModel,
)
from modulos.repositories.relatorio_repository import (
    RelatorioRepository,
)


@pytest.fixture
def banco_orm(tmp_path):
    caminho = (
        tmp_path
        / "relatorio_repository.db"
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
def repository(banco_orm):
    return RelatorioRepository(
        banco_sqlalchemy=banco_orm,
    )


def criar_veiculo(
    id_veiculo,
    modelo,
    tipo="Carro",
):
    return VeiculoModel(
        id=id_veiculo,
        tipo=tipo,
        modelo=modelo,
        ano=2025,
        diaria=100,
        preco_km=0.5,
        quilometragem=0,
        status="disponivel",
        disponivel=True,
        alugado_por=None,
        ativo=True,
    )


def criar_cliente(
    id_cliente,
    usuario,
    nome,
):
    return ClienteModel(
        id=id_cliente,
        nome=nome,
        usuario=usuario,
        email=f"{usuario}@email.com",
        senha_hash="hash",
        ativo=True,
        usuario_id=None,
    )


def criar_aluguel(
    id_aluguel,
    cliente_id,
    cliente_usuario,
    cliente_nome,
    veiculo_id,
    veiculo_modelo,
    valor,
    status="finalizado",
    veiculo_tipo="Carro",
):
    return AluguelModel(
        id=id_aluguel,
        cliente_id=cliente_id,
        veiculo_id=veiculo_id,
        cliente_usuario=cliente_usuario,
        cliente_nome=cliente_nome,
        veiculo_tipo=veiculo_tipo,
        veiculo_modelo=veiculo_modelo,
        dias=2,
        status=status,
        km=100,
        pagamento="Pix",
        valor=valor,
        data_inicio="2026-08-01",
        data_prevista="2026-08-03",
        data_fim=(
            "2026-08-03"
            if status == "finalizado"
            else None
        ),
        dias_atraso=0,
        multa=0,
    )


def criar_manutencao(
    id_manutencao,
    veiculo_id,
    custo,
    status="finalizada",
):
    return ManutencaoModel(
        id=id_manutencao,
        veiculo_id=veiculo_id,
        motivo="Revisão",
        quilometragem=10000,
        custo=custo,
        data_inicio="2026-08-01",
        data_fim=(
            "2026-08-02"
            if status == "finalizada"
            else None
        ),
        status=status,
    )


def test_repository_exige_banco_sqlalchemy():
    with pytest.raises(
        ValueError,
        match="BancoSQLAlchemy é obrigatório.",
    ):
        RelatorioRepository(None)


def test_repository_nao_possui_estado_legado(
    repository,
):
    assert not hasattr(
        repository,
        "dados",
    )


def test_veiculos_mais_alugados_respeita_ranking_e_limite(
    banco_orm,
    repository,
):
    with banco_orm.criar_sessao() as sessao:
        sessao.add_all(
            [
                criar_veiculo(1, "Civic"),
                criar_veiculo(2, "Corolla"),
                criar_cliente(1, "lucas", "Lucas"),
            ]
        )
        sessao.flush()

        for numero in range(1, 4):
            sessao.add(
                criar_aluguel(
                    numero,
                    1,
                    "lucas",
                    "Lucas",
                    1,
                    "Civic",
                    100,
                )
            )

        sessao.add(
            criar_aluguel(
                4,
                1,
                "lucas",
                "Lucas",
                2,
                "Corolla",
                200,
            )
        )

        sessao.commit()

    resultado = (
        repository
        .veiculos_mais_alugados(
            limite=1
        )
    )

    assert resultado == [
        {
            "id": 1,
            "tipo": "Carro",
            "modelo": "Civic",
            "total_alugueis": 3,
        }
    ]


def test_faturamento_por_tipo_considera_apenas_finalizados(
    banco_orm,
    repository,
):
    with banco_orm.criar_sessao() as sessao:
        sessao.add_all(
            [
                criar_veiculo(1, "Civic"),
                criar_veiculo(2, "CG", tipo="Moto"),
                criar_cliente(1, "lucas", "Lucas"),
            ]
        )
        sessao.flush()
        sessao.add_all(
            [
                criar_aluguel(
                    1, 1, "lucas", "Lucas",
                    1, "Civic", 400,
                ),
                criar_aluguel(
                    2, 1, "lucas", "Lucas",
                    1, "Civic", 600,
                ),
                criar_aluguel(
                    3, 1, "lucas", "Lucas",
                    1, "Civic", 999,
                    status="ativo",
                ),
                criar_aluguel(
                    4, 1, "lucas", "Lucas",
                    2, "CG", 300,
                    veiculo_tipo="Moto",
                ),
            ]
        )
        sessao.commit()

    resultado = (
        repository
        .faturamento_por_tipo()
    )

    assert resultado == [
        {
            "tipo": "Carro",
            "total_alugueis": 2,
            "faturamento": 1000.0,
        },
        {
            "tipo": "Moto",
            "total_alugueis": 1,
            "faturamento": 300.0,
        },
    ]


def test_custos_manutencao_conta_todas_e_soma_finalizadas(
    banco_orm,
    repository,
):
    with banco_orm.criar_sessao() as sessao:
        sessao.add(
            criar_veiculo(1, "Civic")
        )
        sessao.flush()
        sessao.add_all(
            [
                criar_manutencao(
                    1,
                    1,
                    250,
                ),
                criar_manutencao(
                    2,
                    1,
                    400,
                ),
                criar_manutencao(
                    3,
                    1,
                    900,
                    status="ativa",
                ),
            ]
        )
        sessao.commit()

    resultado = (
        repository
        .custos_manutencao()
    )

    assert resultado == [
        {
            "id": 1,
            "tipo": "Carro",
            "modelo": "Civic",
            "total_manutencoes": 3,
            "custo_total": 650.0,
        }
    ]


def test_clientes_mais_alugam_ordena_e_soma_somente_finalizados(
    banco_orm,
    repository,
):
    with banco_orm.criar_sessao() as sessao:
        sessao.add(
            criar_veiculo(1, "Civic")
        )
        sessao.add_all(
            [
                criar_cliente(1, "lucas", "Lucas"),
                criar_cliente(2, "maria", "Maria"),
            ]
        )
        sessao.flush()
        sessao.add_all(
            [
                criar_aluguel(
                    1, 1, "lucas", "Lucas",
                    1, "Civic", 400,
                ),
                criar_aluguel(
                    2, 1, "lucas", "Lucas",
                    1, "Civic", 500,
                ),
                criar_aluguel(
                    3, 1, "lucas", "Lucas",
                    1, "Civic", 999,
                    status="ativo",
                ),
                criar_aluguel(
                    4, 2, "maria", "Maria",
                    1, "Civic", 700,
                ),
            ]
        )
        sessao.commit()

    resultado = (
        repository
        .clientes_mais_alugam()
    )

    assert resultado[0] == {
        "cliente_id": 1,
        "cliente_nome": "Lucas",
        "cliente_usuario": "lucas",
        "total_alugueis": 3,
        "total_gasto": 900.0,
    }

    assert resultado[1][
        "cliente_usuario"
    ] == "maria"


def test_resumo_financeiro_calcula_resultado_bruto(
    banco_orm,
    repository,
):
    with banco_orm.criar_sessao() as sessao:
        sessao.add(
            criar_veiculo(1, "Civic")
        )
        sessao.add(
            criar_cliente(1, "lucas", "Lucas")
        )
        sessao.flush()
        sessao.add_all(
            [
                criar_aluguel(
                    1, 1, "lucas", "Lucas",
                    1, "Civic", 500,
                ),
                criar_aluguel(
                    2, 1, "lucas", "Lucas",
                    1, "Civic", 1000,
                ),
                criar_manutencao(
                    1,
                    1,
                    400,
                ),
            ]
        )
        sessao.commit()

    resultado = (
        repository
        .resumo_financeiro()
    )

    assert resultado == {
        "receita_alugueis": 1500.0,
        "custos_manutencao": 400.0,
        "resultado_bruto": 1100.0,
    }


def test_resumo_financeiro_sem_movimentacao_retorna_zeros(
    repository,
):
    assert repository.resumo_financeiro() == {
        "receita_alugueis": 0.0,
        "custos_manutencao": 0.0,
        "resultado_bruto": 0.0,
    }


def test_resultado_por_veiculo_nao_duplica_receitas_e_custos(
    banco_orm,
    repository,
):
    with banco_orm.criar_sessao() as sessao:
        sessao.add(
            criar_veiculo(1, "Civic")
        )
        sessao.add(
            criar_cliente(1, "lucas", "Lucas")
        )
        sessao.flush()
        sessao.add_all(
            [
                criar_aluguel(
                    1, 1, "lucas", "Lucas",
                    1, "Civic", 400,
                ),
                criar_aluguel(
                    2, 1, "lucas", "Lucas",
                    1, "Civic", 600,
                ),
                criar_manutencao(
                    1,
                    1,
                    100,
                ),
                criar_manutencao(
                    2,
                    1,
                    200,
                ),
            ]
        )
        sessao.commit()

    resultado = (
        repository
        .resultado_por_veiculo()
    )

    assert resultado == [
        {
            "id": 1,
            "tipo": "Carro",
            "modelo": "Civic",
            "total_alugueis": 2,
            "receita": 1000.0,
            "total_manutencoes": 2,
            "custo_manutencao": 300.0,
            "resultado_bruto": 700.0,
        }
    ]
