from datetime import date
from types import SimpleNamespace

from modulos.consultas import ResultadoPaginado
from modulos.servicos.notificacao_service import (
    NotificacaoService,
)


class NotificacaoRepositoryFake:
    def __init__(self):
        self.items = []
        self.next_id = 1

    def inserir_se_ausente(self, notificacao):
        existente = next(
            (
                item
                for item in self.items
                if item.chave_deduplicacao
                == notificacao.chave_deduplicacao
            ),
            None,
        )
        if existente:
            return existente, False

        notificacao.id = self.next_id
        self.next_id += 1
        self.items.append(notificacao)
        return notificacao, True

    def atualizar(self, notificacao):
        return notificacao

    def buscar_do_usuario(self, id_notificacao, usuario_id):
        return next(
            (
                item
                for item in self.items
                if item.id == id_notificacao
                and item.usuario_id == usuario_id
            ),
            None,
        )

    def consultar_usuario(self, **kwargs):
        usuario_id = kwargs["usuario_id"]
        items = [
            item
            for item in self.items
            if item.usuario_id == usuario_id
        ]
        return ResultadoPaginado(
            items=items,
            total=len(items),
            resumo={
                "total": len(items),
                "nao_lidas": sum(not item.lida for item in items),
                "lidas": sum(item.lida for item in items),
            },
        )

    def marcar_todas_lidas(self, usuario_id):
        atualizadas = 0
        for item in self.items:
            if item.usuario_id == usuario_id and not item.lida:
                item.marcar_como_lida()
                atualizadas += 1
        return atualizadas


class ClienteRepositoryFake:
    cliente = SimpleNamespace(
        id=5,
        usuario="cliente",
        email="cliente@example.com",
    )

    def buscar_por_usuario_id(self, usuario_id):
        if usuario_id == 2:
            return self.cliente
        return None


class ReservaRepositoryFake:
    def listar_do_cliente(self, cliente_id):
        return [
            SimpleNamespace(
                id=10,
                ativa=True,
                data_inicio="2026-09-29",
                veiculo_modelo="Civic",
            )
        ]


class AluguelRepositoryFake:
    def listar_do_cliente(self, cliente):
        return [
            SimpleNamespace(
                id=20,
                status="ativo",
                data_prevista="2026-09-28",
                veiculo_modelo="Corolla",
            ),
            SimpleNamespace(
                id=21,
                status="finalizado",
                data_prevista="2026-09-20",
                veiculo_modelo="Onix",
            ),
        ]


class ManutencaoRepositoryFake:
    def listar_ativas(self):
        return [
            SimpleNamespace(
                id=30,
                veiculo_id=7,
                data_prevista="2026-09-27",
            )
        ]


class PagamentoServiceFake:
    def obter_resumo(self, id_aluguel):
        return {
            "saldo_pendente": 120.0,
        }


class EmailServiceFake:
    def __init__(self):
        self.config = SimpleNamespace(
            email_configurado=True,
        )
        self.envios = []

    def enviar_notificacao(self, **kwargs):
        self.envios.append(kwargs)


def criar_service():
    repository = NotificacaoRepositoryFake()
    email = EmailServiceFake()
    service = NotificacaoService(
        notificacao_repository=repository,
        usuario_repository=SimpleNamespace(),
        cliente_repository=ClienteRepositoryFake(),
        reserva_repository=ReservaRepositoryFake(),
        aluguel_repository=AluguelRepositoryFake(),
        manutencao_repository=ManutencaoRepositoryFake(),
        pagamento_service=PagamentoServiceFake(),
        email_service=email,
    )
    return service, repository, email


def test_cliente_recebe_lembretes_idempotentes():
    service, repository, email = criar_service()
    usuario = SimpleNamespace(
        id=2,
        role=SimpleNamespace(value="cliente"),
    )

    primeiro = service.processar_usuario(
        usuario,
        date(2026, 9, 28),
    )
    segundo = service.processar_usuario(
        usuario,
        date(2026, 9, 28),
    )

    assert primeiro["criadas"] == 3
    assert primeiro["emails_enviados"] == 3
    assert segundo["criadas"] == 0
    assert len(repository.items) == 3
    assert len(email.envios) == 3


def test_admin_recebe_manutencao_atrasada_sem_email():
    service, repository, email = criar_service()
    usuario = SimpleNamespace(
        id=1,
        role=SimpleNamespace(value="admin"),
    )

    resultado = service.processar_usuario(
        usuario,
        date(2026, 9, 28),
    )

    assert resultado["criadas"] == 1
    assert repository.items[0].tipo == "manutencao_atrasada"
    assert repository.items[0].email_status == "nao_aplicavel"
    assert email.envios == []


def test_service_marca_notificacao_como_lida():
    service, repository, _ = criar_service()
    usuario = SimpleNamespace(
        id=1,
        role=SimpleNamespace(value="admin"),
    )
    service.processar_usuario(
        usuario,
        date(2026, 9, 28),
    )

    notificacao = service.marcar_como_lida(1, 1)

    assert notificacao.lida is True
