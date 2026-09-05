from datetime import date
from enum import Enum
import unicodedata


# ================================================================
# FUNÇÕES AUXILIARES
# ================================================================

def normalizar_texto(texto):
    """
    Converte textos para minúsculo e remove acentos.

    Exemplo:
        "Caminhão" -> "caminhao"
    """
    texto = str(texto).strip().lower()

    return "".join(
        caractere
        for caractere in unicodedata.normalize(
            "NFD",
            texto,
        )
        if unicodedata.category(
            caractere
        ) != "Mn"
    )


def converter_bool(valor):
    """
    Converte valores vindos do SQLite/JSON para bool.

    SQLite:
        1 -> True
        0 -> False
    """
    if isinstance(valor, bool):
        return valor

    if isinstance(valor, (int, float)):
        return bool(valor)

    if isinstance(valor, str):
        return (
            valor.strip().lower()
            in (
                "1",
                "true",
                "sim",
                "yes",
            )
        )

    return bool(valor)


# ================================================================
# STATUS DO VEÍCULO
# ================================================================

class StatusVeiculo(str, Enum):
    DISPONIVEL = "disponivel"
    ALUGADO = "alugado"
    MANUTENCAO = "manutencao"
    DESATIVADO = "desativado"


# ================================================================
# VEÍCULO
# ================================================================

class Veiculo:
    TIPO = "Veículo"

    ANOS_MINIMOS_HABILITACAO = 2

    def __init__(
        self,
        id_veiculo,
        modelo,
        ano,
        diaria,
        preco_km,
        disponivel=True,
        alugado_por=None,
        ativo=True,
        quilometragem=0,
        status=None,
    ):
        self.id = id_veiculo

        self.modelo = str(
            modelo
        ).strip()

        self.ano = int(
            ano
        )

        self.diaria = float(
            diaria
        )

        self.preco_km = float(
            preco_km
        )

        self.quilometragem = float(
            quilometragem
        )

        self.alugado_por = (
            alugado_por
        )

        # ============================================================
        # STATUS
        # ============================================================

        if status is not None:
            if isinstance(
                status,
                StatusVeiculo,
            ):
                self.status = status

            else:
                self.status = (
                    StatusVeiculo(
                        normalizar_texto(
                            status
                        )
                    )
                )

        else:
            ativo = converter_bool(
                ativo
            )

            disponivel = converter_bool(
                disponivel
            )

            # Compatibilidade com dados antigos.
            if not ativo:
                self.status = (
                    StatusVeiculo.DESATIVADO
                )

            elif not disponivel:
                self.status = (
                    StatusVeiculo.ALUGADO
                )

            else:
                self.status = (
                    StatusVeiculo.DISPONIVEL
                )

    # ================================================================
    # PROPRIEDADES
    # ================================================================

    @property
    def tipo(self):
        return self.TIPO

    @property
    def disponivel(self):
        """
        Um veículo só está disponível para aluguel
        quando seu status é DISPONIVEL.
        """
        return (
            self.status
            == StatusVeiculo.DISPONIVEL
        )

    @property
    def ativo(self):
        """
        MANUTENCAO continua sendo um veículo ativo.

        Apenas DESATIVADO representa veículo inativo.
        """
        return (
            self.status
            != StatusVeiculo.DESATIVADO
        )

    # ================================================================
    # VALIDAÇÃO
    # ================================================================

    def validar_dados(self):
        if not self.modelo:
            return (
                False,
                "O modelo não pode ficar vazio.",
            )

        ano_atual = date.today().year

        if (
            self.ano < 1900
            or self.ano > ano_atual + 1
        ):
            return (
                False,
                "Ano do veículo inválido.",
            )

        if self.diaria <= 0:
            return (
                False,
                "A diária deve ser maior que zero.",
            )

        if self.preco_km < 0:
            return (
                False,
                "O preço por km não pode ser negativo.",
            )

        if self.quilometragem < 0:
            return (
                False,
                "Quilometragem inválida.",
            )

        return True, ""

    # ================================================================
    # EDIÇÃO
    # ================================================================

    def atualizar_dados(
        self,
        modelo=None,
        ano=None,
        diaria=None,
        preco_km=None,
    ):
        """
        Atualiza os dados do veículo.

        Se algum novo dado for inválido,
        os valores antigos são restaurados.
        """

        dados_antigos = {
            "modelo": self.modelo,
            "ano": self.ano,
            "diaria": self.diaria,
            "preco_km": self.preco_km,
        }

        if modelo is not None:
            self.modelo = str(
                modelo
            ).strip()

        if ano is not None:
            self.ano = int(
                ano
            )

        if diaria is not None:
            self.diaria = float(
                diaria
            )

        if preco_km is not None:
            self.preco_km = float(
                preco_km
            )

        valido, mensagem = (
            self.validar_dados()
        )

        if not valido:
            self.modelo = (
                dados_antigos["modelo"]
            )

            self.ano = (
                dados_antigos["ano"]
            )

            self.diaria = (
                dados_antigos["diaria"]
            )

            self.preco_km = (
                dados_antigos["preco_km"]
            )

            return (
                False,
                mensagem,
            )

        return (
            True,
            "Veículo atualizado com sucesso.",
        )

    # ================================================================
    # BUSCA
    # ================================================================

    def corresponde_busca(
        self,
        termo,
    ):
        termo = normalizar_texto(
            termo
        )

        if not termo:
            return False

        dados_busca = (
            str(self.id),
            self.tipo,
            self.modelo,
            str(self.ano),
        )

        return any(
            termo
            in normalizar_texto(
                valor
            )
            for valor in dados_busca
        )

    # ================================================================
    # ALUGUEL
    # ================================================================

    def pode_ser_alugado(
        self,
        anos_habilitacao=0,
    ):
        if (
            self.status
            != StatusVeiculo.DISPONIVEL
        ):
            return False

        return (
            anos_habilitacao
            >= self.ANOS_MINIMOS_HABILITACAO
        )

    def alugar(
        self,
        usuario,
    ):
        if (
            self.status
            != StatusVeiculo.DISPONIVEL
        ):
            return False

        self.status = (
            StatusVeiculo.ALUGADO
        )

        self.alugado_por = usuario

        return True

    def devolver(self):
        if (
            self.status
            != StatusVeiculo.ALUGADO
        ):
            return False

        self.status = (
            StatusVeiculo.DISPONIVEL
        )

        self.alugado_por = None

        return True

    # ================================================================
    # VALOR DO ALUGUEL
    # ================================================================

    def calcular_valor(
        self,
        dias,
        km,
    ):
        valor_diarias = (
            self.diaria
            * dias
        )

        valor_km = (
            self.preco_km
            * km
        )

        return (
            valor_diarias
            + valor_km
        )

    # ================================================================
    # QUILOMETRAGEM
    # ================================================================

    def adicionar_quilometragem(
        self,
        km,
    ):
        if km < 0:
            return False

        self.quilometragem += float(
            km
        )

        return True

    # ================================================================
    # MANUTENÇÃO
    # ================================================================

    def enviar_para_manutencao(
        self,
    ):
        """
        Apenas veículos disponíveis podem entrar
        em manutenção.
        """

        if (
            self.status
            != StatusVeiculo.DISPONIVEL
        ):
            return False

        self.status = (
            StatusVeiculo.MANUTENCAO
        )

        self.alugado_por = None

        return True

    def finalizar_manutencao(
        self,
    ):
        if (
            self.status
            != StatusVeiculo.MANUTENCAO
        ):
            return False

        self.status = (
            StatusVeiculo.DISPONIVEL
        )

        self.alugado_por = None

        return True

    # ================================================================
    # ATIVAÇÃO / DESATIVAÇÃO
    # ================================================================

    def desativar(self):
        """
        Desativa o veículo.

        Um veículo alugado não pode ser desativado.
        """

        if (
            self.status
            == StatusVeiculo.ALUGADO
        ):
            return (
                False,
                "Não é possível desativar um veículo alugado.",
            )

        if (
            self.status
            == StatusVeiculo.DESATIVADO
        ):
            return (
                False,
                "O veículo já está desativado.",
            )

        self.status = (
            StatusVeiculo.DESATIVADO
        )

        self.alugado_por = None

        return (
            True,
            "Veículo desativado com sucesso.",
        )


    def reativar(self):
        """
        Reativa um veículo desativado.
        """

        if (
            self.status
            != StatusVeiculo.DESATIVADO
        ):
            return (
                False,
                "O veículo não está desativado.",
            )

        self.status = (
            StatusVeiculo.DISPONIVEL
        )

        self.alugado_por = None

        return (
            True,
            "Veículo reativado com sucesso.",
        )

    # ================================================================
    # SERIALIZAÇÃO
    # ================================================================

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "modelo": self.modelo,
            "ano": self.ano,
            "diaria": self.diaria,
            "preco_km": self.preco_km,
            "quilometragem": self.quilometragem,

            # Nova fonte de verdade.
            "status": self.status.value,

            # Mantidos temporariamente para compatibilidade
            # com o SQLite atual.
            "disponivel": self.disponivel,
            "alugado_por": self.alugado_por,
            "ativo": self.ativo,
        }

    @classmethod
    def from_dict(
        cls,
        dados,
        id_padrao=None,
    ):
        tipo = normalizar_texto(
            dados.get(
                "tipo",
                "veiculo",
            )
        )

        classes = {
            "carro": Carro,
            "moto": Moto,
            "caminhao": Caminhao,
            "bicicleta": Bicicleta,
        }

        classe_veiculo = (
            classes.get(
                tipo,
                Veiculo,
            )
        )

        id_veiculo = dados.get(
            "id",
            id_padrao,
        )

        if id_veiculo is None:
            id_veiculo = 0

        return classe_veiculo(
            id_veiculo=id_veiculo,

            modelo=dados.get(
                "modelo",
                "",
            ),

            ano=dados.get(
                "ano",
                1900,
            ),

            diaria=dados.get(
                "diaria",
                0,
            ),

            preco_km=dados.get(
                "preco_km",
                0,
            ),

            disponivel=converter_bool(
                dados.get(
                    "disponivel",
                    True,
                )
            ),

            alugado_por=dados.get(
                "alugado_por"
            ),

            ativo=converter_bool(
                dados.get(
                    "ativo",
                    True,
                )
            ),

            quilometragem=dados.get(
                "quilometragem",
                0,
            ),

            status=dados.get(
                "status"
            ),
        )


# ================================================================
# TIPOS DE VEÍCULOS
# ================================================================

class Carro(Veiculo):
    TIPO = "Carro"

    ANOS_MINIMOS_HABILITACAO = 2


class Moto(Veiculo):
    TIPO = "Moto"

    ANOS_MINIMOS_HABILITACAO = 2


class Caminhao(Veiculo):
    TIPO = "Caminhão"

    ANOS_MINIMOS_HABILITACAO = 2


class Bicicleta(Veiculo):
    TIPO = "Bicicleta"

    ANOS_MINIMOS_HABILITACAO = 0


# ================================================================
# FACTORY
# ================================================================

def criar_veiculo_por_tipo(
    tipo,
    id_veiculo,
    modelo,
    ano,
    diaria,
    preco_km,
):
    """
    Factory responsável por criar o tipo correto
    de veículo.
    """

    tipo_normalizado = normalizar_texto(
        tipo
    )

    tipos = {
        "1": Carro,
        "carro": Carro,

        "2": Moto,
        "moto": Moto,

        "3": Caminhao,
        "caminhao": Caminhao,

        "4": Bicicleta,
        "bicicleta": Bicicleta,
    }

    classe = tipos.get(
        tipo_normalizado
    )

    if classe is None:
        return None

    return classe(
        id_veiculo=id_veiculo,
        modelo=modelo,
        ano=ano,
        diaria=diaria,
        preco_km=preco_km,
    )