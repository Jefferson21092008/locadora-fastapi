from types import (
    SimpleNamespace,
)

import pytest

from fastapi.testclient import (
    TestClient,
)

from api.auditoria import (
    registrar_auditoria,
)
from api.dependencias import (
    get_container,
)
from api.main import app
from api.seguranca import (
    criar_token_acesso,
)
from modulos.auditoria import (
    RegistroAuditoria,
)
from modulos.container import (
    Container,
)
from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.models.usuario_model import (
    UsuarioModel,
)
from modulos.repositories.auditoria_repository import (
    AuditoriaRepository,
)
from modulos.servicos.auditoria_service import (
    AuditoriaService,
)
from modulos.usuarios import (
    Role,
)


JWT_SECRET_TESTE = (
    "locadora-jwt-chave-auditoria-1234567890"
)


class ConfiguracaoFake:
    admin_usuario = "admin"
    admin_senha = "Admin123"
    jwt_secret = JWT_SECRET_TESTE
    email_configurado = False
    public_url = "http://127.0.0.1:8000"
    brevo_api_key = None
    email_remetente = None

    def __init__(
        self,
        database_url,
    ):
        self.database_url = database_url


@pytest.fixture
def container_real(tmp_path):
    caminho = (
        tmp_path
        / "auditoria.db"
    )

    container = Container(
        config=ConfiguracaoFake(
            f"sqlite:///{caminho.as_posix()}"
        )
    )

    try:
        yield container

    finally:
        container.banco_sqlalchemy.fechar()


def test_registro_auditoria_serializa_metadados():
    registro = RegistroAuditoria(
        id_registro=10,
        usuario_id=3,
        usuario="admin",
        role=Role.ADMIN,
        acao="veiculo.editado",
        recurso="veiculo",
        recurso_id=7,
        campos_alterados=(
            "modelo",
            "diaria",
        ),
        request_id="req-123",
        criado_em="2026-09-27T20:00:00+00:00",
    )

    assert registro.to_dict() == {
        "id": 10,
        "usuario_id": 3,
        "usuario": "admin",
        "role": "admin",
        "acao": "veiculo.editado",
        "recurso": "veiculo",
        "recurso_id": "7",
        "campos_alterados": [
            "modelo",
            "diaria",
        ],
        "request_id": "req-123",
        "criado_em": "2026-09-27T20:00:00+00:00",
    }


def test_auditoria_service_remove_campos_sensiveis():
    class RepositoryFake:
        def __init__(self):
            self.registro = None

        def inserir(
            self,
            registro,
        ):
            self.registro = registro
            return 5

    repository = RepositoryFake()
    service = AuditoriaService(
        auditoria_repository=repository
    )

    registro = service.registrar(
        usuario_id=1,
        usuario="admin",
        role="admin",
        acao="conta.alterada",
        recurso="usuario",
        recurso_id=1,
        campos_alterados=(
            "usuario",
            "senha",
            "token",
            "authorization_header",
            "usuario",
        ),
        request_id="req-safe",
    )

    assert registro.id == 5
    assert list(
        registro.campos_alterados
    ) == [
        "usuario"
    ]


def test_auditoria_repository_persiste_e_lista_em_ordem(
    tmp_path,
):
    caminho = (
        tmp_path
        / "repo_auditoria.db"
    )

    banco = BancoSQLAlchemy(
        f"sqlite:///{caminho.as_posix()}"
    )
    banco.aplicar_migrations()

    try:
        with banco.criar_sessao() as sessao:
            usuario = UsuarioModel(
                usuario="admin",
                senha_hash="hash",
                role="admin",
                ativo=True,
                criado_em="2026-09-27T18:00:00",
            )
            sessao.add(usuario)
            sessao.commit()
            sessao.refresh(usuario)
            usuario_id = usuario.id

        repository = AuditoriaRepository(
            banco_sqlalchemy=banco
        )
        service = AuditoriaService(
            auditoria_repository=repository
        )

        primeiro = service.registrar(
            usuario_id=usuario_id,
            usuario="admin",
            role="admin",
            acao="veiculo.cadastrado",
            recurso="veiculo",
            recurso_id=1,
            campos_alterados=(
                "modelo",
            ),
            request_id="req-1",
        )
        segundo = service.registrar(
            usuario_id=usuario_id,
            usuario="admin",
            role="admin",
            acao="veiculo.desativado",
            recurso="veiculo",
            recurso_id=1,
            campos_alterados=(
                "ativo",
            ),
            request_id="req-2",
        )

        registros = repository.listar()

        assert primeiro.id is not None
        assert segundo.id is not None
        assert [
            registro.acao
            for registro in registros
        ] == [
            "veiculo.desativado",
            "veiculo.cadastrado",
        ]
        assert registros[0].request_id == "req-2"

    finally:
        banco.fechar()


def test_auditoria_repository_exige_banco():
    with pytest.raises(
        ValueError,
        match="BancoSQLAlchemy é obrigatório.",
    ):
        AuditoriaRepository(
            banco_sqlalchemy=None
        )


def test_operacao_admin_cria_auditoria_com_request_id(
    container_real,
):
    admin = (
        container_real.auth_service
        .buscar_por_usuario(
            "admin"
        )
    )

    token = criar_token_acesso(
        usuario=admin,
        secret=JWT_SECRET_TESTE,
    )

    app.dependency_overrides[
        get_container
    ] = lambda: container_real

    try:
        with TestClient(app) as client:
            resposta = client.post(
                "/veiculos",
                headers={
                    "Authorization": (
                        f"Bearer {token}"
                    )
                },
                json={
                    "tipo": "carro",
                    "modelo": "Corolla",
                    "ano": 2026,
                    "diaria": 180.0,
                    "preco_km": 1.5,
                },
            )

            assert resposta.status_code == 201

            request_id = resposta.headers[
                "X-Request-ID"
            ]

            auditoria = client.get(
                "/auditoria",
                headers={
                    "Authorization": (
                        f"Bearer {token}"
                    )
                },
            )

        assert auditoria.status_code == 200

        registro = auditoria.json()[0]

        assert registro["usuario"] == "admin"
        assert registro["role"] == "admin"
        assert registro["acao"] == "veiculo.cadastrado"
        assert registro["recurso"] == "veiculo"
        assert registro["request_id"] == request_id
        assert "senha" not in registro["campos_alterados"]

    finally:
        app.dependency_overrides.clear()


def test_cliente_nao_pode_listar_auditoria(
    container_real,
):
    usuario = (
        container_real.auth_service
        .criar_usuario(
            nome_usuario="cliente1",
            senha="Senha123",
            role=Role.CLIENTE,
        )
    )

    token = criar_token_acesso(
        usuario=usuario,
        secret=JWT_SECRET_TESTE,
    )

    app.dependency_overrides[
        get_container
    ] = lambda: container_real

    try:
        with TestClient(app) as client:
            resposta = client.get(
                "/auditoria",
                headers={
                    "Authorization": (
                        f"Bearer {token}"
                    )
                },
            )

        assert resposta.status_code == 403

    finally:
        app.dependency_overrides.clear()


def test_falha_na_auditoria_nao_muda_resultado_da_operacao(
    monkeypatch,
):
    class AuditoriaFalha:
        def registrar(
            self,
            **kwargs,
        ):
            raise RuntimeError(
                "falha simulada"
            )

    request = SimpleNamespace(
        state=SimpleNamespace(
            request_id="req-falha"
        )
    )
    container = SimpleNamespace(
        auditoria_service=AuditoriaFalha()
    )
    ator = SimpleNamespace(
        id=1,
        usuario="admin",
        role=SimpleNamespace(
            value="admin"
        ),
    )

    monkeypatch.setattr(
        "api.auditoria.sentry_sdk.is_initialized",
        lambda: False,
    )

    resultado = registrar_auditoria(
        request=request,
        container=container,
        ator=ator,
        acao="veiculo.editado",
        recurso="veiculo",
        recurso_id=1,
        campos_alterados=(
            "modelo",
        ),
    )

    assert resultado is None
