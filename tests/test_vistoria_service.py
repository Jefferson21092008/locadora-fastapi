from types import SimpleNamespace

import pytest

from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)
from modulos.servicos.vistoria_service import (
    VistoriaService,
)
from modulos.vistorias import (
    CaucaoAluguel,
)


class AluguelRepositoryFake:
    def __init__(self):
        self.alugueis = {
            1: SimpleNamespace(
                id=1,
                cliente_id=10,
                cliente_usuario="lucas",
                cliente_nome="Lucas",
                veiculo_id=20,
                veiculo_tipo="carro",
                veiculo_modelo="Civic",
                status="ativo",
                data_inicio="2026-09-28",
                data_prevista="2026-10-01",
                data_fim=None,
            ),
            2: SimpleNamespace(
                id=2,
                cliente_id=11,
                cliente_usuario="maria",
                cliente_nome="Maria",
                veiculo_id=21,
                veiculo_tipo="carro",
                veiculo_modelo="Corolla",
                status="finalizado",
                data_inicio="2026-09-20",
                data_prevista="2026-09-23",
                data_fim="2026-09-23",
            ),
        }

    def buscar_por_id(
        self,
        id_aluguel,
    ):
        return self.alugueis.get(
            id_aluguel
        )


class VistoriaRepositoryFake:
    def __init__(self):
        self.inspecoes = []
        self.danos = []
        self.multas = []
        self.caucoes = {}
        self.proximo_id = 1

    def _id(self):
        valor = self.proximo_id
        self.proximo_id += 1
        return valor

    def buscar_inspecao(
        self,
        aluguel_id,
        tipo,
    ):
        return next(
            (
                item
                for item in self.inspecoes
                if item.aluguel_id == aluguel_id
                and item.tipo == tipo
            ),
            None,
        )

    def listar_inspecoes(
        self,
        aluguel_id,
    ):
        return [
            item
            for item in self.inspecoes
            if item.aluguel_id == aluguel_id
        ]

    def registrar_inspecao(
        self,
        inspecao,
    ):
        inspecao.id = self._id()
        self.inspecoes.append(
            inspecao
        )
        return inspecao.id

    def listar_danos(
        self,
        aluguel_id,
    ):
        return [
            item
            for item in self.danos
            if item.aluguel_id == aluguel_id
        ]

    def registrar_dano(
        self,
        dano,
    ):
        dano.id = self._id()
        self.danos.append(
            dano
        )
        return dano.id

    def buscar_dano(
        self,
        id_dano,
    ):
        return next(
            (
                item
                for item in self.danos
                if item.id == id_dano
            ),
            None,
        )

    def atualizar_dano(
        self,
        dano,
    ):
        return None

    def listar_multas(
        self,
        aluguel_id,
    ):
        return [
            item
            for item in self.multas
            if item.aluguel_id == aluguel_id
        ]

    def registrar_multa(
        self,
        multa,
    ):
        multa.id = self._id()
        self.multas.append(
            multa
        )
        return multa.id

    def buscar_multa(
        self,
        id_multa,
    ):
        return next(
            (
                item
                for item in self.multas
                if item.id == id_multa
            ),
            None,
        )

    def atualizar_multa(
        self,
        multa,
    ):
        return None

    def buscar_caucao(
        self,
        aluguel_id,
    ):
        return self.caucoes.get(
            aluguel_id
        )

    def salvar_caucao(
        self,
        caucao,
    ):
        if not caucao.id:
            caucao.id = self._id()

        self.caucoes[
            caucao.aluguel_id
        ] = caucao

        return caucao


@pytest.fixture
def ambiente():
    repository = (
        VistoriaRepositoryFake()
    )
    service = VistoriaService(
        aluguel_repository=(
            AluguelRepositoryFake()
        ),
        vistoria_repository=(
            repository
        ),
    )
    return service, repository


def test_registra_inspecoes_e_calcula_combustivel_faltante(
    ambiente,
):
    service, _ = ambiente

    service.registrar_inspecao(
        id_aluguel=1,
        tipo="retirada",
        quilometragem=10000,
        combustivel_percentual=80,
    )
    service.registrar_inspecao(
        id_aluguel=1,
        tipo="devolucao",
        quilometragem=10300,
        combustivel_percentual=55,
    )

    resumo = service.obter_resumo(
        1
    )

    assert resumo["indicadores"][
        "combustivel_retirada"
    ] == 80
    assert resumo["indicadores"][
        "combustivel_devolucao"
    ] == 55
    assert resumo["indicadores"][
        "combustivel_faltante"
    ] == 25


def test_rejeita_inspecao_duplicada(
    ambiente,
):
    service, _ = ambiente

    service.registrar_inspecao(
        id_aluguel=1,
        tipo="retirada",
        quilometragem=10000,
        combustivel_percentual=80,
    )

    with pytest.raises(
        RegraDeNegocio,
        match="Já existe",
    ):
        service.registrar_inspecao(
            id_aluguel=1,
            tipo="retirada",
            quilometragem=10010,
            combustivel_percentual=70,
        )


def test_rejeita_quilometragem_de_devolucao_menor(
    ambiente,
):
    service, _ = ambiente

    service.registrar_inspecao(
        id_aluguel=1,
        tipo="retirada",
        quilometragem=10000,
        combustivel_percentual=80,
    )

    with pytest.raises(
        RegraDeNegocio,
        match="quilometragem",
    ):
        service.registrar_inspecao(
            id_aluguel=1,
            tipo="devolucao",
            quilometragem=9999,
            combustivel_percentual=80,
        )


def test_rejeita_retirada_em_aluguel_finalizado(
    ambiente,
):
    service, _ = ambiente

    with pytest.raises(
        RegraDeNegocio,
        match="aluguel ativo",
    ):
        service.registrar_inspecao(
            id_aluguel=2,
            tipo="retirada",
            quilometragem=5000,
            combustivel_percentual=100,
        )


def test_resumo_soma_apenas_ocorrencias_ativas(
    ambiente,
):
    service, repository = ambiente

    dano = service.registrar_dano(
        1,
        "Risco no para-choque",
        300,
    )
    service.registrar_dano(
        1,
        "Retrovisor quebrado",
        500,
    )
    multa = service.registrar_multa(
        1,
        "Excesso de velocidade",
        195,
        "2026-09-28",
    )
    service.registrar_multa(
        1,
        "Estacionamento irregular",
        130,
        "2026-09-28",
    )

    service.cancelar_dano(
        dano.id
    )
    service.cancelar_multa(
        multa.id
    )

    resumo = service.obter_resumo(
        1
    )

    assert resumo["indicadores"][
        "danos_ativos_total"
    ] == 500
    assert resumo["indicadores"][
        "multas_ativas_total"
    ] == 130
    assert resumo["indicadores"][
        "pendencias_estimadas_total"
    ] == 630
    assert len(repository.danos) == 2


def test_caucao_pode_ser_atualizada_parcialmente(
    ambiente,
):
    service, _ = ambiente

    primeira = service.definir_caucao(
        id_aluguel=1,
        valor=1000,
    )
    atualizada = service.definir_caucao(
        id_aluguel=1,
        valor=1000,
        valor_liberado=400,
        observacoes="Liberação parcial.",
    )

    assert atualizada.id == primeira.id
    assert atualizada.status == "parcial"
    assert atualizada.valor_retido == 600


def test_aluguel_inexistente_retorna_404_de_dominio(
    ambiente,
):
    service, _ = ambiente

    with pytest.raises(
        RecursoNaoEncontrado,
        match="Aluguel",
    ):
        service.obter_resumo(
            999
        )


def test_caucao_rejeita_valor_liberado_acima_do_total(
    ambiente,
):
    service, repository = ambiente

    repository.caucoes[1] = (
        CaucaoAluguel(
            id_caucao=7,
            aluguel_id=1,
            valor=500,
        )
    )

    with pytest.raises(
        RegraDeNegocio,
        match="superar",
    ):
        service.definir_caucao(
            id_aluguel=1,
            valor=500,
            valor_liberado=700,
        )
