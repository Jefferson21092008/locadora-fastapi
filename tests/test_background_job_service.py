from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from modulos.database import BancoSQLAlchemy
from modulos.models import Base
from modulos.repositories.background_job_repository import (
    BackgroundJobRepository,
)
from modulos.servicos.background_job_service import (
    BackgroundJobService,
)


class UsuarioRepositoryFake:
    def __init__(self):
        self.usuarios = [
            SimpleNamespace(id=1, ativo=True),
            SimpleNamespace(id=2, ativo=True),
            SimpleNamespace(id=3, ativo=False),
        ]

    def listar(self):
        return list(self.usuarios)

    def buscar_por_id(self, id_usuario):
        return next(
            (
                usuario
                for usuario in self.usuarios
                if usuario.id == id_usuario
            ),
            None,
        )


class NotificacaoServiceFake:
    def __init__(self):
        self.chamadas = []
        self.falhar = False

    def processar_usuario(self, usuario, data_referencia=None):
        self.chamadas.append((usuario.id, data_referencia))
        if self.falhar:
            raise RuntimeError("falha temporária")
        return {
            "criadas": 1,
            "emails_enviados": 0,
            "emails_falharam": 0,
        }


@pytest.fixture
def ambiente(tmp_path):
    banco = BancoSQLAlchemy(
        f"sqlite:///{(tmp_path / 'jobs_service.db').as_posix()}"
    )
    Base.metadata.create_all(banco.engine)
    repository = BackgroundJobRepository(banco)
    usuarios = UsuarioRepositoryFake()
    notificacoes = NotificacaoServiceFake()
    service = BackgroundJobService(
        background_job_repository=repository,
        usuario_repository=usuarios,
        notificacao_service=notificacoes,
        retry_base_segundos=60,
    )

    try:
        yield repository, usuarios, notificacoes, service
    finally:
        banco.fechar()


def test_service_agenda_um_job_por_usuario_ativo_e_deduplica(ambiente):
    repository, _, _, service = ambiente

    primeiro = service.agendar_notificacoes_do_dia(
        date(2026, 9, 30)
    )
    segundo = service.agendar_notificacoes_do_dia(
        date(2026, 9, 30)
    )

    assert primeiro == {"enfileiradas": 2, "existentes": 0}
    assert segundo == {"enfileiradas": 0, "existentes": 2}
    assert len(repository.listar()) == 2


def test_service_executa_jobs_reutilizando_notificacao_service(ambiente):
    _, _, notificacoes, service = ambiente
    agora = datetime(2026, 9, 30, 10, tzinfo=timezone.utc)

    service.agendar_notificacoes_do_dia(
        date(2026, 9, 30),
        agora=agora,
    )
    resultado = service.executar_lote(limite=10, agora=agora)

    assert resultado["executadas"] == 2
    assert resultado["concluidas"] == 2
    assert notificacoes.chamadas == [
        (1, date(2026, 9, 30)),
        (2, date(2026, 9, 30)),
    ]


def test_service_reagenda_com_backoff_e_falha_no_limite(ambiente):
    repository, usuarios, notificacoes, service = ambiente
    usuarios.usuarios = [SimpleNamespace(id=1, ativo=True)]
    notificacoes.falhar = True
    agora = datetime(2026, 9, 30, 10, tzinfo=timezone.utc)

    service.agendar_notificacoes_do_dia(
        date(2026, 9, 30),
        agora=agora,
    )

    primeira = service.executar_proxima(agora=agora)
    assert primeira["status"] == "reagendada"

    tarefa = repository.listar()[0]
    proxima = datetime.fromisoformat(tarefa.disponivel_em)
    assert proxima == agora + timedelta(seconds=60)

    segunda = service.executar_proxima(agora=proxima)
    assert segunda["status"] == "reagendada"

    tarefa = repository.listar()[0]
    terceira_data = datetime.fromisoformat(tarefa.disponivel_em)
    terceira = service.executar_proxima(agora=terceira_data)

    assert terceira["status"] == "falhou"
    assert repository.listar()[0].status == "falhou"
