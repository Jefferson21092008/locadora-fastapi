import hashlib

from datetime import (
    datetime,
    timedelta,
)

import pytest

from modulos.excecoes import (
    RegraDeNegocio,
)

from modulos.servicos.recuperacao_senha_service import (
    RecuperacaoSenhaService,
)


class UsuarioFake:
    def __init__(
        self,
        id_usuario=1,
        usuario="lucas123",
        senha="senha123",
        ativo=True,
    ):
        self.id = id_usuario
        self.usuario = usuario
        self.senha = senha
        self.ativo = ativo

        self._senha_hash = (
            f"hash:{senha}"
        )

    def validar_senha(
        self,
        senha,
    ):
        return (
            self.senha
            == senha
        )

    def alterar_senha(
        self,
        nova_senha,
    ):
        self.senha = nova_senha
        self._senha_hash = (
            f"hash:{nova_senha}"
        )

        return (
            True,
            "Senha alterada com sucesso.",
        )

    def to_dict(self):
        return {
            "senha_hash": (
                self._senha_hash
            )
        }


class ClienteFake:
    def __init__(
        self,
        usuario_id=1,
        email="lucas@email.com",
        ativo=True,
    ):
        self.usuario_id = usuario_id
        self.email = email
        self.ativo = ativo


class UsuarioRepositoryFake:
    def __init__(
        self,
        usuario=None,
    ):
        self.usuario = (
            usuario
            or UsuarioFake()
        )

        self.atualizacoes = 0

    def buscar_por_usuario(
        self,
        nome_usuario,
    ):
        if (
            self.usuario is not None
            and self.usuario.usuario
            == nome_usuario
        ):
            return self.usuario

        return None

    def buscar_por_id(
        self,
        id_usuario,
    ):
        if (
            self.usuario is not None
            and self.usuario.id
            == id_usuario
        ):
            return self.usuario

        return None

    def atualizar(
        self,
        usuario,
    ):
        self.atualizacoes += 1


class ClienteRepositoryFake:
    def __init__(
        self,
        cliente=None,
    ):
        self.cliente = (
            cliente
            or ClienteFake()
        )

    def buscar_por_usuario_id(
        self,
        usuario_id,
    ):
        if (
            self.cliente is not None
            and self.cliente.usuario_id
            == usuario_id
        ):
            return self.cliente

        return None


class EmailServiceFake:
    def __init__(self):
        self.envios = []

    def enviar_recuperacao_senha(
        self,
        destinatario,
        token,
    ):
        self.envios.append(
            {
                "destinatario": destinatario,
                "token": token,
            }
        )


class TokenRecuperacaoRepositoryFake:
    def __init__(self):
        self.tokens = {}
        self.proximo_id = 1

    def inserir(
        self,
        usuario_id,
        token_hash,
        expira_em,
        criado_em,
    ):
        id_token = (
            self.proximo_id
        )

        self.proximo_id += 1

        self.tokens[token_hash] = {
            "id": id_token,
            "usuario_id": usuario_id,
            "token_hash": token_hash,
            "expira_em": expira_em,
            "usado": 0,
            "criado_em": criado_em,
            "usado_em": None,
        }

        return id_token

    def buscar_por_hash(
        self,
        token_hash,
    ):
        return self.tokens.get(
            token_hash
        )

    def invalidar_do_usuario(
        self,
        usuario_id,
        usado_em,
    ):
        total = 0

        for registro in (
            self.tokens.values()
        ):
            if (
                registro["usuario_id"]
                == usuario_id
                and not registro["usado"]
            ):
                registro["usado"] = 1
                registro["usado_em"] = (
                    usado_em
                )

                total += 1

        return total

    def marcar_como_usado(
        self,
        id_token,
        usado_em,
    ):
        for registro in (
            self.tokens.values()
        ):
            if (
                registro["id"]
                == id_token
                and not registro["usado"]
            ):
                registro["usado"] = 1
                registro["usado_em"] = (
                    usado_em
                )

                return True

        return False


@pytest.fixture
def componentes():
    usuario_repository = (
        UsuarioRepositoryFake()
    )

    cliente_repository = (
        ClienteRepositoryFake()
    )

    token_repository = (
        TokenRecuperacaoRepositoryFake()
    )

    email_service = (
        EmailServiceFake()
    )

    service = (
        RecuperacaoSenhaService(
            usuario_repository=(
                usuario_repository
            ),
            token_recuperacao_repository=(
                token_repository
            ),
            cliente_repository=(
                cliente_repository
            ),
            email_service=(
                email_service
            ),
        )
    )

    return (
        service,
        usuario_repository,
        cliente_repository,
        token_repository,
        email_service,
    )


def test_solicitar_recuperacao_gera_token(
    componentes,
):
    (
        service,
        _,
        _,
        token_repository,
        email_service,
    ) = componentes

    token = (
        service.solicitar_recuperacao(
            "lucas123"
        )
    )

    assert isinstance(
        token,
        str,
    )

    assert token

    assert len(
        token_repository.tokens
    ) == 1

    assert len(
        email_service.envios
    ) == 1


def test_email_recebe_token_puro(
    componentes,
):
    (
        service,
        _,
        _,
        _,
        email_service,
    ) = componentes

    token = (
        service.solicitar_recuperacao(
            "lucas123"
        )
    )

    envio = (
        email_service.envios[0]
    )

    assert (
        envio["destinatario"]
        == "lucas@email.com"
    )

    assert (
        envio["token"]
        == token
    )


def test_token_puro_nao_e_salvo(
    componentes,
):
    (
        service,
        _,
        _,
        token_repository,
        _,
    ) = componentes

    token = (
        service.solicitar_recuperacao(
            "lucas123"
        )
    )

    hashes_salvos = list(
        token_repository.tokens.keys()
    )

    assert token not in hashes_salvos

    hash_esperado = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    assert (
        hash_esperado
        in hashes_salvos
    )


def test_token_tem_validade_de_15_minutos(
    componentes,
):
    (
        service,
        _,
        _,
        token_repository,
        _,
    ) = componentes

    token = (
        service.solicitar_recuperacao(
            "lucas123"
        )
    )

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    registro = (
        token_repository.tokens[
            token_hash
        ]
    )

    criado_em = datetime.fromisoformat(
        registro["criado_em"]
    )

    expira_em = datetime.fromisoformat(
        registro["expira_em"]
    )

    assert (
        expira_em
        - criado_em
    ) == timedelta(
        minutes=15
    )


def test_usuario_inexistente_nao_gera_token(
    componentes,
):
    (
        service,
        _,
        _,
        token_repository,
        email_service,
    ) = componentes

    token = (
        service.solicitar_recuperacao(
            "naoexiste"
        )
    )

    assert token is None

    assert (
        token_repository.tokens
        == {}
    )

    assert (
        email_service.envios
        == []
    )


def test_nova_solicitacao_invalida_token_anterior(
    componentes,
):
    (
        service,
        _,
        _,
        token_repository,
        _,
    ) = componentes

    token_antigo = (
        service.solicitar_recuperacao(
            "lucas123"
        )
    )

    token_novo = (
        service.solicitar_recuperacao(
            "lucas123"
        )
    )

    hash_antigo = hashlib.sha256(
        token_antigo.encode("utf-8")
    ).hexdigest()

    hash_novo = hashlib.sha256(
        token_novo.encode("utf-8")
    ).hexdigest()

    assert (
        token_repository.tokens[
            hash_antigo
        ]["usado"]
        == 1
    )

    assert (
        token_repository.tokens[
            hash_novo
        ]["usado"]
        == 0
    )


def test_redefinir_senha_com_token_valido(
    componentes,
):
    (
        service,
        usuario_repository,
        _,
        token_repository,
        _,
    ) = componentes

    token = (
        service.solicitar_recuperacao(
            "lucas123"
        )
    )

    mensagem = (
        service.redefinir_senha(
            token=token,
            nova_senha="novaSenha123",
        )
    )

    assert mensagem == (
        "Senha redefinida "
        "com sucesso."
    )

    assert (
        usuario_repository.usuario.senha
        == "novaSenha123"
    )

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    assert (
        token_repository.tokens[
            token_hash
        ]["usado"]
        == 1
    )


def test_token_invalido_e_rejeitado(
    componentes,
):
    (
        service,
        _,
        _,
        _,
        _,
    ) = componentes

    with pytest.raises(
        RegraDeNegocio,
        match=(
            "Token de recuperação "
            "inválido ou expirado"
        ),
    ):
        service.redefinir_senha(
            token="token-invalido",
            nova_senha="novaSenha123",
        )


def test_token_expirado_e_rejeitado(
    componentes,
):
    (
        service,
        _,
        _,
        token_repository,
        _,
    ) = componentes

    token = "token-expirado"

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    agora = datetime.now()

    token_repository.inserir(
        usuario_id=1,
        token_hash=token_hash,
        expira_em=(
            agora
            - timedelta(
                minutes=1
            )
        ).isoformat(
            timespec="seconds"
        ),
        criado_em=(
            agora
            - timedelta(
                minutes=20
            )
        ).isoformat(
            timespec="seconds"
        ),
    )

    with pytest.raises(
        RegraDeNegocio,
        match=(
            "Token de recuperação "
            "inválido ou expirado"
        ),
    ):
        service.redefinir_senha(
            token=token,
            nova_senha="novaSenha123",
        )


def test_token_nao_pode_ser_reutilizado(
    componentes,
):
    (
        service,
        _,
        _,
        _,
        _,
    ) = componentes

    token = (
        service.solicitar_recuperacao(
            "lucas123"
        )
    )

    service.redefinir_senha(
        token=token,
        nova_senha="novaSenha123",
    )

    with pytest.raises(
        RegraDeNegocio,
        match=(
            "Token de recuperação "
            "inválido ou expirado"
        ),
    ):
        service.redefinir_senha(
            token=token,
            nova_senha="outraSenha123",
        )


def test_nova_senha_nao_pode_ser_igual_a_atual(
    componentes,
):
    (
        service,
        _,
        _,
        _,
        _,
    ) = componentes

    token = (
        service.solicitar_recuperacao(
            "lucas123"
        )
    )

    with pytest.raises(
        RegraDeNegocio,
        match=(
            "A nova senha deve ser "
            "diferente da senha atual"
        ),
    ):
        service.redefinir_senha(
            token=token,
            nova_senha="senha123",
        )
