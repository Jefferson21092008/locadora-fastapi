import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from threading import Barrier

import pytest

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.engine import (
    make_url,
)
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
)

from modulos.alugueis import Aluguel
from modulos.container import (
    Container,
)
from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.excecoes import ConflitoConcorrencia
from modulos.eventos import EventoAplicacao
from modulos.outbox import operacao_com_outbox, persistir_eventos_outbox
from modulos.models import (
    AluguelModel,
    ClienteModel,
    VeiculoModel,
)
from modulos.pagamentos import PagamentoFinanceiro
from modulos.repositories.aluguel_repository import AluguelRepository
from modulos.repositories.pagamento_repository import PagamentoRepository
from modulos.repositories.outbox_repository import OutboxRepository
from modulos.repositories.reserva_repository import ReservaRepository
from modulos.reservas import Reserva
from modulos.usuarios import (
    Role,
)
from modulos.veiculos import Carro


load_dotenv()


pytestmark = pytest.mark.postgresql


TABELAS_ESPERADAS = {
    "alembic_version",
    "audit_logs",
    "alugueis",
    "clientes",
    "manutencoes",
    "reservas",
    "inspecoes",
    "danos",
    "multas_transito",
    "caucoes",
    "pagamentos_financeiros",
    "notificacoes",
    "tarefas_background",
    "eventos_outbox",
    "sessoes",
    "tokens_recuperacao_senha",
    "usuarios",
    "veiculos",
}


def obter_url_postgresql_teste():
    database_url = os.getenv(
        "LOCADORA_TEST_DATABASE_URL"
    )

    if not database_url:
        pytest.skip(
            "LOCADORA_TEST_DATABASE_URL não foi configurada."
        )

    url = make_url(
        database_url
    )

    if (
        url.get_backend_name()
        != "postgresql"
    ):
        pytest.fail(
            "LOCADORA_TEST_DATABASE_URL deve apontar "
            "para PostgreSQL."
        )

    if url.database != "locadora_test":
        pytest.fail(
            "Por segurança, os testes destrutivos aceitam "
            "somente o banco locadora_test."
        )

    if url.username != "locadora_app":
        pytest.fail(
            "Os testes devem usar o usuário limitado "
            "locadora_app."
        )

    return database_url


def recriar_schema_public(database_url):
    engine = create_engine(
        database_url
    )

    try:
        try:
            with engine.begin() as conexao:
                banco_atual = conexao.scalar(
                    text(
                        "SELECT current_database()"
                    )
                )
                usuario_atual = conexao.scalar(
                    text(
                        "SELECT current_user"
                    )
                )

                if (
                    banco_atual
                    != "locadora_test"
                    or usuario_atual
                    != "locadora_app"
                ):
                    pytest.fail(
                        "A conexão real não corresponde ao banco "
                        "locadora_test e ao usuário locadora_app.",
                        pytrace=False,
                    )

                conexao.exec_driver_sql(
                    "DROP SCHEMA IF EXISTS public CASCADE"
                )
                conexao.exec_driver_sql(
                    "CREATE SCHEMA public"
                )

        except OperationalError:
            pytest.fail(
                "Não foi possível conectar ao PostgreSQL. "
                "Confira o serviço, o usuário, a senha e a URL "
                "de LOCADORA_TEST_DATABASE_URL.",
                pytrace=False,
            )

    finally:
        engine.dispose()


@pytest.fixture
def banco_postgresql():
    database_url = (
        obter_url_postgresql_teste()
    )
    recriar_schema_public(
        database_url
    )

    banco = BancoSQLAlchemy(
        database_url
    )

    try:
        banco.aplicar_migrations()
        yield banco

    finally:
        banco.fechar()
        recriar_schema_public(
            database_url
        )


def test_postgresql_conecta_com_usuario_limitado(
    banco_postgresql,
):
    assert (
        banco_postgresql.testar_conexao()
        is True
    )

    with banco_postgresql.engine.connect() as conexao:
        identidade = conexao.execute(
            text(
                "SELECT current_user, current_database()"
            )
        ).one()

    assert tuple(identidade) == (
        "locadora_app",
        "locadora_test",
    )


def test_alembic_cria_schema_postgresql_completo(
    banco_postgresql,
):
    inspetor = inspect(
        banco_postgresql.engine
    )

    assert set(
        inspetor.get_table_names()
    ) == TABELAS_ESPERADAS

    with banco_postgresql.engine.connect() as conexao:
        revisao = conexao.scalar(
            text(
                "SELECT version_num "
                "FROM alembic_version"
            )
        )

    assert revisao == "20261006_0011"

    fks_clientes = (
        inspetor.get_foreign_keys(
            "clientes"
        )
    )

    assert any(
        fk["referred_table"]
        == "usuarios"
        for fk in fks_clientes
    )

    colunas_usuarios = {
        coluna["name"]: coluna
        for coluna in inspetor.get_columns(
            "usuarios"
        )
    }

    assert isinstance(
        colunas_usuarios["ativo"]["type"],
        Boolean,
    )


def test_indice_permite_apenas_uma_manutencao_ativa(
    banco_postgresql,
):
    with banco_postgresql.engine.begin() as conexao:
        veiculo_id = conexao.scalar(
            text(
                """
                INSERT INTO veiculos (
                    tipo, modelo, ano, diaria, preco_km,
                    quilometragem, status, disponivel,
                    alugado_por, ativo
                ) VALUES (
                    'Carro', 'Teste PostgreSQL', 2026,
                    150, 1, 0, 'manutencao', FALSE,
                    NULL, TRUE
                )
                RETURNING id
                """
            )
        )

        conexao.execute(
            text(
                """
                INSERT INTO manutencoes (
                    veiculo_id, motivo, quilometragem,
                    custo, data_inicio, data_fim, status
                ) VALUES (
                    :veiculo_id, 'Revisão anterior', 0,
                    100, '2026-09-01', '2026-09-02',
                    'finalizada'
                )
                """
            ),
            {
                "veiculo_id": veiculo_id,
            },
        )

        conexao.execute(
            text(
                """
                INSERT INTO manutencoes (
                    veiculo_id, motivo, quilometragem,
                    custo, data_inicio, data_fim, status
                ) VALUES (
                    :veiculo_id, 'Revisão atual', 0,
                    0, '2026-09-05', NULL, 'ativa'
                )
                """
            ),
            {
                "veiculo_id": veiculo_id,
            },
        )

    with pytest.raises(
        IntegrityError
    ):
        with banco_postgresql.engine.begin() as conexao:
            conexao.execute(
                text(
                    """
                    INSERT INTO manutencoes (
                        veiculo_id, motivo, quilometragem,
                        custo, data_inicio, data_fim, status
                    ) VALUES (
                        :veiculo_id, 'Duplicada', 0,
                        0, '2026-09-05', NULL, 'ativa'
                    )
                    """
                ),
                {
                    "veiculo_id": veiculo_id,
                },
            )


class ConfiguracaoPostgreSQLTeste:
    admin_usuario = "admin_postgresql"
    admin_senha = "SenhaAdmin123"
    jwt_secret = "segredo-postgresql-de-teste"
    email_configurado = False

    def __init__(
        self,
        database_url,
    ):
        self.database_url = database_url


def test_container_e_repository_funcionam_no_postgresql(
    banco_postgresql,
):
    config = ConfiguracaoPostgreSQLTeste(
        banco_postgresql.database_url
    )
    container = Container(
        config=config,
        banco_sqlalchemy=banco_postgresql,
    )

    administrador = (
        container.usuario_repository
        .buscar_por_usuario(
            "ADMIN_POSTGRESQL"
        )
    )

    assert administrador is not None
    assert administrador.role == Role.ADMIN


def _semear_cliente_e_veiculo(
    banco,
    *,
    cliente_id=1,
    veiculo_id=10,
):
    with banco.criar_sessao() as sessao:
        sessao.add(
            ClienteModel(
                id=cliente_id,
                nome="Cliente Concorrência",
                usuario=f"concorrencia-{cliente_id}",
                email=f"concorrencia-{cliente_id}@example.com",
                senha_hash="",
                ativo=True,
                usuario_id=None,
            )
        )
        sessao.add(
            VeiculoModel(
                id=veiculo_id,
                tipo="Carro",
                modelo="Civic Concorrência",
                ano=date.today().year,
                diaria=150,
                preco_km=1.5,
                quilometragem=1000,
                status="disponivel",
                disponivel=True,
                alugado_por=None,
                ativo=True,
            )
        )
        sessao.commit()


def test_indice_permite_apenas_um_aluguel_ativo_por_veiculo(
    banco_postgresql,
):
    _semear_cliente_e_veiculo(
        banco_postgresql
    )

    def novo_aluguel():
        return AluguelModel(
            cliente_id=1,
            veiculo_id=10,
            cliente_usuario="concorrencia-1",
            cliente_nome="Cliente Concorrência",
            veiculo_tipo="Carro",
            veiculo_modelo="Civic Concorrência",
            dias=2,
            status="ativo",
            km=0,
            pagamento=None,
            valor=0,
            data_inicio=date.today().isoformat(),
            data_prevista=(
                date.today()
                + timedelta(days=2)
            ).isoformat(),
            data_fim=None,
            dias_atraso=0,
            multa=0,
        )

    with banco_postgresql.criar_sessao() as sessao:
        sessao.add(novo_aluguel())
        sessao.commit()

    with pytest.raises(IntegrityError):
        with banco_postgresql.criar_sessao() as sessao:
            sessao.add(novo_aluguel())
            sessao.commit()


def test_reservas_sobrepostas_concorrentes_sao_serializadas(
    banco_postgresql,
):
    _semear_cliente_e_veiculo(
        banco_postgresql
    )
    repository = ReservaRepository(
        banco_postgresql
    )
    inicio = date.today() + timedelta(days=20)
    fim = inicio + timedelta(days=4)
    barreira = Barrier(2)

    def tentar(indice):
        reserva = Reserva(
            id_reserva=0,
            cliente_id=1,
            cliente_usuario="concorrencia-1",
            cliente_nome="Cliente Concorrência",
            veiculo_id=10,
            veiculo_tipo="Carro",
            veiculo_modelo="Civic Concorrência",
            data_inicio=(
                inicio + timedelta(days=indice)
            ).isoformat(),
            data_fim=(
                fim + timedelta(days=indice)
            ).isoformat(),
        )
        barreira.wait()
        try:
            repository.registrar(reserva)
            return "ok"
        except ConflitoConcorrencia:
            return "conflito"

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(
            executor.map(tentar, [0, 1])
        )

    assert sorted(resultados) == [
        "conflito",
        "ok",
    ]
    assert len(repository.listar_colecao()) == 1


def test_alugueis_concorrentes_nao_duplicam_veiculo(
    banco_postgresql,
):
    _semear_cliente_e_veiculo(
        banco_postgresql
    )
    repository = AluguelRepository(
        banco_postgresql
    )
    barreira = Barrier(2)

    def tentar(indice):
        veiculo = Carro(
            id_veiculo=10,
            modelo="Civic Concorrência",
            ano=date.today().year,
            diaria=150,
            preco_km=1.5,
            quilometragem=1000,
            status="disponivel",
        )
        assert veiculo.alugar(
            "concorrencia-1"
        ) is True
        aluguel = Aluguel(
            id_aluguel=0,
            cliente_id=1,
            cliente_usuario="concorrencia-1",
            cliente_nome="Cliente Concorrência",
            veiculo_id=10,
            veiculo_tipo="Carro",
            veiculo_modelo="Civic Concorrência",
            dias=2 + indice,
        )
        barreira.wait()
        try:
            repository.registrar(
                aluguel,
                veiculo,
            )
            return "ok"
        except ConflitoConcorrencia:
            return "conflito"

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(
            executor.map(tentar, [0, 1])
        )

    assert sorted(resultados) == [
        "conflito",
        "ok",
    ]
    assert len(repository.listar_ativos()) == 1


def test_pagamentos_concorrentes_nao_ultrapassam_limite(
    banco_postgresql,
):
    _semear_cliente_e_veiculo(
        banco_postgresql
    )
    with banco_postgresql.criar_sessao() as sessao:
        aluguel = AluguelModel(
            cliente_id=1,
            veiculo_id=10,
            cliente_usuario="concorrencia-1",
            cliente_nome="Cliente Concorrência",
            veiculo_tipo="Carro",
            veiculo_modelo="Civic Concorrência",
            dias=2,
            status="finalizado",
            km=50,
            pagamento="Pix",
            valor=300,
            data_inicio=date.today().isoformat(),
            data_prevista=(
                date.today()
                + timedelta(days=2)
            ).isoformat(),
            data_fim=date.today().isoformat(),
            dias_atraso=0,
            multa=0,
        )
        sessao.add(aluguel)
        sessao.commit()
        aluguel_id = aluguel.id

    repository = PagamentoRepository(
        banco_postgresql
    )
    barreira = Barrier(2)

    def tentar(indice):
        pagamento = PagamentoFinanceiro(
            id_pagamento=0,
            aluguel_id=aluguel_id,
            valor=70,
            forma="pix",
            observacoes=f"concorrente-{indice}",
        )
        barreira.wait()
        try:
            repository.registrar(
                pagamento,
                limite_adicional=100,
            )
            return "ok"
        except ConflitoConcorrencia:
            return "conflito"

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(
            executor.map(tentar, [0, 1])
        )

    assert sorted(resultados) == [
        "conflito",
        "ok",
    ]
    confirmados = [
        pagamento
        for pagamento in repository.listar_por_aluguel(
            aluguel_id
        )
        if pagamento.confirmado
    ]
    assert len(confirmados) == 1
    assert confirmados[0].valor == 70


def test_outbox_concorrente_nao_reserva_mesmo_evento_duas_vezes(
    banco_postgresql,
):
    evento = EventoAplicacao(nome="aluguel.finalizado")

    with operacao_com_outbox(None, evento) as lote:
        with banco_postgresql.criar_sessao() as sessao:
            persistir_eventos_outbox(sessao)
            sessao.commit()
        lote.materializar()

    repository = OutboxRepository(banco_postgresql)
    barreira = Barrier(2)

    def reservar(_indice):
        barreira.wait()
        mensagem = repository.reservar_proxima()
        return (
            mensagem.evento.id_evento
            if mensagem is not None
            else None
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(reservar, [0, 1]))

    assert resultados.count(evento.id_evento) == 1
    assert resultados.count(None) == 1
