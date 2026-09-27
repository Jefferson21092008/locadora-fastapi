import hashlib

from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from modulos.excecoes import (
    RegraDeNegocio,
)
from modulos.servicos.sessao_service import (
    SessaoService,
)


class SessaoRepositoryFake:
    def __init__(self):
        self.sessoes = {}
        self.proximo_id = 1

    def inserir(
        self,
        *,
        usuario_id,
        refresh_token_hash,
        expira_em,
        criado_em,
    ):
        id_sessao = self.proximo_id
        self.proximo_id += 1
        self.sessoes[id_sessao] = {
            "id": id_sessao,
            "usuario_id": usuario_id,
            "refresh_token_hash": refresh_token_hash,
            "expira_em": expira_em,
            "revogada": False,
            "criado_em": criado_em,
            "ultimo_uso_em": None,
            "revogada_em": None,
        }
        return id_sessao

    def buscar_por_id(self, id_sessao):
        registro = self.sessoes.get(
            id_sessao
        )
        return (
            dict(registro)
            if registro is not None
            else None
        )

    def buscar_por_hash(
        self,
        refresh_token_hash,
    ):
        for registro in self.sessoes.values():
            if (
                registro["refresh_token_hash"]
                == refresh_token_hash
            ):
                return dict(registro)
        return None

    def listar_do_usuario(self, usuario_id):
        return [
            dict(registro)
            for registro in self.sessoes.values()
            if registro["usuario_id"] == usuario_id
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
        registro = self.sessoes.get(
            id_sessao
        )
        if (
            registro is None
            or registro["revogada"]
            or registro["refresh_token_hash"]
            != hash_anterior
        ):
            return False

        registro["refresh_token_hash"] = novo_hash
        registro["expira_em"] = expira_em
        registro["ultimo_uso_em"] = ultimo_uso_em
        return True

    def revogar(
        self,
        *,
        id_sessao,
        usuario_id,
        revogada_em,
    ):
        registro = self.sessoes.get(
            id_sessao
        )
        if (
            registro is None
            or registro["usuario_id"] != usuario_id
            or registro["revogada"]
        ):
            return False

        registro["revogada"] = True
        registro["revogada_em"] = revogada_em
        return True

    def revogar_por_hash(
        self,
        *,
        refresh_token_hash,
        revogada_em,
    ):
        registro = self.buscar_por_hash(
            refresh_token_hash
        )
        if registro is None:
            return False
        return self.revogar(
            id_sessao=registro["id"],
            usuario_id=registro["usuario_id"],
            revogada_em=revogada_em,
        )

    def revogar_todas_do_usuario(
        self,
        *,
        usuario_id,
        revogada_em,
    ):
        total = 0
        for registro in self.sessoes.values():
            if (
                registro["usuario_id"]
                == usuario_id
                and not registro["revogada"]
            ):
                registro["revogada"] = True
                registro["revogada_em"] = revogada_em
                total += 1
        return total


@pytest.fixture
def componentes():
    repository = SessaoRepositoryFake()
    service = SessaoService(repository)
    return service, repository


def test_criar_sessao_salva_apenas_hash(
    componentes,
):
    service, repository = componentes

    sessao = service.criar(
        usuario_id=7
    )

    registro = repository.sessoes[
        sessao["id"]
    ]

    assert sessao["refresh_token"] not in str(
        registro
    )
    assert (
        registro["refresh_token_hash"]
        == hashlib.sha256(
            sessao["refresh_token"].encode(
                "utf-8"
            )
        ).hexdigest()
    )


def test_renovar_rotaciona_refresh_token(
    componentes,
):
    service, repository = componentes
    criada = service.criar(1)
    token_anterior = criada[
        "refresh_token"
    ]

    renovada = service.renovar(
        token_anterior
    )

    assert (
        renovada["refresh_token"]
        != token_anterior
    )
    assert repository.buscar_por_hash(
        hashlib.sha256(
            token_anterior.encode("utf-8")
        ).hexdigest()
    ) is None


def test_refresh_token_antigo_nao_pode_ser_reutilizado(
    componentes,
):
    service, _ = componentes
    criada = service.criar(1)
    token_anterior = criada[
        "refresh_token"
    ]

    service.renovar(
        token_anterior
    )

    with pytest.raises(
        RegraDeNegocio,
        match="Sessão inválida ou expirada",
    ):
        service.renovar(
            token_anterior
        )


def test_sessao_expirada_e_rejeitada(
    componentes,
):
    service, repository = componentes
    criada = service.criar(1)
    registro = repository.sessoes[
        criada["id"]
    ]
    registro["expira_em"] = (
        datetime.now(timezone.utc)
        - timedelta(seconds=1)
    ).isoformat(timespec="seconds")

    assert service.esta_ativa(
        criada["id"],
        1,
    ) is False
    assert registro["revogada"] is True


def test_revogar_por_token_invalida_sessao(
    componentes,
):
    service, _ = componentes
    criada = service.criar(1)

    assert service.revogar_por_token(
        criada["refresh_token"]
    ) is True
    assert service.esta_ativa(
        criada["id"],
        1,
    ) is False
