from datetime import (
    datetime,
    timezone,
)


class RegistroAuditoria:
    """
    Representa um registro persistente de auditoria.

    O registro guarda apenas metadados necessários para
    responder quem realizou a ação, qual recurso foi afetado,
    quais campos mudaram e quando a ação ocorreu.
    """

    def __init__(
        self,
        id_registro,
        usuario_id,
        usuario,
        role,
        acao,
        recurso,
        recurso_id=None,
        campos_alterados=None,
        request_id=None,
        criado_em=None,
    ):
        self.id = id_registro
        self.usuario_id = int(
            usuario_id
        )
        self.usuario = str(
            usuario
        ).strip()
        self.role = str(
            getattr(
                role,
                "value",
                role,
            )
        ).strip().lower()
        self.acao = str(
            acao
        ).strip()
        self.recurso = str(
            recurso
        ).strip()

        if recurso_id is None:
            self.recurso_id = None
        else:
            self.recurso_id = str(
                recurso_id
            ).strip()

        self.campos_alterados = tuple(
            str(campo).strip()
            for campo in (
                campos_alterados
                or ()
            )
            if str(campo).strip()
        )

        self.request_id = (
            str(request_id).strip()
            if request_id
            else None
        )

        self.criado_em = (
            criado_em
            or datetime.now(
                timezone.utc
            ).isoformat(
                timespec="seconds"
            )
        )

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "usuario": self.usuario,
            "role": self.role,
            "acao": self.acao,
            "recurso": self.recurso,
            "recurso_id": self.recurso_id,
            "campos_alterados": list(
                self.campos_alterados
            ),
            "request_id": self.request_id,
            "criado_em": self.criado_em,
        }
