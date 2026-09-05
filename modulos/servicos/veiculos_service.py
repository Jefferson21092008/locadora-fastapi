from modulos.veiculos import (
    criar_veiculo_por_tipo,
    StatusVeiculo,
)

from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)


class VeiculoService:
    """Regras e operações relacionadas aos veículos."""

    def __init__(
        self,
        veiculo_repository,
    ):
        """Recebe o repository por injeção de dependência."""
        if veiculo_repository is None:
            raise ValueError(
                "VeiculoRepository é obrigatório."
            )

        self.veiculo_repository = (
            veiculo_repository
        )

    # ================================================================
    # BUSCAS
    # ================================================================

    def buscar_por_id(
        self,
        id_veiculo,
    ):
        return (
            self.veiculo_repository
            .buscar_por_id(
                id_veiculo
            )
        )

    def buscar(
        self,
        termo,
    ):
        return (
            self.veiculo_repository
            .buscar(
                termo
            )
        )

    # ================================================================
    # LISTAGENS
    # ================================================================

    def listar_todos(self):
        return (
            self.veiculo_repository
            .listar_colecao()
        )

    def listar_disponiveis(self):
        return (
            self.veiculo_repository
            .listar_disponiveis()
        )

    def listar_ativos(self):
        return (
            self.veiculo_repository
            .listar_ativos()
        )

    def listar_desativados(self):
        return (
            self.veiculo_repository
            .listar_desativados()
        )

    def listar_alugados(self):
        return (
            self.veiculo_repository
            .listar_alugados()
        )

    # ================================================================
    # DISPONIBILIDADE
    # ================================================================

    def obter_disponivel(
        self,
        id_veiculo,
    ):
        veiculo = self.buscar_por_id(
            id_veiculo
        )

        if veiculo is None:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        if not veiculo.ativo:
            raise RegraDeNegocio(
                "Esse veículo está desativado."
            )

        if not veiculo.disponivel:
            raise RegraDeNegocio(
                "Esse veículo está alugado."
            )

        return veiculo

    # ================================================================
    # CADASTRO
    # ================================================================

    def cadastrar(
        self,
        tipo,
        modelo,
        ano,
        diaria,
        preco_km,
    ):
        novo_veiculo = criar_veiculo_por_tipo(
            tipo=tipo,
            id_veiculo=0,
            modelo=modelo,
            ano=ano,
            diaria=diaria,
            preco_km=preco_km,
        )

        if novo_veiculo is None:
            raise RegraDeNegocio(
                "Tipo de veículo inválido."
            )

        valido, mensagem = (
            novo_veiculo.validar_dados()
        )

        if not valido:
            raise RegraDeNegocio(
                mensagem
            )

        novo_id = (
            self.veiculo_repository
            .inserir(
                novo_veiculo
            )
        )

        novo_veiculo.id = novo_id

        return novo_veiculo

    # ================================================================
    # EDIÇÃO
    # ================================================================

    def editar(
        self,
        id_veiculo,
        modelo=None,
        ano=None,
        diaria=None,
        preco_km=None,
    ):
        veiculo = self.buscar_por_id(
            id_veiculo
        )

        if veiculo is None:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        if not veiculo.ativo:
            raise RegraDeNegocio(
                "Não é possível editar "
                "um veículo desativado."
            )

        if not veiculo.disponivel:
            raise RegraDeNegocio(
                "Não é possível editar "
                "um veículo alugado."
            )

        sucesso, mensagem = (
            veiculo.atualizar_dados(
                modelo=modelo,
                ano=ano,
                diaria=diaria,
                preco_km=preco_km,
            )
        )

        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        self.veiculo_repository.atualizar(
            veiculo
        )

        return veiculo

    # ================================================================
    # DESATIVAÇÃO / REATIVAÇÃO
    # ================================================================

    def desativar(
        self,
        id_veiculo,
    ):
        veiculo = self.buscar_por_id(
            id_veiculo
        )

        if veiculo is None:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        sucesso, mensagem = (
            veiculo.desativar()
        )

        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        self.veiculo_repository.atualizar(
            veiculo
        )

        return veiculo

    def reativar(
        self,
        id_veiculo,
    ):
        veiculo = self.buscar_por_id(
            id_veiculo
        )

        if veiculo is None:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        sucesso, mensagem = (
            veiculo.reativar()
        )

        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        self.veiculo_repository.atualizar(
            veiculo
        )

        return veiculo

    # ================================================================
    # MANUTENÇÃO
    # ================================================================

    def enviar_para_manutencao(
        self,
        id_veiculo,
    ):
        veiculo = self.buscar_por_id(
            id_veiculo
        )

        if veiculo is None:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        if (
            veiculo.status
            == StatusVeiculo.ALUGADO
        ):
            raise RegraDeNegocio(
                "Um veículo alugado não pode "
                "entrar em manutenção."
            )

        if (
            veiculo.status
            == StatusVeiculo.MANUTENCAO
        ):
            raise RegraDeNegocio(
                "O veículo já está em manutenção."
            )

        if (
            veiculo.status
            == StatusVeiculo.DESATIVADO
        ):
            raise RegraDeNegocio(
                "Um veículo desativado não pode "
                "entrar em manutenção."
            )

        estado_anterior = veiculo.status

        sucesso = (
            veiculo.enviar_para_manutencao()
        )

        if not sucesso:
            raise RegraDeNegocio(
                "Não foi possível enviar o "
                "veículo para manutenção."
            )

        try:
            self.veiculo_repository.atualizar(
                veiculo
            )

        except Exception:
            veiculo.status = estado_anterior
            raise

        return veiculo

    def finalizar_manutencao(
        self,
        id_veiculo,
    ):
        veiculo = self.buscar_por_id(
            id_veiculo
        )

        if veiculo is None:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        if (
            veiculo.status
            != StatusVeiculo.MANUTENCAO
        ):
            raise RegraDeNegocio(
                "Esse veículo não está em manutenção."
            )

        estado_anterior = veiculo.status

        sucesso = (
            veiculo.finalizar_manutencao()
        )

        if not sucesso:
            raise RegraDeNegocio(
                "Não foi possível finalizar "
                "a manutenção."
            )

        try:
            self.veiculo_repository.atualizar(
                veiculo
            )

        except Exception:
            veiculo.status = estado_anterior
            raise

        return veiculo

    def listar_em_manutencao(self):
        return (
            self.veiculo_repository
            .listar_em_manutencao()
        )
