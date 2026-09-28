from datetime import date, timedelta

import pytest

from modulos.database import BancoSQLAlchemy
from modulos.models import (
    AluguelModel,
    Base,
    ClienteModel,
    ManutencaoModel,
    VeiculoModel,
)
from modulos.repositories.aluguel_repository import AluguelRepository
from modulos.repositories.cliente_repository import ClienteRepository
from modulos.repositories.manutencao_repository import ManutencaoRepository
from modulos.repositories.veiculo_repository import VeiculoRepository


@pytest.fixture
def banco_sqlalchemy(tmp_path):
    caminho = tmp_path / "consultas_paginadas.db"
    banco = BancoSQLAlchemy(f"sqlite:///{caminho.as_posix()}")
    Base.metadata.create_all(banco.engine)

    try:
        yield banco
    finally:
        banco.fechar()


def seed(banco):
    hoje = date.today()

    with banco.criar_sessao() as sessao:
        clientes = [
            ClienteModel(
                nome="Lucas Silva",
                usuario="lucas",
                email="lucas@email.com",
                senha_hash="",
                ativo=True,
            ),
            ClienteModel(
                nome="Maria Souza",
                usuario="maria",
                email="maria@email.com",
                senha_hash="",
                ativo=True,
            ),
            ClienteModel(
                nome="Pedro Lima",
                usuario="pedro",
                email="pedro@email.com",
                senha_hash="",
                ativo=False,
            ),
        ]
        veiculos = [
            VeiculoModel(
                tipo="carro",
                modelo="Civic",
                ano=2024,
                diaria=180,
                preco_km=1.5,
                quilometragem=10000,
                status="disponivel",
                disponivel=True,
                alugado_por=None,
                ativo=True,
            ),
            VeiculoModel(
                tipo="carro",
                modelo="Corolla",
                ano=2023,
                diaria=170,
                preco_km=1.4,
                quilometragem=15000,
                status="alugado",
                disponivel=False,
                alugado_por="lucas",
                ativo=True,
            ),
            VeiculoModel(
                tipo="moto",
                modelo="CB 500",
                ano=2025,
                diaria=110,
                preco_km=0.8,
                quilometragem=5000,
                status="manutencao",
                disponivel=False,
                alugado_por=None,
                ativo=True,
            ),
            VeiculoModel(
                tipo="carro",
                modelo="Uno",
                ano=2018,
                diaria=90,
                preco_km=1.0,
                quilometragem=80000,
                status="desativado",
                disponivel=False,
                alugado_por=None,
                ativo=False,
            ),
        ]
        sessao.add_all(clientes + veiculos)
        sessao.flush()

        alugueis = [
            AluguelModel(
                cliente_id=clientes[0].id,
                veiculo_id=veiculos[0].id,
                cliente_usuario="lucas",
                cliente_nome="Lucas Silva",
                veiculo_tipo="carro",
                veiculo_modelo="Civic",
                dias=3,
                status="ativo",
                km=0,
                pagamento=None,
                valor=540,
                data_inicio=(hoje - timedelta(days=5)).isoformat(),
                data_prevista=(hoje - timedelta(days=2)).isoformat(),
                data_fim=None,
                dias_atraso=0,
                multa=0,
            ),
            AluguelModel(
                cliente_id=clientes[0].id,
                veiculo_id=veiculos[1].id,
                cliente_usuario="lucas",
                cliente_nome="Lucas Silva",
                veiculo_tipo="carro",
                veiculo_modelo="Corolla",
                dias=2,
                status="finalizado",
                km=100,
                pagamento="PIX",
                valor=440,
                data_inicio=(hoje - timedelta(days=10)).isoformat(),
                data_prevista=(hoje - timedelta(days=8)).isoformat(),
                data_fim=(hoje - timedelta(days=8)).isoformat(),
                dias_atraso=0,
                multa=0,
            ),
            AluguelModel(
                cliente_id=clientes[1].id,
                veiculo_id=veiculos[2].id,
                cliente_usuario="maria",
                cliente_nome="Maria Souza",
                veiculo_tipo="moto",
                veiculo_modelo="CB 500",
                dias=4,
                status="ativo",
                km=0,
                pagamento=None,
                valor=440,
                data_inicio=hoje.isoformat(),
                data_prevista=(hoje + timedelta(days=4)).isoformat(),
                data_fim=None,
                dias_atraso=0,
                multa=0,
            ),
        ]
        manutencoes = [
            ManutencaoModel(
                veiculo_id=veiculos[0].id,
                motivo="Troca de óleo",
                quilometragem=10000,
                custo=0,
                data_inicio=hoje.isoformat(),
                data_fim=None,
                status="ativa",
            ),
            ManutencaoModel(
                veiculo_id=veiculos[2].id,
                motivo="Revisão de freios",
                quilometragem=5000,
                custo=850,
                data_inicio=(hoje - timedelta(days=10)).isoformat(),
                data_fim=(hoje - timedelta(days=8)).isoformat(),
                status="finalizada",
            ),
        ]
        sessao.add_all(alugueis + manutencoes)
        sessao.commit()


def test_consulta_clientes_filtra_ordena_e_pagina(banco_sqlalchemy):
    seed(banco_sqlalchemy)
    repository = ClienteRepository(banco_sqlalchemy)

    pagina = repository.consultar(
        pagina=1,
        por_pagina=2,
        status="todos",
        ordenar="nome",
        direcao="asc",
    )

    assert pagina.total == 3
    assert [item.nome for item in pagina.items] == ["Lucas Silva", "Maria Souza"]
    assert pagina.resumo == {"total": 3, "ativos": 2, "desativados": 1}

    busca = repository.consultar(busca="pedro", status="desativado")
    assert busca.total == 1
    assert busca.items[0].usuario == "pedro"


def test_consulta_veiculos_filtra_e_resume_status(banco_sqlalchemy):
    seed(banco_sqlalchemy)
    repository = VeiculoRepository(banco_sqlalchemy)

    pagina = repository.consultar(
        pagina=1,
        por_pagina=2,
        ordenar="ano",
        direcao="desc",
    )

    assert pagina.total == 4
    assert [item.modelo for item in pagina.items] == ["CB 500", "Civic"]
    assert pagina.resumo == {
        "total": 4,
        "disponiveis": 1,
        "alugados": 1,
        "manutencao": 1,
        "desativados": 1,
    }

    busca = repository.consultar(busca="civic", status="disponivel")
    assert busca.total == 1
    assert busca.items[0].modelo == "Civic"


def test_consulta_alugueis_respeita_escopo_do_cliente(banco_sqlalchemy):
    seed(banco_sqlalchemy)
    repository = AluguelRepository(banco_sqlalchemy)

    pagina = repository.consultar(cliente_id=1, por_pagina=1)

    assert pagina.total == 2
    assert len(pagina.items) == 1
    assert pagina.resumo == {
        "total": 2,
        "ativos": 1,
        "finalizados": 1,
        "atrasados": 1,
    }

    busca = repository.consultar(busca="maria", status="ativo")
    assert busca.total == 1
    assert busca.items[0].cliente_usuario == "maria"


def test_consulta_manutencoes_busca_dados_do_veiculo(banco_sqlalchemy):
    seed(banco_sqlalchemy)
    repository = ManutencaoRepository(banco_sqlalchemy)

    pagina = repository.consultar(busca="civic", status="ativa")

    assert pagina.total == 1
    assert pagina.items[0].motivo == "Troca de óleo"
    assert pagina.resumo == {
        "total": 2,
        "ativas": 1,
        "finalizadas": 1,
        "custo_finalizado": 850.0,
        "atrasadas": 0,
        "custo_estimado_ativo": 0.0,
    }
