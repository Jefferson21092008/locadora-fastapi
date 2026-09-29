import pytest

from modulos.database import BancoSQLAlchemy
from modulos.models import Base, UsuarioModel
from modulos.notificacoes import Notificacao
from modulos.repositories.notificacao_repository import (
    NotificacaoRepository,
)


@pytest.fixture
def ambiente(tmp_path):
    caminho = tmp_path / "notificacoes.db"
    banco = BancoSQLAlchemy(
        f"sqlite:///{caminho.as_posix()}"
    )
    Base.metadata.create_all(banco.engine)

    with banco.criar_sessao() as sessao:
        usuario = UsuarioModel(
            usuario="maria",
            senha_hash="hash",
            role="cliente",
            ativo=True,
            criado_em="2026-09-28T18:00:00+00:00",
        )
        sessao.add(usuario)
        sessao.commit()
        usuario_id = usuario.id

    repository = NotificacaoRepository(banco)

    try:
        yield repository, usuario_id
    finally:
        banco.fechar()


def nova_notificacao(usuario_id, chave="lembrete-1"):
    return Notificacao(
        id_notificacao=0,
        usuario_id=usuario_id,
        tipo="aluguel_vencendo",
        titulo="Devolução hoje",
        mensagem="Seu aluguel vence hoje.",
        chave_deduplicacao=chave,
        referencia_tipo="aluguel",
        referencia_id=20,
    )


def test_repository_insere_sem_duplicar(ambiente):
    repository, usuario_id = ambiente

    primeira, criada = repository.inserir_se_ausente(
        nova_notificacao(usuario_id)
    )
    segunda, criada_novamente = repository.inserir_se_ausente(
        nova_notificacao(usuario_id)
    )

    assert criada is True
    assert criada_novamente is False
    assert primeira.id == segunda.id


def test_repository_consulta_e_marca_lidas(ambiente):
    repository, usuario_id = ambiente
    repository.inserir_se_ausente(
        nova_notificacao(usuario_id, "lembrete-1")
    )
    repository.inserir_se_ausente(
        nova_notificacao(usuario_id, "lembrete-2")
    )

    resultado = repository.consultar_usuario(
        usuario_id,
        pagina=1,
        por_pagina=20,
    )
    assert resultado.total == 2
    assert resultado.resumo["nao_lidas"] == 2

    atualizadas = repository.marcar_todas_lidas(usuario_id)
    resultado = repository.consultar_usuario(
        usuario_id,
        pagina=1,
        por_pagina=20,
        status="lidas",
    )

    assert atualizadas == 2
    assert resultado.total == 2
    assert resultado.resumo["nao_lidas"] == 0
