import hashlib
import logging
import secrets

from datetime import (
    datetime,
    timedelta,
)

from modulos.excecoes import (
    RegraDeNegocio,
)

from modulos.usuarios import Usuario


logger = logging.getLogger(
    __name__
)


class RecuperacaoSenhaService:
    """
    Gerencia o fluxo de recuperação
    e redefinição de senha.
    """

    VALIDADE_TOKEN_MINUTOS = 15

    def __init__(
        self,
        usuario_repository,
        token_recuperacao_repository,
        cliente_repository,
        email_service,
    ):
        self.usuario_repository = (
            usuario_repository
        )

        self.token_recuperacao_repository = (
            token_recuperacao_repository
        )

        self.cliente_repository = (
            cliente_repository
        )

        self.email_service = (
            email_service
        )

    # ================================================================
    # HASH DO TOKEN
    # ================================================================

    @staticmethod
    def _gerar_hash_token(
        token,
    ):
        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    # ================================================================
    # SOLICITAÇÃO
    # ================================================================

    def solicitar_recuperacao(
        self,
        nome_usuario,
    ):
        usuario = (
            self.usuario_repository
            .buscar_por_usuario(
                nome_usuario
            )
        )

        # Por segurança, não diferenciamos
        # usuário inexistente de indisponível.
        if (
            usuario is None
            or not usuario.ativo
        ):
            return None

        cliente = (
            self.cliente_repository
            .buscar_por_usuario_id(
                usuario.id
            )
        )

        # Atualmente apenas contas de cliente
        # possuem e-mail associado.
        if (
            cliente is None
            or not cliente.ativo
            or not cliente.email
        ):
            return None

        agora = datetime.now()

        usado_em = agora.isoformat(
            timespec="seconds"
        )

        self.token_recuperacao_repository.invalidar_do_usuario(
            usuario_id=usuario.id,
            usado_em=usado_em,
        )

        token = secrets.token_urlsafe(
            32
        )

        token_hash = (
            self._gerar_hash_token(
                token
            )
        )

        expira_em = (
            agora
            + timedelta(
                minutes=(
                    self.VALIDADE_TOKEN_MINUTOS
                )
            )
        )

        self.token_recuperacao_repository.inserir(
            usuario_id=usuario.id,
            token_hash=token_hash,
            expira_em=expira_em.isoformat(
                timespec="seconds"
            ),
            criado_em=agora.isoformat(
                timespec="seconds"
            ),
        )

        try:
            self.email_service.enviar_recuperacao_senha(
                destinatario=cliente.email,
                token=token,
            )

        except Exception:
            # Se o envio falhar, invalida o token
            # para não deixar um token ativo que
            # nunca chegou ao usuário.
            self.token_recuperacao_repository.invalidar_do_usuario(
                usuario_id=usuario.id,
                usado_em=datetime.now().isoformat(
                    timespec="seconds"
                ),
            )

            # O erro fica nos logs do servidor,
            # mas a API continua com resposta
            # genérica para evitar enumeração.
            logger.exception(
                "Falha ao enviar e-mail "
                "de recuperação de senha."
            )

            return None

        # O token puro nunca é persistido.
        # O retorno continua útil para testes
        # internos do Service.
        return token

    # ================================================================
    # REDEFINIÇÃO
    # ================================================================

    def redefinir_senha(
        self,
        token,
        nova_senha,
    ):
        token = str(
            token
        ).strip()

        if not token:
            raise RegraDeNegocio(
                "Token de recuperação "
                "inválido ou expirado."
            )

        token_hash = (
            self._gerar_hash_token(
                token
            )
        )

        registro = (
            self.token_recuperacao_repository
            .buscar_por_hash(
                token_hash
            )
        )

        if registro is None:
            raise RegraDeNegocio(
                "Token de recuperação "
                "inválido ou expirado."
            )

        if registro["usado"]:
            raise RegraDeNegocio(
                "Token de recuperação "
                "inválido ou expirado."
            )

        agora = datetime.now()

        expira_em = datetime.fromisoformat(
            registro["expira_em"]
        )

        if agora > expira_em:
            raise RegraDeNegocio(
                "Token de recuperação "
                "inválido ou expirado."
            )

        usuario = (
            self.usuario_repository
            .buscar_por_id(
                registro["usuario_id"]
            )
        )

        if (
            usuario is None
            or not usuario.ativo
        ):
            raise RegraDeNegocio(
                "Token de recuperação "
                "inválido ou expirado."
            )

        valido, mensagem = (
            Usuario.validar_nova_senha(
                nova_senha
            )
        )

        if not valido:
            raise RegraDeNegocio(
                mensagem
            )

        if usuario.validar_senha(
            nova_senha
        ):
            raise RegraDeNegocio(
                "A nova senha deve ser "
                "diferente da senha atual."
            )

        hash_anterior = (
            usuario.to_dict()[
                "senha_hash"
            ]
        )

        sucesso, mensagem = (
            usuario.alterar_senha(
                nova_senha
            )
        )

        if not sucesso:
            raise RegraDeNegocio(
                mensagem
            )

        try:
            self.usuario_repository.atualizar(
                usuario
            )

            token_usado = (
                self.token_recuperacao_repository
                .marcar_como_usado(
                    id_token=registro["id"],
                    usado_em=agora.isoformat(
                        timespec="seconds"
                    ),
                )
            )

            if not token_usado:
                raise RuntimeError(
                    "Não foi possível consumir "
                    "o token de recuperação."
                )

        except Exception:
            usuario._senha_hash = (
                hash_anterior
            )

            try:
                self.usuario_repository.atualizar(
                    usuario
                )
            except Exception:
                pass

            raise

        return "Senha redefinida com sucesso."
