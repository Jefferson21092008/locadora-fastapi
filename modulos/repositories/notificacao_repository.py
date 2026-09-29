from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from modulos.consultas import ResultadoPaginado
from modulos.models.notificacao_model import NotificacaoModel
from modulos.notificacoes import Notificacao


class NotificacaoRepository:
    def __init__(self, banco_sqlalchemy):
        if banco_sqlalchemy is None:
            raise ValueError("BancoSQLAlchemy é obrigatório.")

        self.banco_sqlalchemy = banco_sqlalchemy

    @staticmethod
    def _para_entidade(model):
        if model is None:
            return None

        return Notificacao.from_dict(
            {
                "id": model.id,
                "usuario_id": model.usuario_id,
                "tipo": model.tipo,
                "titulo": model.titulo,
                "mensagem": model.mensagem,
                "chave_deduplicacao": model.chave_deduplicacao,
                "referencia_tipo": model.referencia_tipo,
                "referencia_id": model.referencia_id,
                "lida": model.lida,
                "criada_em": model.criada_em,
                "lida_em": model.lida_em,
                "email_destinatario": model.email_destinatario,
                "email_status": model.email_status,
                "email_enviado_em": model.email_enviado_em,
            }
        )

    def buscar_por_chave(self, chave):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.scalar(
                select(NotificacaoModel).where(
                    NotificacaoModel.chave_deduplicacao == chave
                )
            )
            return self._para_entidade(model)

    def buscar_do_usuario(self, id_notificacao, usuario_id):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.scalar(
                select(NotificacaoModel).where(
                    NotificacaoModel.id == id_notificacao,
                    NotificacaoModel.usuario_id == usuario_id,
                )
            )
            return self._para_entidade(model)

    def inserir_se_ausente(self, notificacao):
        existente = self.buscar_por_chave(
            notificacao.chave_deduplicacao
        )
        if existente is not None:
            return existente, False

        dados = notificacao.to_dict()
        model = NotificacaoModel(
            usuario_id=dados["usuario_id"],
            tipo=dados["tipo"],
            titulo=dados["titulo"],
            mensagem=dados["mensagem"],
            chave_deduplicacao=dados["chave_deduplicacao"],
            referencia_tipo=dados["referencia_tipo"],
            referencia_id=dados["referencia_id"],
            lida=dados["lida"],
            criada_em=dados["criada_em"],
            lida_em=dados["lida_em"],
            email_destinatario=dados["email_destinatario"],
            email_status=dados["email_status"],
            email_enviado_em=dados["email_enviado_em"],
        )

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            try:
                sessao.add(model)
                sessao.commit()
                sessao.refresh(model)
                return self._para_entidade(model), True
            except IntegrityError:
                sessao.rollback()

        existente = self.buscar_por_chave(
            notificacao.chave_deduplicacao
        )
        if existente is None:
            raise RuntimeError("Não foi possível persistir a notificação.")

        return existente, False

    def atualizar(self, notificacao):
        dados = notificacao.to_dict()

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            model = sessao.get(
                NotificacaoModel,
                dados["id"],
            )
            if model is None:
                return None

            model.lida = dados["lida"]
            model.lida_em = dados["lida_em"]
            model.email_status = dados["email_status"]
            model.email_enviado_em = dados["email_enviado_em"]
            sessao.commit()
            sessao.refresh(model)
            return self._para_entidade(model)

    def marcar_todas_lidas(self, usuario_id):
        agora = datetime.now(timezone.utc).isoformat()

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            resultado = sessao.execute(
                update(NotificacaoModel)
                .where(
                    NotificacaoModel.usuario_id == usuario_id,
                    NotificacaoModel.lida.is_(False),
                )
                .values(
                    lida=True,
                    lida_em=agora,
                )
            )
            sessao.commit()
            return int(resultado.rowcount or 0)

    def consultar_usuario(
        self,
        usuario_id,
        pagina=1,
        por_pagina=20,
        status="todas",
    ):
        filtros_base = [
            NotificacaoModel.usuario_id == usuario_id,
        ]
        filtros = list(filtros_base)

        if status == "nao_lidas":
            filtros.append(
                NotificacaoModel.lida.is_(False)
            )
        elif status == "lidas":
            filtros.append(
                NotificacaoModel.lida.is_(True)
            )

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            total = int(
                sessao.scalar(
                    select(func.count(NotificacaoModel.id)).where(*filtros)
                )
                or 0
            )

            models = sessao.scalars(
                select(NotificacaoModel)
                .where(*filtros)
                .order_by(
                    NotificacaoModel.criada_em.desc(),
                    NotificacaoModel.id.desc(),
                )
                .offset((pagina - 1) * por_pagina)
                .limit(por_pagina)
            ).all()

            total_geral = int(
                sessao.scalar(
                    select(func.count(NotificacaoModel.id)).where(*filtros_base)
                )
                or 0
            )
            nao_lidas = int(
                sessao.scalar(
                    select(func.count(NotificacaoModel.id)).where(
                        *filtros_base,
                        NotificacaoModel.lida.is_(False),
                    )
                )
                or 0
            )

        return ResultadoPaginado(
            items=[self._para_entidade(model) for model in models],
            total=total,
            resumo={
                "total": total_geral,
                "nao_lidas": nao_lidas,
                "lidas": max(total_geral - nao_lidas, 0),
            },
        )
