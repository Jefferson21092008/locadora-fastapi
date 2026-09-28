from modulos.excecoes import (
    RecursoNaoEncontrado,
    RegraDeNegocio,
)
from modulos.vistorias import (
    CaucaoAluguel,
    DanoAluguel,
    InspecaoAluguel,
    MultaTransito,
)


class VistoriaService:
    def __init__(
        self,
        aluguel_repository,
        vistoria_repository,
    ):
        if aluguel_repository is None:
            raise ValueError(
                "AluguelRepository é obrigatório."
            )

        if vistoria_repository is None:
            raise ValueError(
                "VistoriaRepository é obrigatório."
            )

        self.aluguel_repository = (
            aluguel_repository
        )
        self.vistoria_repository = (
            vistoria_repository
        )

    # ================================================================
    # APOIO
    # ================================================================

    def _obter_aluguel(
        self,
        id_aluguel,
    ):
        aluguel = (
            self.aluguel_repository
            .buscar_por_id(
                id_aluguel
            )
        )

        if aluguel is None:
            raise RecursoNaoEncontrado(
                "Aluguel não encontrado."
            )

        return aluguel

    @staticmethod
    def _validar_entidade(
        entidade,
    ):
        valido, mensagem = (
            entidade.validar_dados()
        )

        if not valido:
            raise RegraDeNegocio(
                mensagem
            )

    # ================================================================
    # CONSULTA CONSOLIDADA
    # ================================================================

    def obter_resumo(
        self,
        id_aluguel,
    ):
        aluguel = self._obter_aluguel(
            id_aluguel
        )

        inspecoes = (
            self.vistoria_repository
            .listar_inspecoes(
                id_aluguel
            )
        )
        danos = (
            self.vistoria_repository
            .listar_danos(
                id_aluguel
            )
        )
        multas = (
            self.vistoria_repository
            .listar_multas(
                id_aluguel
            )
        )
        caucao = (
            self.vistoria_repository
            .buscar_caucao(
                id_aluguel
            )
        )

        retirada = next(
            (
                item
                for item in inspecoes
                if item.tipo
                == InspecaoAluguel.TIPO_RETIRADA
            ),
            None,
        )
        devolucao = next(
            (
                item
                for item in inspecoes
                if item.tipo
                == InspecaoAluguel.TIPO_DEVOLUCAO
            ),
            None,
        )

        combustivel_retirada = (
            retirada.combustivel_percentual
            if retirada is not None
            else None
        )
        combustivel_devolucao = (
            devolucao.combustivel_percentual
            if devolucao is not None
            else None
        )

        combustivel_faltante = 0

        if (
            combustivel_retirada is not None
            and combustivel_devolucao is not None
        ):
            combustivel_faltante = max(
                combustivel_retirada
                - combustivel_devolucao,
                0,
            )

        danos_ativos_total = sum(
            dano.valor_estimado
            for dano in danos
            if dano.ativo
        )
        multas_ativas_total = sum(
            multa.valor
            for multa in multas
            if multa.ativa
        )

        return {
            "aluguel": aluguel,
            "inspecoes": inspecoes,
            "danos": danos,
            "multas": multas,
            "caucao": caucao,
            "indicadores": {
                "combustivel_retirada": (
                    combustivel_retirada
                ),
                "combustivel_devolucao": (
                    combustivel_devolucao
                ),
                "combustivel_faltante": (
                    combustivel_faltante
                ),
                "danos_ativos_total": (
                    danos_ativos_total
                ),
                "multas_ativas_total": (
                    multas_ativas_total
                ),
                "caucao_retida": (
                    caucao.valor_retido
                    if caucao is not None
                    else 0
                ),
                "pendencias_estimadas_total": (
                    danos_ativos_total
                    + multas_ativas_total
                ),
            },
        }

    # ================================================================
    # INSPEÇÕES
    # ================================================================

    def registrar_inspecao(
        self,
        id_aluguel,
        tipo,
        quilometragem,
        combustivel_percentual,
        observacoes=None,
    ):
        aluguel = self._obter_aluguel(
            id_aluguel
        )

        tipo = str(
            tipo
        ).strip().lower()

        existente = (
            self.vistoria_repository
            .buscar_inspecao(
                id_aluguel,
                tipo,
            )
        )

        if existente is not None:
            raise RegraDeNegocio(
                "Já existe uma inspeção desse tipo "
                "para o aluguel."
            )

        if (
            tipo
            == InspecaoAluguel.TIPO_RETIRADA
            and aluguel.status != "ativo"
        ):
            raise RegraDeNegocio(
                "A inspeção de retirada só pode ser "
                "registrada em aluguel ativo."
            )

        inspecao = InspecaoAluguel(
            id_inspecao=0,
            aluguel_id=id_aluguel,
            tipo=tipo,
            quilometragem=quilometragem,
            combustivel_percentual=(
                combustivel_percentual
            ),
            observacoes=observacoes,
        )

        self._validar_entidade(
            inspecao
        )

        if (
            tipo
            == InspecaoAluguel.TIPO_DEVOLUCAO
        ):
            retirada = (
                self.vistoria_repository
                .buscar_inspecao(
                    id_aluguel,
                    InspecaoAluguel.TIPO_RETIRADA,
                )
            )

            if (
                retirada is not None
                and inspecao.quilometragem
                < retirada.quilometragem
            ):
                raise RegraDeNegocio(
                    "A quilometragem da devolução "
                    "não pode ser menor que a da retirada."
                )

        inspecao.id = (
            self.vistoria_repository
            .registrar_inspecao(
                inspecao
            )
        )

        return inspecao

    # ================================================================
    # DANOS
    # ================================================================

    def registrar_dano(
        self,
        id_aluguel,
        descricao,
        valor_estimado,
    ):
        self._obter_aluguel(
            id_aluguel
        )

        dano = DanoAluguel(
            id_dano=0,
            aluguel_id=id_aluguel,
            descricao=descricao,
            valor_estimado=(
                valor_estimado
            ),
        )

        self._validar_entidade(
            dano
        )

        dano.id = (
            self.vistoria_repository
            .registrar_dano(
                dano
            )
        )

        return dano

    def cancelar_dano(
        self,
        id_dano,
    ):
        dano = (
            self.vistoria_repository
            .buscar_dano(
                id_dano
            )
        )

        if dano is None:
            raise RecursoNaoEncontrado(
                "Dano não encontrado."
            )

        sucesso, mensagem = (
            dano.cancelar()
        )

        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        self.vistoria_repository.atualizar_dano(
            dano
        )

        return dano

    # ================================================================
    # MULTAS DE TRÂNSITO
    # ================================================================

    def registrar_multa(
        self,
        id_aluguel,
        descricao,
        valor,
        data_ocorrencia,
    ):
        self._obter_aluguel(
            id_aluguel
        )

        multa = MultaTransito(
            id_multa=0,
            aluguel_id=id_aluguel,
            descricao=descricao,
            valor=valor,
            data_ocorrencia=(
                data_ocorrencia
            ),
        )

        self._validar_entidade(
            multa
        )

        multa.id = (
            self.vistoria_repository
            .registrar_multa(
                multa
            )
        )

        return multa

    def cancelar_multa(
        self,
        id_multa,
    ):
        multa = (
            self.vistoria_repository
            .buscar_multa(
                id_multa
            )
        )

        if multa is None:
            raise RecursoNaoEncontrado(
                "Multa de trânsito não encontrada."
            )

        sucesso, mensagem = (
            multa.cancelar()
        )

        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        self.vistoria_repository.atualizar_multa(
            multa
        )

        return multa

    # ================================================================
    # CAUÇÃO
    # ================================================================

    def definir_caucao(
        self,
        id_aluguel,
        valor,
        valor_liberado=0,
        observacoes=None,
    ):
        self._obter_aluguel(
            id_aluguel
        )

        caucao = (
            self.vistoria_repository
            .buscar_caucao(
                id_aluguel
            )
        )

        if caucao is None:
            caucao = CaucaoAluguel(
                id_caucao=0,
                aluguel_id=id_aluguel,
                valor=valor,
                valor_liberado=(
                    valor_liberado
                ),
                observacoes=observacoes,
            )
            self._validar_entidade(
                caucao
            )
        else:
            sucesso, mensagem = (
                caucao.atualizar(
                    valor=valor,
                    valor_liberado=(
                        valor_liberado
                    ),
                    observacoes=(
                        observacoes
                    ),
                )
            )

            if not sucesso:
                raise RegraDeNegocio(
                    mensagem
                )

        return (
            self.vistoria_repository
            .salvar_caucao(
                caucao
            )
        )
