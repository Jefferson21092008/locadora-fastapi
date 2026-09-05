from sqlalchemy import (
    select,
    update,
)

from modulos.models.token_recuperacao_model import (
    TokenRecuperacaoModel,
)


class TokenRecuperacaoRepository:
    """
    Repository dos tokens de recuperação de senha.

    SQLAlchemy é a única fonte de persistência.
    O token original nunca é armazenado aqui;
    somente o hash recebido pelo Service.
    """

    def __init__(
        self,
        banco_sqlalchemy,
    ):
        self.banco_sqlalchemy = (
            banco_sqlalchemy
        )

    # ================================================================
    # MAPEAMENTO MODEL -> DICIONÁRIO
    # ================================================================

    @staticmethod
    def _para_dict(
        model,
    ):
        if model is None:
            return None

        return {
            "id": model.id,
            "usuario_id": model.usuario_id,
            "token_hash": model.token_hash,
            "expira_em": model.expira_em,
            "usado": model.usado,
            "criado_em": model.criado_em,
            "usado_em": model.usado_em,
        }

    # ================================================================
    # INSERÇÃO
    # ================================================================

    def inserir(
        self,
        usuario_id,
        token_hash,
        expira_em,
        criado_em,
    ):
        model = TokenRecuperacaoModel(
            usuario_id=usuario_id,
            token_hash=token_hash,
            expira_em=expira_em,
            usado=False,
            criado_em=criado_em,
            usado_em=None,
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

    # ================================================================
    # BUSCA
    # ================================================================

    def buscar_por_hash(
        self,
        token_hash,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = select(
                TokenRecuperacaoModel
            ).where(
                TokenRecuperacaoModel.token_hash
                == token_hash
            )

            model = sessao.scalar(
                comando
            )

            return self._para_dict(
                model
            )

    # ================================================================
    # INVALIDAÇÃO
    # ================================================================

    def invalidar_do_usuario(
        self,
        usuario_id,
        usado_em,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                comando = (
                    update(
                        TokenRecuperacaoModel
                    )
                    .where(
                        TokenRecuperacaoModel.usuario_id
                        == usuario_id,
                        TokenRecuperacaoModel.usado
                        .is_(False),
                    )
                    .values(
                        usado=True,
                        usado_em=usado_em,
                    )
                )

                resultado = sessao.execute(
                    comando
                )

                total_invalidados = (
                    resultado.rowcount
                )

                sessao.commit()

                return total_invalidados

            except Exception:
                sessao.rollback()
                raise

    def marcar_como_usado(
        self,
        id_token,
        usado_em,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                comando = (
                    update(
                        TokenRecuperacaoModel
                    )
                    .where(
                        TokenRecuperacaoModel.id
                        == id_token,
                        TokenRecuperacaoModel.usado
                        .is_(False),
                    )
                    .values(
                        usado=True,
                        usado_em=usado_em,
                    )
                )

                resultado = sessao.execute(
                    comando
                )

                atualizado = (
                    resultado.rowcount
                    == 1
                )

                sessao.commit()

                return atualizado

            except Exception:
                sessao.rollback()
                raise
