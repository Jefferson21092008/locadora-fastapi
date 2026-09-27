from modulos.auditoria import (
    RegistroAuditoria,
)


CAMPOS_SENSIVEIS = {
    "authorization",
    "senha",
    "senha_atual",
    "senha_hash",
    "nova_senha",
    "token",
    "jwt",
    "secret",
    "api_key",
    "dsn",
}


class AuditoriaService:
    """
    Coordena a criação e consulta dos registros de auditoria.

    A auditoria registra somente metadados seguros. Valores dos
    campos alterados não são persistidos nesta etapa.
    """

    def __init__(
        self,
        auditoria_repository,
    ):
        self.auditoria_repository = (
            auditoria_repository
        )

    @staticmethod
    def _normalizar_campos(
        campos_alterados,
    ):
        resultado = []

        for campo in (
            campos_alterados
            or ()
        ):
            campo = str(
                campo
            ).strip()

            if not campo:
                continue

            campo_lower = campo.lower()

            if any(
                termo in campo_lower
                for termo in CAMPOS_SENSIVEIS
            ):
                continue

            if campo not in resultado:
                resultado.append(
                    campo
                )

        return resultado

    def registrar(
        self,
        *,
        usuario_id,
        usuario,
        role,
        acao,
        recurso,
        recurso_id=None,
        campos_alterados=None,
        request_id=None,
    ):
        registro = RegistroAuditoria(
            id_registro=None,
            usuario_id=usuario_id,
            usuario=usuario,
            role=role,
            acao=acao,
            recurso=recurso,
            recurso_id=recurso_id,
            campos_alterados=(
                self._normalizar_campos(
                    campos_alterados
                )
            ),
            request_id=request_id,
        )

        registro.id = (
            self.auditoria_repository
            .inserir(
                registro
            )
        )

        return registro

    def listar(self):
        return (
            self.auditoria_repository
            .listar()
        )
