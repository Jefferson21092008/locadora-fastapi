import pytest

from modulos.servicos.manutencao_service import (
    ManutencaoService,
)

from modulos.servicos.veiculos_service import (
    VeiculoService,
)

from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)


class DadosFake:
    def __init__(self):
        self.ultimo_id_veiculo = 0

    def inserir_veiculo(
        self,
        veiculo,
    ):
        self.ultimo_id_veiculo += 1
        return self.ultimo_id_veiculo

    @staticmethod
    def atualizar_veiculo(
        veiculo,
    ):
        pass


class VeiculoRepositoryFake:
    def __init__(
        self,
        dados,
        veiculos=None,
    ):
        self.dados = dados
        self.veiculos = (
            veiculos
            if veiculos is not None
            else []
        )

    def buscar_por_id(self, id_veiculo):
        for veiculo in self.veiculos:
            if veiculo.id == id_veiculo:
                return veiculo
        return None

    def buscar(self, termo):
        termo = str(termo).strip()
        if not termo:
            return []
        return [
            v for v in self.veiculos
            if v.ativo and v.corresponde_busca(termo)
        ]

    def listar_colecao(self):
        return list(self.veiculos)

    def listar_disponiveis(self):
        return [v for v in self.veiculos if v.disponivel]

    def listar_ativos(self):
        return [v for v in self.veiculos if v.ativo]

    def listar_desativados(self):
        return [v for v in self.veiculos if not v.ativo]

    def listar_alugados(self):
        return [
            v
            for v in self.veiculos
            if v.status.value == "alugado"
        ]

    def listar_em_manutencao(self):
        return [
            v
            for v in self.veiculos
            if v.status.value == "manutencao"
        ]

    def inserir(self, veiculo):
        novo_id = self.dados.inserir_veiculo(
            veiculo
        )
        self.veiculos.append(
            veiculo
        )
        return novo_id

    def atualizar(self, veiculo):
        return self.dados.atualizar_veiculo(
            veiculo
        )


class ManutencaoRepositoryFake:
    """Repository em memória usado apenas nos testes do Service."""

    def __init__(
        self,
        manutencoes=None,
        falhar_registro=False,
        falhar_finalizacao=False,
    ):
        self.manutencoes = (
            manutencoes
            if manutencoes is not None
            else []
        )
        self.falhar_registro = falhar_registro
        self.falhar_finalizacao = falhar_finalizacao
        self.ultimo_id = max(
            [item.id for item in self.manutencoes],
            default=0,
        )

    def buscar_ativa_por_veiculo(
        self,
        id_veiculo,
    ):
        for manutencao in self.manutencoes:
            if (
                manutencao.veiculo_id == id_veiculo
                and manutencao.ativa
            ):
                return manutencao
        return None

    def listar_por_veiculo(
        self,
        id_veiculo,
    ):
        return [
            manutencao
            for manutencao in self.manutencoes
            if manutencao.veiculo_id == id_veiculo
        ]

    def listar_ativas(self):
        return [
            manutencao
            for manutencao in self.manutencoes
            if manutencao.ativa
        ]

    def registrar(
        self,
        manutencao,
        veiculo,
    ):
        if self.falhar_registro:
            raise RuntimeError(
                "Falha simulada na abertura."
            )

        self.ultimo_id += 1
        self.manutencoes.append(
            manutencao
        )
        return self.ultimo_id

    def registrar_finalizacao(
        self,
        manutencao,
        veiculo,
    ):
        if self.falhar_finalizacao:
            raise RuntimeError(
                "Falha simulada na finalização."
            )

    def listar_colecao(self):
        return list(
            self.manutencoes
        )


def criar_ambiente(
    falhar_finalizacao=False,
):
    dados = DadosFake()
    veiculos = []
    manutencoes = []

    veiculo_service = (
        VeiculoService(
            veiculo_repository=(
                VeiculoRepositoryFake(
                    dados,
                    veiculos,
                )
            ),
        )
    )

    manutencao_service = (
        ManutencaoService(
            veiculo_service=veiculo_service,
            manutencao_repository=(
                ManutencaoRepositoryFake(
                    manutencoes=manutencoes,
                    falhar_finalizacao=(
                        falhar_finalizacao
                    ),
                )
            ),
        )
    )

    carro = (
        veiculo_service.cadastrar(
            tipo="carro",
            modelo="Civic",
            ano=2025,
            diaria=100,
            preco_km=0.50,
        )
    )

    return (
        carro,
        manutencao_service,
    )


def test_abrir_manutencao():
    carro, service = (
        criar_ambiente()
    )

    manutencao = (
        service.abrir(
            carro.id,
            "Troca de óleo",
        )
    )

    assert manutencao.id == 1
    assert manutencao.ativa is True
    assert manutencao.veiculo_id == carro.id
    assert carro.status.value == "manutencao"


def test_manutencao_registra_quilometragem_do_veiculo():
    carro, service = (
        criar_ambiente()
    )

    carro.adicionar_quilometragem(
        12500
    )

    manutencao = (
        service.abrir(
            carro.id,
            "Revisão",
        )
    )

    assert manutencao.quilometragem == 12500


def test_nao_abrir_manutencao_com_motivo_vazio():
    carro, service = (
        criar_ambiente()
    )

    with pytest.raises(
        RegraDeNegocio
    ):
        service.abrir(
            carro.id,
            "",
        )

    assert carro.status.value == "disponivel"


def test_nao_abrir_duas_manutencoes_ativas():
    carro, service = (
        criar_ambiente()
    )

    service.abrir(
        carro.id,
        "Troca de óleo",
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.abrir(
            carro.id,
            "Freios",
        )

    assert (
        erro.value.mensagem
        == (
            "Esse veículo já possui "
            "uma manutenção ativa."
        )
    )

    assert len(
        service.listar_manutencoes()
    ) == 1


def test_finalizar_manutencao():
    carro, service = (
        criar_ambiente()
    )

    service.abrir(
        carro.id,
        "Troca de óleo",
    )

    manutencao = (
        service.finalizar(
            carro.id,
            custo=350,
        )
    )

    assert manutencao.ativa is False
    assert manutencao.custo == 350
    assert carro.status.value == "disponivel"


def test_listar_historico_do_veiculo():
    carro, service = (
        criar_ambiente()
    )

    service.abrir(
        carro.id,
        "Troca de óleo",
    )

    service.finalizar(
        carro.id,
        custo=250,
    )

    service.abrir(
        carro.id,
        "Revisão dos freios",
    )

    historico = (
        service.listar_por_veiculo(
            carro.id
        )
    )

    assert len(historico) == 2


def test_falha_ao_finalizar_restaura_estado():
    carro, service = criar_ambiente(
        falhar_finalizacao=True
    )

    manutencao = (
        service.abrir(
            carro.id,
            "Troca de óleo",
        )
    )

    assert manutencao.ativa is True
    assert carro.status.value == "manutencao"

    estado_manutencao = (
        vars(manutencao).copy()
    )
    estado_veiculo = (
        vars(carro).copy()
    )

    with pytest.raises(
        RuntimeError,
        match="Falha simulada na finalização.",
    ):
        service.finalizar(
            carro.id,
            custo=350,
        )

    assert vars(manutencao) == estado_manutencao
    assert vars(carro) == estado_veiculo
    assert manutencao.ativa is True
    assert carro.status.value == "manutencao"


def test_abrir_manutencao_veiculo_inexistente():
    _, service = (
        criar_ambiente()
    )

    with pytest.raises(
        RecursoNaoEncontrado
    ) as erro:
        service.abrir(
            999,
            "Revisão",
        )

    assert erro.value.mensagem == "Veículo não encontrado."


def test_finalizar_manutencao_veiculo_inexistente():
    _, service = (
        criar_ambiente()
    )

    with pytest.raises(
        RecursoNaoEncontrado
    ) as erro:
        service.finalizar(
            999,
            custo=300,
        )

    assert erro.value.mensagem == "Veículo não encontrado."


def test_finalizar_sem_manutencao_ativa():
    carro, service = (
        criar_ambiente()
    )

    with pytest.raises(
        RecursoNaoEncontrado
    ) as erro:
        service.finalizar(
            carro.id,
            custo=300,
        )

    assert (
        erro.value.mensagem
        == (
            "Esse veículo não possui "
            "manutenção ativa."
        )
    )
