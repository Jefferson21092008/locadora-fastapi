import hashlib
import secrets

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from modulos.excecoes import (
    RegraDeNegocio,
)


MENSAGEM_SESSAO_INVALIDA = (
    "Sessão inválida ou expirada."
)


class SessaoService:
    """
    Gerencia sessões persistentes e refresh tokens rotativos.

    O refresh token puro é entregue ao navegador em cookie HttpOnly.
    Somente seu hash SHA-256 é persistido no banco.
    """

    VALIDADE_REFRESH_DIAS = 7
    TAMANHO_TOKEN_BYTES = 48

    def __init__(
        self,
        sessao_repository,
    ):
        if sessao_repository is None:
            raise ValueError(
                "SessaoRepository é obrigatório."
            )

        self.sessao_repository = (
            sessao_repository
        )

    @classmethod
    def validade_refresh_segundos(
        cls,
    ):
        return (
            cls.VALIDADE_REFRESH_DIAS
            * 24
            * 60
            * 60
        )

    @staticmethod
    def _agora():
        return datetime.now(
            timezone.utc
        )

    @staticmethod
    def _hash_token(
        token,
    ):
        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    @classmethod
    def _gerar_token(cls):
        return secrets.token_urlsafe(
            cls.TAMANHO_TOKEN_BYTES
        )

    @classmethod
    def _expiracao(cls, agora):
        return (
            agora
            + timedelta(
                days=(
                    cls.VALIDADE_REFRESH_DIAS
                )
            )
        )

    @staticmethod
    def _normalizar_token(
        token,
    ):
        if token is None:
            return ""

        return str(token).strip()

    @staticmethod
    def _data_expiracao(
        registro,
    ):
        try:
            expira_em = datetime.fromisoformat(
                registro["expira_em"]
            )

        except (
            TypeError,
            ValueError,
            KeyError,
        ) as erro:
            raise RegraDeNegocio(
                MENSAGEM_SESSAO_INVALIDA
            ) from erro

        if expira_em.tzinfo is None:
            expira_em = expira_em.replace(
                tzinfo=timezone.utc
            )

        return expira_em

    def criar(
        self,
        usuario_id,
    ):
        agora = self._agora()
        token = self._gerar_token()
        token_hash = self._hash_token(
            token
        )
        expira_em = self._expiracao(
            agora
        )

        id_sessao = (
            self.sessao_repository
            .inserir(
                usuario_id=usuario_id,
                refresh_token_hash=(
                    token_hash
                ),
                expira_em=(
                    expira_em.isoformat(
                        timespec="seconds"
                    )
                ),
                criado_em=(
                    agora.isoformat(
                        timespec="seconds"
                    )
                ),
            )
        )

        return {
            "id": id_sessao,
            "usuario_id": usuario_id,
            "refresh_token": token,
            "expira_em": expira_em.isoformat(
                timespec="seconds"
            ),
        }

    def renovar(
        self,
        refresh_token,
    ):
        refresh_token = (
            self._normalizar_token(
                refresh_token
            )
        )

        if not refresh_token:
            raise RegraDeNegocio(
                MENSAGEM_SESSAO_INVALIDA
            )

        hash_anterior = self._hash_token(
            refresh_token
        )

        registro = (
            self.sessao_repository
            .buscar_por_hash(
                hash_anterior
            )
        )

        if (
            registro is None
            or registro["revogada"]
        ):
            raise RegraDeNegocio(
                MENSAGEM_SESSAO_INVALIDA
            )

        agora = self._agora()
        expira_em = self._data_expiracao(
            registro
        )

        if agora >= expira_em:
            self.sessao_repository.revogar(
                id_sessao=registro["id"],
                usuario_id=(
                    registro["usuario_id"]
                ),
                revogada_em=(
                    agora.isoformat(
                        timespec="seconds"
                    )
                ),
            )

            raise RegraDeNegocio(
                MENSAGEM_SESSAO_INVALIDA
            )

        novo_token = self._gerar_token()
        novo_hash = self._hash_token(
            novo_token
        )
        nova_expiracao = self._expiracao(
            agora
        )
        agora_iso = agora.isoformat(
            timespec="seconds"
        )

        atualizado = (
            self.sessao_repository
            .rotacionar_token(
                id_sessao=registro["id"],
                hash_anterior=hash_anterior,
                novo_hash=novo_hash,
                expira_em=(
                    nova_expiracao.isoformat(
                        timespec="seconds"
                    )
                ),
                ultimo_uso_em=agora_iso,
            )
        )

        if not atualizado:
            raise RegraDeNegocio(
                MENSAGEM_SESSAO_INVALIDA
            )

        return {
            "id": registro["id"],
            "usuario_id": (
                registro["usuario_id"]
            ),
            "refresh_token": novo_token,
            "expira_em": (
                nova_expiracao.isoformat(
                    timespec="seconds"
                )
            ),
            "criado_em": (
                registro["criado_em"]
            ),
            "ultimo_uso_em": agora_iso,
        }

    def esta_ativa(
        self,
        id_sessao,
        usuario_id,
    ):
        registro = (
            self.sessao_repository
            .buscar_por_id(
                id_sessao
            )
        )

        if (
            registro is None
            or registro["usuario_id"]
            != usuario_id
            or registro["revogada"]
        ):
            return False

        agora = self._agora()

        try:
            expira_em = self._data_expiracao(
                registro
            )

        except RegraDeNegocio:
            return False

        if agora >= expira_em:
            self.sessao_repository.revogar(
                id_sessao=registro["id"],
                usuario_id=usuario_id,
                revogada_em=(
                    agora.isoformat(
                        timespec="seconds"
                    )
                ),
            )
            return False

        return True

    def listar_ativas(
        self,
        usuario_id,
    ):
        agora = self._agora()
        ativas = []

        for registro in (
            self.sessao_repository
            .listar_do_usuario(
                usuario_id
            )
        ):
            if registro["revogada"]:
                continue

            try:
                expira_em = (
                    self._data_expiracao(
                        registro
                    )
                )
            except RegraDeNegocio:
                continue

            if agora >= expira_em:
                self.sessao_repository.revogar(
                    id_sessao=registro["id"],
                    usuario_id=usuario_id,
                    revogada_em=(
                        agora.isoformat(
                            timespec="seconds"
                        )
                    ),
                )
                continue

            ativas.append(registro)

        return ativas

    def revogar(
        self,
        id_sessao,
        usuario_id,
    ):
        return (
            self.sessao_repository
            .revogar(
                id_sessao=id_sessao,
                usuario_id=usuario_id,
                revogada_em=(
                    self._agora()
                    .isoformat(
                        timespec="seconds"
                    )
                ),
            )
        )

    def revogar_por_token(
        self,
        refresh_token,
    ):
        refresh_token = (
            self._normalizar_token(
                refresh_token
            )
        )

        if not refresh_token:
            return False

        return (
            self.sessao_repository
            .revogar_por_hash(
                refresh_token_hash=(
                    self._hash_token(
                        refresh_token
                    )
                ),
                revogada_em=(
                    self._agora()
                    .isoformat(
                        timespec="seconds"
                    )
                ),
            )
        )

    def revogar_todas(
        self,
        usuario_id,
    ):
        return (
            self.sessao_repository
            .revogar_todas_do_usuario(
                usuario_id=usuario_id,
                revogada_em=(
                    self._agora()
                    .isoformat(
                        timespec="seconds"
                    )
                ),
            )
        )
