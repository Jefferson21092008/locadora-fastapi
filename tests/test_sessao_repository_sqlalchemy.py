from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.models import (
    Base,
    UsuarioModel,
)
from modulos.repositories.sessao_repository import (
    SessaoRepository,
)


def criar_repositorio(tmp_path):
    caminho = (
        tmp_path
        / "sessoes.db"
    )
    banco = BancoSQLAlchemy(
        f"sqlite:///{caminho.as_posix()}"
    )
    Base.metadata.create_all(
        banco.engine
    )

    with banco.criar_sessao() as sessao:
        usuario = UsuarioModel(
            usuario="lucas123",
            senha_hash="hash",
            role="cliente",
            ativo=True,
            criado_em="2026-09-27T18:00:00+00:00",
        )
        sessao.add(usuario)
        sessao.commit()
        sessao.refresh(usuario)
        usuario_id = usuario.id

    return (
        banco,
        SessaoRepository(banco),
        usuario_id,
    )


def test_inserir_e_buscar_sessao(tmp_path):
    banco, repository, usuario_id = (
        criar_repositorio(tmp_path)
    )

    try:
        id_sessao = repository.inserir(
            usuario_id=usuario_id,
            refresh_token_hash="a" * 64,
            expira_em="2026-10-04T18:00:00+00:00",
            criado_em="2026-09-27T18:00:00+00:00",
        )

        registro = repository.buscar_por_id(
            id_sessao
        )

        assert registro["usuario_id"] == usuario_id
        assert registro["revogada"] is False
        assert (
            registro["refresh_token_hash"]
            == "a" * 64
        )

    finally:
        banco.fechar()


def test_rotacao_invalida_hash_anterior(tmp_path):
    banco, repository, usuario_id = (
        criar_repositorio(tmp_path)
    )

    try:
        id_sessao = repository.inserir(
            usuario_id=usuario_id,
            refresh_token_hash="a" * 64,
            expira_em="2026-10-04T18:00:00+00:00",
            criado_em="2026-09-27T18:00:00+00:00",
        )

        atualizado = repository.rotacionar_token(
            id_sessao=id_sessao,
            hash_anterior="a" * 64,
            novo_hash="b" * 64,
            expira_em="2026-10-04T19:00:00+00:00",
            ultimo_uso_em="2026-09-27T19:00:00+00:00",
        )

        assert atualizado is True
        assert repository.buscar_por_hash(
            "a" * 64
        ) is None
        assert repository.buscar_por_hash(
            "b" * 64
        )["id"] == id_sessao

    finally:
        banco.fechar()


def test_revogar_todas_sessoes_do_usuario(tmp_path):
    banco, repository, usuario_id = (
        criar_repositorio(tmp_path)
    )

    try:
        for caractere in ("a", "b"):
            repository.inserir(
                usuario_id=usuario_id,
                refresh_token_hash=(
                    caractere * 64
                ),
                expira_em="2026-10-04T18:00:00+00:00",
                criado_em="2026-09-27T18:00:00+00:00",
            )

        total = (
            repository
            .revogar_todas_do_usuario(
                usuario_id=usuario_id,
                revogada_em=(
                    "2026-09-27T19:00:00+00:00"
                ),
            )
        )

        assert total == 2
        assert all(
            sessao["revogada"]
            for sessao in (
                repository
                .listar_do_usuario(
                    usuario_id
                )
            )
        )

    finally:
        banco.fechar()
