from datetime import date, timedelta

from modulos.excecoes import (
    ConflitoConcorrencia,
    RecursoNaoEncontrado,
    RegraDeNegocio,
)
from modulos.reservas import Reserva


class ReservaService:
    """Regras de negócio das reservas futuras."""

    def __init__(
        self,
        veiculo_service,
        reserva_repository,
        aluguel_repository,
        manutencao_repository,
    ):
        if veiculo_service is None:
            raise ValueError(
                "VeiculoService é obrigatório."
            )
        if reserva_repository is None:
            raise ValueError(
                "ReservaRepository é obrigatório."
            )

        self.veiculo_service = veiculo_service
        self.reserva_repository = reserva_repository
        self.aluguel_repository = aluguel_repository
        self.manutencao_repository = manutencao_repository

    @staticmethod
    def _data_iso(valor, nome):
        try:
            return date.fromisoformat(
                str(valor)
            )
        except ValueError as erro:
            raise RegraDeNegocio(
                f"{nome} inválida."
            ) from erro

    def _validar_periodo_futuro(
        self,
        data_inicio,
        data_fim,
    ):
        inicio = self._data_iso(
            data_inicio,
            "Data inicial",
        )
        fim = self._data_iso(
            data_fim,
            "Data final",
        )

        if inicio <= date.today():
            raise RegraDeNegocio(
                "A reserva deve começar "
                "em uma data futura."
            )

        if fim <= inicio:
            raise RegraDeNegocio(
                "A data final deve ser "
                "posterior à data inicial."
            )

        return inicio, fim

    def _conflita_com_aluguel(
        self,
        veiculo_id,
        inicio,
        fim,
    ):
        if self.aluguel_repository is None:
            return False

        for aluguel in (
            self.aluguel_repository
            .listar_ativos()
        ):
            if (
                aluguel.veiculo_id
                != veiculo_id
            ):
                continue

            aluguel_inicio = (
                date.fromisoformat(
                    aluguel.data_inicio
                )
            )
            aluguel_fim = (
                date.fromisoformat(
                    aluguel.data_prevista
                )
            )

            if (
                aluguel_inicio < fim
                and aluguel_fim > inicio
            ):
                return True

        return False

    def _conflita_com_manutencao(
        self,
        veiculo_id,
        inicio,
        fim,
    ):
        if (
            self.manutencao_repository
            is None
        ):
            return False

        manutencao = (
            self.manutencao_repository
            .buscar_ativa_por_veiculo(
                veiculo_id
            )
        )

        if manutencao is None:
            return False

        if not manutencao.data_prevista:
            return True

        manutencao_inicio = (
            date.fromisoformat(
                manutencao.data_inicio
            )
        )
        manutencao_fim = (
            date.fromisoformat(
                manutencao.data_prevista
            )
            + timedelta(days=1)
        )

        return (
            manutencao_inicio < fim
            and manutencao_fim > inicio
        )

    def criar(
        self,
        cliente,
        id_veiculo,
        data_inicio,
        data_fim,
    ):
        inicio, fim = (
            self._validar_periodo_futuro(
                data_inicio,
                data_fim,
            )
        )

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

        if not veiculo.ativo:
            raise RegraDeNegocio(
                "Um veículo desativado "
                "não pode ser reservado."
            )

        conflito = (
            self.reserva_repository
            .buscar_conflitante(
                veiculo_id=id_veiculo,
                data_inicio=(
                    inicio.isoformat()
                ),
                data_fim=(
                    fim.isoformat()
                ),
            )
        )

        if conflito is not None:
            raise RegraDeNegocio(
                "O veículo já possui uma "
                "reserva nesse período."
            )

        if self._conflita_com_aluguel(
            id_veiculo,
            inicio,
            fim,
        ):
            raise RegraDeNegocio(
                "O veículo possui um aluguel "
                "que conflita com esse período."
            )

        if self._conflita_com_manutencao(
            id_veiculo,
            inicio,
            fim,
        ):
            raise RegraDeNegocio(
                "O veículo possui uma manutenção "
                "que conflita com esse período."
            )

        reserva = Reserva(
            id_reserva=0,
            cliente_id=cliente.id,
            cliente_usuario=(
                cliente.usuario
            ),
            cliente_nome=cliente.nome,
            veiculo_id=veiculo.id,
            veiculo_tipo=veiculo.tipo,
            veiculo_modelo=veiculo.modelo,
            data_inicio=inicio.isoformat(),
            data_fim=fim.isoformat(),
        )

        valido, mensagem = (
            reserva.validar_dados()
        )
        if not valido:
            raise RegraDeNegocio(
                mensagem
            )

        reserva.id = (
            self.reserva_repository
            .registrar(
                reserva
            )
        )
        return reserva

    def listar_todas(self):
        return (
            self.reserva_repository
            .listar_colecao()
        )

    def listar_do_cliente(
        self,
        cliente,
    ):
        return (
            self.reserva_repository
            .listar_do_cliente(
                cliente.id
            )
        )

    def consultar(
        self,
        pagina=1,
        por_pagina=12,
        busca="",
        status="todos",
        ordenar="data_inicio",
        direcao="asc",
        cliente_id=None,
    ):
        return (
            self.reserva_repository
            .consultar(
                pagina=pagina,
                por_pagina=por_pagina,
                busca=busca,
                status=status,
                ordenar=ordenar,
                direcao=direcao,
                cliente_id=cliente_id,
            )
        )

    def _cancelar(self, reserva):
        sucesso, mensagem = (
            reserva.cancelar()
        )
        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        self.reserva_repository.atualizar_status(
            reserva,
            status_esperado="ativa",
        )
        return reserva

    def cancelar_do_cliente(
        self,
        id_reserva,
        cliente,
    ):
        reserva = (
            self.reserva_repository
            .buscar_por_id(
                id_reserva
            )
        )
        if reserva is None:
            raise RecursoNaoEncontrado(
                "Reserva não encontrada."
            )
        if not reserva.pertence_ao_cliente(
            cliente
        ):
            raise RegraDeNegocio(
                "Essa reserva não pertence "
                "ao cliente autenticado."
            )

        return self._cancelar(
            reserva
        )

    def cancelar_admin(
        self,
        id_reserva,
    ):
        reserva = (
            self.reserva_repository
            .buscar_por_id(
                id_reserva
            )
        )
        if reserva is None:
            raise RecursoNaoEncontrado(
                "Reserva não encontrada."
            )

        return self._cancelar(
            reserva
        )

    def validar_inicio_aluguel(
        self,
        cliente,
        id_veiculo,
        data_inicio,
        data_fim,
    ):
        reserva = (
            self.reserva_repository
            .buscar_conflitante(
                veiculo_id=id_veiculo,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
        )

        if reserva is None:
            return None

        if (
            reserva.cliente_id
            != cliente.id
        ):
            raise RegraDeNegocio(
                "O veículo está reservado "
                "para outro cliente nesse período."
            )

        if reserva.data_inicio != data_inicio:
            raise RegraDeNegocio(
                "O período solicitado conflita "
                "com uma reserva futura."
            )

        if data_fim > reserva.data_fim:
            raise RegraDeNegocio(
                "O aluguel ultrapassa o período "
                "da reserva existente."
            )

        return reserva

    def converter_para_aluguel(
        self,
        reserva,
    ):
        if reserva is None:
            return None

        sucesso, mensagem = (
            reserva.converter()
        )
        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        self.reserva_repository.atualizar_status(
            reserva,
            status_esperado="ativa",
        )
        return reserva

    def restaurar_apos_falha(
        self,
        reserva,
    ):
        if (
            reserva is None
            or not reserva.restaurar_ativa()
        ):
            return

        try:
            self.reserva_repository.atualizar_status(
                reserva,
                status_esperado="convertida",
                exigir_sem_aluguel_ativo=True,
            )
        except ConflitoConcorrencia:
            # Se outro fluxo já confirmou o aluguel, reativar a reserva
            # recriaria um estado inválido. Nesse caso a restauração é
            # deliberadamente abandonada e a exceção original do aluguel
            # continua sendo a causa visível para o chamador.
            return False

        return True
