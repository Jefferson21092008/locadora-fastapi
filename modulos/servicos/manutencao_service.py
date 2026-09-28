from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)
from modulos.manutencoes import (
    Manutencao,
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

    def buscar_por_id(
        self,
        id_manutencao,
    ):
        return (
            self.manutencao_repository
            .buscar_por_id(
                id_manutencao
            )
        )

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

    def abrir(
        self,
        id_veiculo,
        motivo,
        tipo="corretiva",
        prioridade="media",
        fornecedor=None,
        custo_estimado=0,
        data_prevista=None,
        observacoes=None,
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
            tipo=tipo,
            prioridade=prioridade,
            fornecedor=fornecedor,
            custo_estimado=custo_estimado,
            data_prevista=data_prevista,
            observacoes=observacoes,
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

    def atualizar(
        self,
        id_manutencao,
        alteracoes,
    ):
        manutencao = (
            self.buscar_por_id(
                id_manutencao
            )
        )

        if manutencao is None:
            raise RecursoNaoEncontrado(
                "Manutenção não encontrada."
            )

        estado_anterior = (
            vars(
                manutencao
            ).copy()
        )

        sucesso, mensagem = (
            manutencao.atualizar_detalhes(
                **alteracoes
            )
        )

        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        try:
            self.manutencao_repository.atualizar(
                manutencao
            )
        except Exception:
            manutencao.__dict__.clear()
            manutencao.__dict__.update(
                estado_anterior
            )
            raise

        return manutencao

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

    def consultar_manutencoes(
        self,
        pagina=1,
        por_pagina=12,
        busca="",
        status="todos",
        tipo="todos",
        prioridade="todos",
        ordenar="id",
        direcao="desc",
    ):
        return (
            self.manutencao_repository
            .consultar(
                pagina=pagina,
                por_pagina=por_pagina,
                busca=busca,
                status=status,
                tipo=tipo,
                prioridade=prioridade,
                ordenar=ordenar,
                direcao=direcao,
            )
        )

    def listar_manutencoes(self):
        return (
            self.manutencao_repository
            .listar_colecao()
        )
