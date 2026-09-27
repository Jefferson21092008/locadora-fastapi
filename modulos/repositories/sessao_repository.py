from sqlalchemy import (
    select,
    update,
)

from modulos.models.sessao_model import (
    SessaoModel,
)


class SessaoRepository:
    """
    Persistência das sessões de autenticação.

    O repository recebe somente hashes de refresh token. O valor puro
    existe apenas entre a API e o navegador do usuário.
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
    def _para_dict(
        model,
    ):
        if model is None:
            return None

        return {
            "id": model.id,
            "usuario_id": model.usuario_id,
            "refresh_token_hash": (
                model.refresh_token_hash
            ),
            "expira_em": model.expira_em,
            "revogada": model.revogada,
            "criado_em": model.criado_em,
            "ultimo_uso_em": (
                model.ultimo_uso_em
            ),
            "revogada_em": model.revogada_em,
        }

    def inserir(
        self,
        *,
        usuario_id,
        refresh_token_hash,
        expira_em,
        criado_em,
    ):
        model = SessaoModel(
            usuario_id=usuario_id,
            refresh_token_hash=(
                refresh_token_hash
            ),
            expira_em=expira_em,
            revogada=False,
            criado_em=criado_em,
            ultimo_uso_em=None,
            revogada_em=None,
        )

        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                sessao.add(model)
                sessao.commit()
                sessao.refresh(model)
                return model.id

            except Exception:
                sessao.rollback()
                raise

    def buscar_por_id(
        self,
        id_sessao,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            model = sessao.get(
                SessaoModel,
                id_sessao,
            )
            return self._para_dict(model)

    def buscar_por_hash(
        self,
        refresh_token_hash,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = select(
                SessaoModel
            ).where(
                SessaoModel.refresh_token_hash
                == refresh_token_hash
            )

            model = sessao.scalar(comando)
            return self._para_dict(model)

    def listar_do_usuario(
        self,
        usuario_id,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            comando = (
                select(SessaoModel)
                .where(
                    SessaoModel.usuario_id
                    == usuario_id
                )
                .order_by(
                    SessaoModel.id.desc()
                )
            )

            models = (
                sessao.scalars(comando)
                .all()
            )

            return [
                self._para_dict(model)
                for model in models
            ]

    def rotacionar_token(
        self,
        *,
        id_sessao,
        hash_anterior,
        novo_hash,
        expira_em,
        ultimo_uso_em,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                comando = (
                    update(SessaoModel)
                    .where(
                        SessaoModel.id
                        == id_sessao,
                        SessaoModel.refresh_token_hash
                        == hash_anterior,
                        SessaoModel.revogada
                        .is_(False),
                    )
                    .values(
                        refresh_token_hash=(
                            novo_hash
                        ),
                        expira_em=expira_em,
                        ultimo_uso_em=(
                            ultimo_uso_em
                        ),
                    )
                )

                resultado = sessao.execute(
                    comando
                )
                atualizado = (
                    resultado.rowcount == 1
                )
                sessao.commit()
                return atualizado

            except Exception:
                sessao.rollback()
                raise

    def revogar(
        self,
        *,
        id_sessao,
        usuario_id,
        revogada_em,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                comando = (
                    update(SessaoModel)
                    .where(
                        SessaoModel.id
                        == id_sessao,
                        SessaoModel.usuario_id
                        == usuario_id,
                        SessaoModel.revogada
                        .is_(False),
                    )
                    .values(
                        revogada=True,
                        revogada_em=revogada_em,
                    )
                )

                resultado = sessao.execute(
                    comando
                )
                atualizado = (
                    resultado.rowcount == 1
                )
                sessao.commit()
                return atualizado

            except Exception:
                sessao.rollback()
                raise

    def revogar_por_hash(
        self,
        *,
        refresh_token_hash,
        revogada_em,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                comando = (
                    update(SessaoModel)
                    .where(
                        SessaoModel.refresh_token_hash
                        == refresh_token_hash,
                        SessaoModel.revogada
                        .is_(False),
                    )
                    .values(
                        revogada=True,
                        revogada_em=revogada_em,
                    )
                )

                resultado = sessao.execute(
                    comando
                )
                atualizado = (
                    resultado.rowcount == 1
                )
                sessao.commit()
                return atualizado

            except Exception:
                sessao.rollback()
                raise

    def revogar_todas_do_usuario(
        self,
        *,
        usuario_id,
        revogada_em,
    ):
        with (
            self.banco_sqlalchemy
            .criar_sessao()
        ) as sessao:
            try:
                comando = (
                    update(SessaoModel)
                    .where(
                        SessaoModel.usuario_id
                        == usuario_id,
                        SessaoModel.revogada
                        .is_(False),
                    )
                    .values(
                        revogada=True,
                        revogada_em=revogada_em,
                    )
                )

                resultado = sessao.execute(
                    comando
                )
                total = resultado.rowcount
                sessao.commit()
                return total

            except Exception:
                sessao.rollback()
                raise
