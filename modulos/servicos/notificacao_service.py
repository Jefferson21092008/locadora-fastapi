import logging
from datetime import date

from modulos.excecoes import RecursoNaoEncontrado
from modulos.notificacoes import Notificacao


logger = logging.getLogger(__name__)


class NotificacaoService:
    """Gera lembretes idempotentes e gerencia a caixa de notificações."""

    def __init__(
        self,
        notificacao_repository,
        usuario_repository,
        cliente_repository,
        reserva_repository,
        aluguel_repository,
        manutencao_repository,
        pagamento_service,
        email_service,
    ):
        self.notificacao_repository = notificacao_repository
        self.usuario_repository = usuario_repository
        self.cliente_repository = cliente_repository
        self.reserva_repository = reserva_repository
        self.aluguel_repository = aluguel_repository
        self.manutencao_repository = manutencao_repository
        self.pagamento_service = pagamento_service
        self.email_service = email_service

    @staticmethod
    def _data(valor):
        try:
            return date.fromisoformat(str(valor))
        except (TypeError, ValueError):
            return None

    def _status_email_inicial(self, destinatario):
        if not destinatario:
            return "nao_aplicavel"

        if not getattr(
            self.email_service.config,
            "email_configurado",
            False,
        ):
            return "nao_configurado"

        return "pendente"

    def _criar(
        self,
        *,
        usuario_id,
        tipo,
        titulo,
        mensagem,
        chave,
        referencia_tipo=None,
        referencia_id=None,
        email_destinatario=None,
        caminho=None,
    ):
        notificacao = Notificacao(
            id_notificacao=0,
            usuario_id=usuario_id,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            chave_deduplicacao=chave,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
            email_destinatario=email_destinatario,
            email_status=self._status_email_inicial(
                email_destinatario
            ),
        )

        valida, mensagem_erro = notificacao.validar_dados()
        if not valida:
            raise ValueError(mensagem_erro)

        salva, criada = (
            self.notificacao_repository.inserir_se_ausente(
                notificacao
            )
        )

        email_enviado = False
        email_falhou = False

        if criada and salva.email_status == "pendente":
            try:
                self.email_service.enviar_notificacao(
                    destinatario=salva.email_destinatario,
                    assunto=salva.titulo,
                    mensagem=salva.mensagem,
                    caminho=caminho,
                )
                salva.atualizar_status_email("enviado")
                email_enviado = True
            except Exception:
                logger.exception(
                    "Falha ao enviar notificação por e-mail."
                )
                salva.atualizar_status_email("falhou")
                email_falhou = True

            self.notificacao_repository.atualizar(salva)

        return {
            "criada": criada,
            "email_enviado": email_enviado,
            "email_falhou": email_falhou,
        }

    def _processar_cliente(self, usuario, data_referencia):
        cliente = self.cliente_repository.buscar_por_usuario_id(
            usuario.id
        )
        if cliente is None:
            return []

        resultados = []
        hoje = data_referencia

        for reserva in self.reserva_repository.listar_do_cliente(
            cliente.id
        ):
            if not reserva.ativa:
                continue

            inicio = self._data(reserva.data_inicio)
            if inicio is None:
                continue

            dias = (inicio - hoje).days
            if dias not in {0, 1}:
                continue

            quando = "hoje" if dias == 0 else "amanhã"
            resultados.append(
                self._criar(
                    usuario_id=usuario.id,
                    tipo="reserva_proxima",
                    titulo=f"Sua reserva começa {quando}",
                    mensagem=(
                        f"O veículo {reserva.veiculo_modelo} está reservado "
                        f"para você a partir de {reserva.data_inicio}."
                    ),
                    chave=(
                        f"usuario:{usuario.id}:reserva:{reserva.id}:d{dias}"
                    ),
                    referencia_tipo="reserva",
                    referencia_id=reserva.id,
                    email_destinatario=cliente.email,
                    caminho="/app/reservas.html",
                )
            )

        alugueis = self.aluguel_repository.listar_do_cliente(
            cliente
        )
        for aluguel in alugueis:
            if aluguel.status != "ativo":
                continue

            prevista = self._data(aluguel.data_prevista)
            if prevista is None:
                continue

            dias = (prevista - hoje).days
            if dias > 1:
                continue

            if dias == 1:
                tipo = "aluguel_vencendo"
                titulo = "Seu aluguel vence amanhã"
                chave_situacao = "d1"
            elif dias == 0:
                tipo = "aluguel_vencendo"
                titulo = "Seu aluguel vence hoje"
                chave_situacao = "d0"
            else:
                tipo = "aluguel_atrasado"
                titulo = "Seu aluguel está atrasado"
                chave_situacao = "atrasado"

            resultados.append(
                self._criar(
                    usuario_id=usuario.id,
                    tipo=tipo,
                    titulo=titulo,
                    mensagem=(
                        f"O aluguel do veículo {aluguel.veiculo_modelo} "
                        f"tem devolução prevista para {aluguel.data_prevista}."
                    ),
                    chave=(
                        f"usuario:{usuario.id}:aluguel:{aluguel.id}:"
                        f"{chave_situacao}"
                    ),
                    referencia_tipo="aluguel",
                    referencia_id=aluguel.id,
                    email_destinatario=cliente.email,
                    caminho="/app/alugueis.html",
                )
            )

        for aluguel in alugueis:
            if aluguel.status != "finalizado":
                continue

            resumo = self.pagamento_service.obter_resumo(
                aluguel.id
            )
            if resumo["saldo_pendente"] <= 0:
                continue

            resultados.append(
                self._criar(
                    usuario_id=usuario.id,
                    tipo="financeiro_pendente",
                    titulo="Há uma pendência financeira",
                    mensagem=(
                        "Um aluguel finalizado possui valores adicionais "
                        "pendentes. Consulte seus aluguéis ou fale com a locadora para ver o saldo atual."
                    ),
                    chave=(
                        f"usuario:{usuario.id}:financeiro:"
                        f"{aluguel.id}:pendente"
                    ),
                    referencia_tipo="financeiro",
                    referencia_id=aluguel.id,
                    email_destinatario=cliente.email,
                    caminho="/app/alugueis.html",
                )
            )

        return resultados

    def _processar_admin(self, usuario, data_referencia):
        resultados = []
        hoje = data_referencia

        for manutencao in self.manutencao_repository.listar_ativas():
            prevista = self._data(manutencao.data_prevista)
            if prevista is None:
                continue

            dias = (prevista - hoje).days
            if dias > 1:
                continue

            if dias == 1:
                tipo = "manutencao_vencendo"
                titulo = "Manutenção prevista para amanhã"
                chave_situacao = "d1"
            elif dias == 0:
                tipo = "manutencao_vencendo"
                titulo = "Manutenção prevista para hoje"
                chave_situacao = "d0"
            else:
                tipo = "manutencao_atrasada"
                titulo = "Manutenção atrasada"
                chave_situacao = "atrasada"

            resultados.append(
                self._criar(
                    usuario_id=usuario.id,
                    tipo=tipo,
                    titulo=titulo,
                    mensagem=(
                        f"A manutenção #{manutencao.id} do veículo "
                        f"#{manutencao.veiculo_id} tem previsão em "
                        f"{manutencao.data_prevista}."
                    ),
                    chave=(
                        f"usuario:{usuario.id}:manutencao:"
                        f"{manutencao.id}:{chave_situacao}"
                    ),
                    referencia_tipo="manutencao",
                    referencia_id=manutencao.id,
                    caminho="/app/manutencoes.html",
                )
            )

        return resultados

    def processar_usuario(self, usuario, data_referencia=None):
        hoje = data_referencia or date.today()
        role = getattr(usuario.role, "value", usuario.role)

        if role == "cliente":
            resultados = self._processar_cliente(
                usuario,
                hoje,
            )
        else:
            resultados = self._processar_admin(
                usuario,
                hoje,
            )

        return {
            "criadas": sum(
                1 for resultado in resultados if resultado["criada"]
            ),
            "emails_enviados": sum(
                1
                for resultado in resultados
                if resultado["email_enviado"]
            ),
            "emails_falharam": sum(
                1
                for resultado in resultados
                if resultado["email_falhou"]
            ),
        }

    def consultar(
        self,
        usuario_id,
        pagina=1,
        por_pagina=20,
        status="todas",
    ):
        return self.notificacao_repository.consultar_usuario(
            usuario_id=usuario_id,
            pagina=pagina,
            por_pagina=por_pagina,
            status=status,
        )

    def marcar_como_lida(self, id_notificacao, usuario_id):
        notificacao = self.notificacao_repository.buscar_do_usuario(
            id_notificacao,
            usuario_id,
        )
        if notificacao is None:
            raise RecursoNaoEncontrado(
                "Notificação não encontrada."
            )

        if notificacao.marcar_como_lida():
            notificacao = self.notificacao_repository.atualizar(
                notificacao
            )

        return notificacao

    def marcar_todas_como_lidas(self, usuario_id):
        return self.notificacao_repository.marcar_todas_lidas(
            usuario_id
        )
