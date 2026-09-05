from modulos.container import (
    Container,
)
from modulos.database import (
    BancoSQLAlchemy,
)
from modulos.models import (
    Base,
)
from modulos.usuarios import (
    Role,
)


class ConfiguracaoFake:
    admin_usuario = "admin"
    admin_senha = "admin123"

    email_configurado = False
    email_smtp_host = None
    email_smtp_port = 587
    email_usuario = None
    email_senha = None
    email_remetente = None


def test_container_entrega_sqlalchemy_a_todos_repositories(
    tmp_path,
):
    caminho = (
        tmp_path
        / "container_sqlalchemy.db"
    )

    banco = BancoSQLAlchemy(
        f"sqlite:///{caminho.as_posix()}"
    )

    Base.metadata.create_all(
        banco.engine
    )

    try:
        container = Container(
            config=ConfiguracaoFake(),
            banco_sqlalchemy=banco,
        )

        repositories = [
            container.usuario_repository,
            container.token_recuperacao_repository,
            container.cliente_repository,
            container.veiculo_repository,
            container.aluguel_repository,
            container.manutencao_repository,
            container.relatorio_repository,
        ]

        assert all(
            repository.banco_sqlalchemy
            is banco
            for repository in repositories
        )

        admin = (
            container.auth_service
            .buscar_por_usuario(
                "admin"
            )
        )

        assert admin is not None
        assert admin.role == Role.ADMIN
        assert admin.id == 1

    finally:
        banco.fechar()
