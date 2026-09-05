import pytest

from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)

from modulos.servicos.veiculos_service import (
    VeiculoService,
)

from modulos.veiculos import (
    Carro,
)


class VeiculoRepositoryFake:
    """Repository em memória usado somente nos testes do Service."""

    def __init__(self):
        self.veiculos = []
        self.proximo_id = 1

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
            if (
                veiculo.ativo
                and veiculo.corresponde_busca(termo)
            )
        ]

    def listar_colecao(self):
        return list(self.veiculos)

    def listar_disponiveis(self):
        return [
            veiculo
            for veiculo in self.veiculos
            if veiculo.disponivel
        ]

    def listar_ativos(self):
        return [
            veiculo
            for veiculo in self.veiculos
            if veiculo.ativo
        ]

    def listar_desativados(self):
        return [
            veiculo
            for veiculo in self.veiculos
            if not veiculo.ativo
        ]

    def listar_alugados(self):
        return [
            veiculo
            for veiculo in self.veiculos
            if veiculo.status.value == "alugado"
        ]

    def listar_em_manutencao(self):
        return [
            veiculo
            for veiculo in self.veiculos
            if veiculo.status.value == "manutencao"
        ]

    def inserir(self, veiculo):
        novo_id = self.proximo_id
        self.proximo_id += 1
        self.veiculos.append(veiculo)
        return novo_id

    def atualizar(self, veiculo):
        return None


def criar_service():
    return VeiculoService(
        veiculo_repository=(
            VeiculoRepositoryFake()
        ),
    )


# ================================================================
# CADASTRO
# ================================================================


def test_cadastrar_carro():
    service = criar_service()

    resultado = service.cadastrar(
        tipo="carro",
        modelo="Civic",
        ano=2025,
        diaria=100,
        preco_km=0.50,
    )

    assert isinstance(
        resultado,
        Carro,
    )

    assert resultado.id == 1

    assert (
        resultado.modelo
        == "Civic"
    )

    assert resultado.ano == 2025
    assert resultado.diaria == 100

    assert (
        resultado.preco_km
        == 0.50
    )

    assert (
        len(
            service
            .veiculo_repository
            .veiculos
        )
        == 1
    )


def test_cadastrar_tipo_invalido():
    service = criar_service()

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.cadastrar(
            tipo="avião",
            modelo="Boeing",
            ano=2025,
            diaria=1000,
            preco_km=10,
        )

    assert (
        erro.value.mensagem
        == "Tipo de veículo inválido."
    )

    assert (
        len(
            service
            .veiculo_repository
            .veiculos
        )
        == 0
    )


# ================================================================
# BUSCA
# ================================================================


def test_buscar_veiculo_por_id():
    service = criar_service()

    carro = service.cadastrar(
        tipo="carro",
        modelo="Corolla",
        ano=2024,
        diaria=150,
        preco_km=0.75,
    )

    encontrado = (
        service.buscar_por_id(
            carro.id
        )
    )

    assert encontrado is carro


def test_buscar_id_inexistente():
    service = criar_service()

    resultado = (
        service.buscar_por_id(
            999
        )
    )

    assert resultado is None


def test_buscar_por_modelo():
    service = criar_service()

    service.cadastrar(
        "carro",
        "Honda Civic",
        2025,
        120,
        0.60,
    )

    service.cadastrar(
        "moto",
        "Honda CG",
        2024,
        70,
        0.30,
    )

    encontrados = (
        service.buscar(
            "Civic"
        )
    )

    assert (
        len(encontrados)
        == 1
    )

    assert (
        encontrados[0].modelo
        == "Honda Civic"
    )


def test_buscar_por_tipo():
    service = criar_service()

    service.cadastrar(
        "carro",
        "Civic",
        2025,
        120,
        0.60,
    )

    service.cadastrar(
        "moto",
        "CG 160",
        2024,
        70,
        0.30,
    )

    encontrados = (
        service.buscar(
            "moto"
        )
    )

    assert (
        len(encontrados)
        == 1
    )

    assert (
        encontrados[0].tipo
        == "Moto"
    )


# ================================================================
# EDIÇÃO
# ================================================================


def test_editar_modelo():
    service = criar_service()

    carro = service.cadastrar(
        "carro",
        "Civic",
        2025,
        100,
        0.50,
    )

    resultado = service.editar(
        carro.id,
        modelo="Civic Touring",
    )

    assert (
        resultado.modelo
        == "Civic Touring"
    )


def test_editar_veiculo_inexistente():
    service = criar_service()

    with pytest.raises(
        RecursoNaoEncontrado
    ) as erro:
        service.editar(
            999,
            modelo="Teste",
        )

    assert (
        erro.value.mensagem
        == "Veículo não encontrado."
    )


# ================================================================
# DESATIVAÇÃO
# ================================================================


def test_desativar_veiculo():
    service = criar_service()

    carro = service.cadastrar(
        "carro",
        "Civic",
        2025,
        100,
        0.50,
    )

    resultado = (
        service.desativar(
            carro.id
        )
    )

    assert (
        resultado.ativo
        is False
    )


def test_reativar_veiculo():
    service = criar_service()

    carro = service.cadastrar(
        "carro",
        "Civic",
        2025,
        100,
        0.50,
    )

    service.desativar(
        carro.id
    )

    resultado = (
        service.reativar(
            carro.id
        )
    )

    assert (
        resultado.ativo
        is True
    )


# ================================================================
# DISPONIBILIDADE
# ================================================================


def test_listar_disponiveis():
    service = criar_service()

    carro1 = service.cadastrar(
        "carro",
        "Civic",
        2025,
        100,
        0.50,
    )

    carro2 = service.cadastrar(
        "carro",
        "Corolla",
        2024,
        120,
        0.60,
    )

    carro2.alugar(
        "lucas"
    )

    disponiveis = (
        service.listar_disponiveis()
    )

    assert carro1 in disponiveis
    assert carro2 not in disponiveis

    assert (
        len(disponiveis)
        == 1
    )


def test_veiculo_desativado_nao_aparece_como_disponivel():
    service = criar_service()

    carro = service.cadastrar(
        "carro",
        "Civic",
        2025,
        100,
        0.50,
    )

    service.desativar(
        carro.id
    )

    disponiveis = (
        service.listar_disponiveis()
    )

    assert carro not in disponiveis


# ================================================================
# VALIDAÇÃO DE ANO
# ================================================================


def test_nao_cadastrar_veiculo_com_ano_muito_futuro():
    service = criar_service()

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.cadastrar(
            tipo="carro",
            modelo=(
                "Carro do Futuro"
            ),
            ano=9999,
            diaria=100,
            preco_km=0.50,
        )

    assert (
        erro.value.mensagem
        == "Ano do veículo inválido."
    )


# ================================================================
# QUILOMETRAGEM
# ================================================================


def test_adicionar_quilometragem_ao_veiculo():
    service = criar_service()

    carro = service.cadastrar(
        tipo="carro",
        modelo="Civic",
        ano=2025,
        diaria=100,
        preco_km=0.50,
    )

    assert (
        carro.quilometragem
        == 0
    )

    resultado = (
        carro.adicionar_quilometragem(
            150
        )
    )

    assert resultado is True

    assert (
        carro.quilometragem
        == 150
    )


def test_nao_adicionar_quilometragem_negativa():
    service = criar_service()

    carro = service.cadastrar(
        tipo="carro",
        modelo="Civic",
        ano=2025,
        diaria=100,
        preco_km=0.50,
    )

    resultado = (
        carro.adicionar_quilometragem(
            -100
        )
    )

    assert resultado is False

    assert (
        carro.quilometragem
        == 0
    )


# ================================================================
# MANUTENÇÃO
# ================================================================


def test_enviar_veiculo_para_manutencao():
    service = criar_service()

    carro = service.cadastrar(
        "carro",
        "Civic",
        2025,
        100,
        0.50,
    )

    resultado = (
        service.enviar_para_manutencao(
            carro.id
        )
    )

    assert resultado is carro

    assert (
        carro.status.value
        == "manutencao"
    )

    assert (
        carro.disponivel
        is False
    )

    assert (
        carro.ativo
        is True
    )


def test_finalizar_manutencao():
    service = criar_service()

    carro = service.cadastrar(
        "carro",
        "Civic",
        2025,
        100,
        0.50,
    )

    service.enviar_para_manutencao(
        carro.id
    )

    resultado = (
        service.finalizar_manutencao(
            carro.id
        )
    )

    assert resultado is carro

    assert (
        carro.status.value
        == "disponivel"
    )

    assert (
        carro.disponivel
        is True
    )


def test_veiculo_alugado_nao_pode_entrar_em_manutencao():
    service = criar_service()

    carro = service.cadastrar(
        "carro",
        "Civic",
        2025,
        100,
        0.50,
    )

    carro.alugar(
        "lucas"
    )

    with pytest.raises(
        RegraDeNegocio
    ) as erro:
        service.enviar_para_manutencao(
            carro.id
        )

    assert (
        erro.value.mensagem
        == (
            "Um veículo alugado não pode "
            "entrar em manutenção."
        )
    )

    assert (
        carro.status.value
        == "alugado"
    )


def test_listar_veiculos_em_manutencao():
    service = criar_service()

    carro = service.cadastrar(
        "carro",
        "Civic",
        2025,
        100,
        0.50,
    )

    moto = service.cadastrar(
        "moto",
        "CB 500",
        2025,
        80,
        0.30,
    )

    service.enviar_para_manutencao(
        carro.id
    )

    veiculos = (
        service.listar_em_manutencao()
    )

    assert carro in veiculos
    assert moto not in veiculos

def test_service_exige_veiculo_repository():
    with pytest.raises(
        TypeError,
    ):
        VeiculoService()
