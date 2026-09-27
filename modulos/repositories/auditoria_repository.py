import json

from sqlalchemy import (
    select,
)

from modulos.auditoria import (
    RegistroAuditoria,
)
from modulos.models.audit_log_model import (
    AuditLogModel,
)


class AuditoriaRepository:
    """
    Repository append-only dos registros de auditoria.

    A API não expõe operações de atualização ou exclusão para
    audit_logs. Cada ação gera um novo registro persistente.
    """

    def __init__(
        self,
        banco_sqlalchemy,
    ):
        if banco_sqlalchemy is None:
            raise ValueError(
                "BancoSQLAlchemy é obrigatório."
            )

        self.banco_sqlalchemy = (
            banco_sqlalchemy
        )

    @staticmethod
    def _para_entidade(
        model,
    ):
        if model is None:
            return None

        campos = []

        if model.campos_alterados:
            campos = json.loads(
                model.campos_alterados
            )

        return RegistroAuditoria(
            id_registro=model.id,
            usuario_id=model.usuario_id,
            usuario=model.usuario,
            role=model.role,
            acao=model.acao,
            recurso=model.recurso,
            recurso_id=model.recurso_id,
            campos_alterados=campos,
            request_id=model.request_id,
            criado_em=model.criado_em,
        )

    def inserir(
        self,
        registro,
    ):
        dados = registro.to_dict()

        campos_json = None

        if dados["campos_alterados"]:
            campos_json = json.dumps(
                dados["campos_alterados"],
                ensure_ascii=False,
                separators=(",", ":"),
            )

        model = AuditLogModel(
            usuario_id=dados["usuario_id"],
            usuario=dados["usuario"],
            role=dados["role"],
            acao=dados["acao"],
            recurso=dados["recurso"],
            recurso_id=dados["recurso_id"],
            campos_alterados=campos_json,
            request_id=dados["request_id"],
            criado_em=dados["criado_em"],
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                sessao.add(
                    model
                )
                sessao.commit()
                sessao.refresh(
                    model
                )

                return model.id

            except Exception:
                sessao.rollback()
                raise

    def listar(self):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(
                    AuditLogModel
                )
                .order_by(
                    AuditLogModel.id.desc()
                )
            )

            models = (
                sessao.scalars(
                    comando
                )
                .all()
            )

            return [
                self._para_entidade(
                    model
                )
                for model in models
            ]
