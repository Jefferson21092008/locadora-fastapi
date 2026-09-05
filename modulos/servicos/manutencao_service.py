from modulos.manutencoes import (
    Manutencao,
)

from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)


class ManutencaoService:
    def __init__(
        self,
        veiculo_service,
        manutencao_repository,
    ):
        if veiculo_service is None:
            raise ValueError(
                "VeiculoService é obrigatório."
            )

        if manutencao_repository is None:
            raise ValueError(
                "ManutencaoRepository é obrigatório."
            )

        self.veiculo_service = (
            veiculo_service
        )
        self.manutencao_repository = (
            manutencao_repository
        )

    # ================================================================
    # BUSCAS
    # ================================================================

    def buscar_ativa_por_veiculo(
        self,
        id_veiculo,
    ):
        return (
            self.manutencao_repository
            .buscar_ativa_por_veiculo(
                id_veiculo
            )
        )

    def listar_por_veiculo(
        self,
        id_veiculo,
    ):
        return (
            self.manutencao_repository
            .listar_por_veiculo(
                id_veiculo
            )
        )

    def listar_ativas(self):
        return (
            self.manutencao_repository
            .listar_ativas()
        )

    # ================================================================
    # ABRIR MANUTENÇÃO
    # ================================================================

    def abrir(
        self,
        id_veiculo,
        motivo,
    ):
        veiculo = (
            self.veiculo_service
            .buscar_por_id(
                id_veiculo
            )
        )

        if veiculo is None:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        manutencao_ativa = (
            self.buscar_ativa_por_veiculo(
                id_veiculo
            )
        )

        if manutencao_ativa is not None:
            raise RegraDeNegocio(
                "Esse veículo já possui "
                "uma manutenção ativa."
            )

        manutencao = Manutencao(
            id_manutencao=0,
            veiculo_id=veiculo.id,
            motivo=motivo,
            quilometragem=(
                veiculo.quilometragem
            ),
        )

        valido, mensagem = (
            manutencao.validar_dados()
        )

        if not valido:
            raise RegraDeNegocio(
                mensagem
            )

        estado_veiculo = (
            vars(
                veiculo
            ).copy()
        )

        sucesso = (
            veiculo
            .enviar_para_manutencao()
        )

        if not sucesso:
            raise RegraDeNegocio(
                "O veículo precisa estar "
                "disponível para entrar "
                "em manutenção."
            )

        try:
            novo_id = (
                self.manutencao_repository
                .registrar(
                    manutencao,
                    veiculo,
                )
            )

        except Exception:
            veiculo.__dict__.clear()

            veiculo.__dict__.update(
                estado_veiculo
            )

            raise

        manutencao.id = novo_id

        return manutencao

    # ================================================================
    # FINALIZAR MANUTENÇÃO
    # ================================================================

    def finalizar(
        self,
        id_veiculo,
        custo,
        data_fim=None,
    ):
        veiculo = (
            self.veiculo_service
            .buscar_por_id(
                id_veiculo
            )
        )

        if veiculo is None:
            raise RecursoNaoEncontrado(
                "Veículo não encontrado."
            )

        manutencao = (
            self.buscar_ativa_por_veiculo(
                id_veiculo
            )
        )

        if manutencao is None:
            raise RecursoNaoEncontrado(
                "Esse veículo não possui "
                "manutenção ativa."
            )

        estado_manutencao = (
            vars(
                manutencao
            ).copy()
        )

        estado_veiculo = (
            vars(
                veiculo
            ).copy()
        )

        sucesso, mensagem = (
            manutencao.finalizar(
                custo=custo,
                data_fim=data_fim,
            )
        )

        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        sucesso = (
            veiculo
            .finalizar_manutencao()
        )

        if not sucesso:
            manutencao.__dict__.clear()

            manutencao.__dict__.update(
                estado_manutencao
            )

            raise RegraDeNegocio(
                "O veículo não está "
                "em manutenção."
            )

        try:
            self.manutencao_repository.registrar_finalizacao(
                manutencao,
                veiculo,
            )

        except Exception:
            manutencao.__dict__.clear()

            manutencao.__dict__.update(
                estado_manutencao
            )

            veiculo.__dict__.clear()

            veiculo.__dict__.update(
                estado_veiculo
            )

            raise

        return manutencao

    def listar_manutencoes(self):
        return (
            self.manutencao_repository
            .listar_colecao()
        )
