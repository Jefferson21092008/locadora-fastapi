from datetime import date, timedelta
import pytest
from modulos.clientes import Cliente
from modulos.servicos.alugueis_service import AluguelService
from modulos.servicos.veiculos_service import VeiculoService

from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)


# ================================================================
# DADOS FALSOS
# ================================================================

class DadosFake:
    """
    Substitui o GerenciadorDados durante os testes.

    Assim os testes não alteram o banco SQLite real.
    """

    def __init__(self):
        self.ultimo_id_veiculo = 0
        self.ultimo_id_aluguel = 0

    def inserir_veiculo(self, veiculo):
        """
        Simula o AUTOINCREMENT do SQLite.
        """
        self.ultimo_id_veiculo += 1
        return self.ultimo_id_veiculo

    def registrar_aluguel(
        self,
        aluguel,
        veiculo,
    ):
        self.ultimo_id_aluguel += 1
        return self.ultimo_id_aluguel

    @staticmethod
    def atualizar_veiculo(veiculo):
        pass

    @staticmethod
    def registrar_devolucao(
        aluguel,
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
            veiculo
            for veiculo in self.veiculos
            if veiculo.ativo and veiculo.corresponde_busca(termo)
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
        return [v for v in self.veiculos if v.status.value == "alugado"]

    def listar_em_manutencao(self):
        return [v for v in self.veiculos if v.status.value == "manutencao"]

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

class AluguelRepositoryFake:
    """Repository em memória usado somente nos testes do Service."""

    def __init__(
        self,
        alugueis=None,
        falhar_registro=False,
        falhar_devolucao=False,
    ):
        self.alugueis = (
            alugueis
            if alugueis is not None
            else []
        )
        self.falhar_registro = falhar_registro
        self.falhar_devolucao = falhar_devolucao
        self.ultimo_id = max(
            [aluguel.id for aluguel in self.alugueis],
            default=0,
        )

    def listar_ativos_cliente(self, cliente):
        return [
            aluguel
            for aluguel in self.alugueis
            if (
                aluguel.ativo
                and aluguel.pertence_ao_cliente(cliente)
            )
        ]

    def listar_do_cliente(self, cliente):
        return [
            aluguel
            for aluguel in self.alugueis
            if aluguel.pertence_ao_cliente(cliente)
        ]

    def buscar_ativo(
        self,
        cliente,
        id_veiculo=None,
    ):
        for aluguel in self.alugueis:
            if not aluguel.ativo:
                continue
            if not aluguel.pertence_ao_cliente(cliente):
                continue
            if (
                id_veiculo is not None
                and aluguel.veiculo_id != id_veiculo
            ):
                continue
            return aluguel
        return None

    def registrar(self, aluguel, veiculo):
        if self.falhar_registro:
            raise RuntimeError(
                "Falha simulada no banco."
            )

        self.ultimo_id += 1
        self.alugueis.append(aluguel)
        return self.ultimo_id

    def registrar_devolucao(self, aluguel, veiculo):
        if self.falhar_devolucao:
            raise RuntimeError(
                "Falha simulada na devolução."
            )

    def listar_colecao(self):
        return list(self.alugueis)

    def listar_ativos(self):
        return [
            aluguel
            for aluguel in self.alugueis
            if aluguel.ativo
        ]

# ================================================================
# AUXILIARES
# ================================================================

def criar_ambiente():
    veiculos = []
    alugueis = []

    dados = DadosFake()

    veiculo_service = VeiculoService(
        veiculo_repository=(
            VeiculoRepositoryFake(
                dados,
                veiculos,
            )
        ),
    )

    aluguel_service = AluguelService(
        veiculo_service=veiculo_service,
        aluguel_repository=(
            AluguelRepositoryFake(
                alugueis
            )
        ),
    )

    cliente, mensagem = Cliente.criar(
        id_cliente=1,
        nome="Lucas Silva",
        usuario="lucas",
        email="lucas@email.com",
    )

    assert cliente is not None
    assert mensagem == ""

    return (
        cliente,
        veiculo_service,
        aluguel_service,
    )

def cadastrar_carro(
    veiculo_service,
):
    carro = (
        veiculo_service.cadastrar(
            tipo="carro",
            modelo="Civic",
            ano=2025,
            diaria=100,
            preco_km=0.50,
        )
    )

    return carro

def cadastrar_bicicleta(
    veiculo_service,
):
    bicicleta = (
        veiculo_service.cadastrar(
            tipo="bicicleta",
            modelo="Caloi",
            ano=2025,
            diaria=30,
            preco_km=0,
        )
    )

    return bicicleta

# ================================================================
# ALUGUEL
# ================================================================

def test_alugar_carro():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    carro = cadastrar_carro(
        veiculo_service
    )

    aluguel = (
        aluguel_service.alugar(
            cliente=cliente,
            id_veiculo=carro.id,
            dias=3,
            anos_habilitacao=5,
        )
    )

    assert aluguel.cliente_id == cliente.id
    assert aluguel.veiculo_id == carro.id
    assert aluguel.dias == 3
    assert aluguel.ativo is True

    assert carro.disponivel is False

    assert len(
        aluguel_service.aluguel_repository
        .alugueis
    ) == 1

def test_nao_alugar_com_dias_invalidos():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    carro = cadastrar_carro(
        veiculo_service
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        aluguel_service.alugar(
            cliente=cliente,
            id_veiculo=carro.id,
            dias=0,
            anos_habilitacao=5,
        )

    assert (
        erro.value.mensagem
        == (
            "A quantidade de dias "
            "deve ser maior que zero."
        )
    )

    assert carro.disponivel is True

    assert len(
        aluguel_service.aluguel_repository
        .alugueis
    ) == 0

def test_nao_alugar_veiculo_inexistente():
    (
        cliente,
        _,
        aluguel_service,
    ) = criar_ambiente()

    with pytest.raises(
        RecursoNaoEncontrado
    ) as erro:
        aluguel_service.alugar(
            cliente=cliente,
            id_veiculo=999,
            dias=3,
            anos_habilitacao=5,
        )

    assert (
        erro.value.mensagem
        == "Veículo não encontrado."
    )

def test_nao_alugar_sem_tempo_de_habilitacao():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    carro = cadastrar_carro(
        veiculo_service
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        aluguel_service.alugar(
            cliente=cliente,
            id_veiculo=carro.id,
            dias=3,
            anos_habilitacao=1,
        )

    assert (
        "habilitação insuficiente"
        in erro.value.mensagem.lower()
    )

    assert carro.disponivel is True

def test_bicicleta_nao_exige_habilitacao():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    bicicleta = cadastrar_bicicleta(
        veiculo_service
    )

    aluguel = (
        aluguel_service.alugar(
            cliente=cliente,
            id_veiculo=bicicleta.id,
            dias=2,
        )
    )
    assert aluguel.ativo is True

    assert bicicleta.disponivel is False

def test_nao_alugar_veiculo_ja_alugado():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    carro = cadastrar_carro(
        veiculo_service
    )

    aluguel_service.alugar(
        cliente=cliente,
        id_veiculo=carro.id,
        dias=3,
        anos_habilitacao=5,
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        aluguel_service.alugar(
            cliente=cliente,
            id_veiculo=carro.id,
            dias=2,
            anos_habilitacao=5,
        )

    assert (
        erro.value.mensagem
        == "Esse veículo está alugado."
    )

def test_falha_ao_registrar_aluguel_libera_veiculo():
    cliente = Cliente(
        id_cliente=1,
        nome="Lucas Silva",
        usuario="lucas",
        email="lucas@email.com",
    )

    veiculos = []
    alugueis = []

    dados = DadosFake()

    veiculo_service = VeiculoService(
        veiculo_repository=(
            VeiculoRepositoryFake(
                dados,
                veiculos,
            )
        ),
    )

    aluguel_service = AluguelService(
        veiculo_service=veiculo_service,
        aluguel_repository=(
            AluguelRepositoryFake(
                alugueis,
                falhar_registro=True,
            )
        ),
    )

    carro = veiculo_service.cadastrar(
        tipo="carro",
        modelo="Civic",
        ano=2025,
        diaria=100,
        preco_km=0.50,
    )

    assert carro.disponivel is True

    with pytest.raises(
        RuntimeError,
        match="Falha simulada no banco.",
    ):
        aluguel_service.alugar(
            cliente=cliente,
            id_veiculo=carro.id,
            dias=3,
            anos_habilitacao=5,
        )

    # O veículo chegou a ser marcado como alugado,
    # mas deve ter sido restaurado após a falha.
    assert carro.disponivel is True
    assert carro.alugado_por is None

    # O aluguel também não pode ter sido
    # adicionado à lista em memória.
    assert len(
        aluguel_service.aluguel_repository
        .alugueis
    ) == 0

# ================================================================
# CONSULTAS
# ================================================================

def test_buscar_aluguel_ativo():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    carro = cadastrar_carro(
        veiculo_service
    )

    aluguel = aluguel_service.alugar(
        cliente=cliente,
        id_veiculo=carro.id,
        dias=3,
        anos_habilitacao=5,
    )

    encontrado = (
        aluguel_service.buscar_ativo(
            cliente,
            carro.id,
        )
    )

    assert encontrado is aluguel

def test_listar_alugueis_ativos_do_cliente():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    carro = cadastrar_carro(
        veiculo_service
    )

    aluguel_service.alugar(
        cliente=cliente,
        id_veiculo=carro.id,
        dias=3,
        anos_habilitacao=5,
    )

    ativos = (
        aluguel_service.listar_ativos_cliente(
            cliente
        )
    )

    assert len(ativos) == 1
    assert ativos[0].veiculo_id == carro.id

# ================================================================
# DEVOLUÇÃO
# ================================================================

def test_devolver_veiculo():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    carro = cadastrar_carro(
        veiculo_service
    )

    aluguel = aluguel_service.alugar(
        cliente=cliente,
        id_veiculo=carro.id,
        dias=2,
        anos_habilitacao=5,
    )

    resultado = (
        aluguel_service.devolver(
            cliente=cliente,
            id_veiculo=carro.id,
            km=100,
            forma_pagamento=4,
        )
    )

    assert aluguel.ativo is False
    assert carro.disponivel is True

    assert aluguel.km == 100

    assert resultado[
        "valor_inicial"
    ] == 250

    assert aluguel.valor == resultado[
        "pagamento"
    ]["valor_final"]

def test_nao_devolver_com_km_negativo():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    carro = cadastrar_carro(
        veiculo_service
    )

    aluguel_service.alugar(
        cliente=cliente,
        id_veiculo=carro.id,
        dias=2,
        anos_habilitacao=5,
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        aluguel_service.devolver(
            cliente=cliente,
            id_veiculo=carro.id,
            km=-10,
            forma_pagamento=4,
        )

    assert (
        erro.value.mensagem
        == (
            "A quilometragem não pode "
            "ser negativa."
        )
    )

    assert carro.disponivel is False

def test_falha_na_devolucao_restaura_estado():
    cliente = Cliente(
        id_cliente=1,
        nome="Lucas Silva",
        usuario="lucas",
        email="lucas@email.com",
    )

    veiculos = []
    alugueis = []

    dados = DadosFake()

    veiculo_service = VeiculoService(
        veiculo_repository=(
            VeiculoRepositoryFake(
                dados,
                veiculos,
            )
        ),
    )

    aluguel_service = AluguelService(
        veiculo_service=veiculo_service,
        aluguel_repository=(
            AluguelRepositoryFake(
                alugueis,
                falhar_devolucao=True,
            )
        ),
    )

    carro = veiculo_service.cadastrar(
        tipo="carro",
        modelo="Civic",
        ano=2025,
        diaria=100,
        preco_km=0.50,
    )

    aluguel = aluguel_service.alugar(
        cliente=cliente,
        id_veiculo=carro.id,
        dias=3,
        anos_habilitacao=5,
    )

    # Estado antes da devolução
    assert aluguel.ativo is True
    assert carro.disponivel is False
    assert carro.alugado_por == "lucas"

    with pytest.raises(
        RuntimeError,
        match="Falha simulada na devolução.",
    ):
        aluguel_service.devolver(
            cliente=cliente,
            id_veiculo=carro.id,
            km=100,
            forma_pagamento=4,
        )

    # A falha deve restaurar o estado anterior.
    assert aluguel.ativo is True

    assert carro.disponivel is False

    assert (
        carro.alugado_por
        == "lucas"
    )

    assert len(
        aluguel_service.aluguel_repository
        .alugueis
    ) == 1

def test_devolucao_adiciona_quilometragem_ao_veiculo():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    carro = cadastrar_carro(
        veiculo_service
    )

    assert carro.quilometragem == 0

    aluguel = aluguel_service.alugar(
        cliente=cliente,
        id_veiculo=carro.id,
        dias=2,
        anos_habilitacao=5,
    )

    resultado = aluguel_service.devolver(
        cliente=cliente,
        id_veiculo=carro.id,
        km=250,
        forma_pagamento=4,
    )
    assert carro.quilometragem == 250

def test_nao_devolver_veiculo_sem_aluguel():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    carro = cadastrar_carro(
        veiculo_service
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        aluguel_service.devolver(
            cliente=cliente,
            id_veiculo=carro.id,
            km=100,
            forma_pagamento=4,
        )

    assert (
        erro.value.mensagem
        == (
            "Esse veículo não pertence "
            "aos seus aluguéis ativos."
        )
    )


def test_pagamento_invalido_na_devolucao():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    carro = cadastrar_carro(
        veiculo_service
    )

    aluguel_service.alugar(
        cliente=cliente,
        id_veiculo=carro.id,
        dias=2,
        anos_habilitacao=5,
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        aluguel_service.devolver(
            cliente=cliente,
            id_veiculo=carro.id,
            km=100,
            forma_pagamento=99,
        )

    assert (
        erro.value.mensagem
        == "Forma de pagamento inválida."
    )

    assert carro.disponivel is False


def test_parcelamento_invalido():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    carro = cadastrar_carro(
        veiculo_service
    )

    aluguel_service.alugar(
        cliente=cliente,
        id_veiculo=carro.id,
        dias=2,
        anos_habilitacao=5,
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        aluguel_service.devolver(
            cliente=cliente,
            id_veiculo=carro.id,
            km=100,
            forma_pagamento=5,
            parcelas=20,
        )

    assert (
        erro.value.mensagem
        == (
            "A quantidade de parcelas "
            "deve estar entre 2 e 12."
        )
    )

    assert carro.disponivel is False

def test_devolucao_com_atraso_aplica_multa():
    (
        cliente,
        veiculo_service,
        aluguel_service,
    ) = criar_ambiente()

    carro = cadastrar_carro(
        veiculo_service
    )

    aluguel = aluguel_service.alugar(
        cliente=cliente,
        id_veiculo=carro.id,
        dias=2,
        anos_habilitacao=5,
    )

    data_referencia = (
        date.fromisoformat(
            aluguel.data_prevista
        )
        + timedelta(days=3)
    )

    resultado = (
        aluguel_service.devolver(
            cliente=cliente,
            id_veiculo=carro.id,
            km=100,
            forma_pagamento=4,
            data_referencia=data_referencia,
        )
    )

    assert resultado[
        "valor_aluguel"
    ] == 250

    assert resultado[
        "dias_atraso"
    ] == 3

    assert resultado[
        "multa"
    ] == 60

    assert resultado[
        "valor_inicial"
    ] == 310

    assert aluguel.dias_atraso == 3
    assert aluguel.multa == 60