import inspect as inspect_python

from sqlalchemy import inspect

from modulos.container import (
    Container,
)
from modulos.usuarios import (
    Role,
)


class ConfiguracaoSQLAlchemyFake:
    admin_usuario = "admin"
    admin_senha = "admin123"

    email_configurado = False
    email_smtp_host = None
    email_smtp_port = 587
    email_usuario = None
    email_senha = None
    email_remetente = None

    def __init__(
        self,
        database_url,
    ):
        self.database_url = database_url


def criar_container_sqlalchemy(
    tmp_path,
):
    caminho = (
        tmp_path
        / "locadora_sqlalchemy.db"
    )

    config = ConfiguracaoSQLAlchemyFake(
        f"sqlite:///{caminho.as_posix()}"
    )

    return Container(
        config=config
    )


def test_container_nao_possui_estado_da_persistencia_antiga(
    tmp_path,
):
    container = criar_container_sqlalchemy(
        tmp_path
    )

    try:
        atributos_legados = (
            "dados",
            "clientes",
            "veiculos",
            "alugueis",
            "manutencoes",
            "usuarios",
        )

        assert all(
            not hasattr(
                container,
                atributo,
            )
            for atributo in atributos_legados
        )

    finally:
        container.banco_sqlalchemy.fechar()


def test_container_nao_aceita_dados_no_construtor():
    parametros = (
        inspect_python
        .signature(Container)
        .parameters
    )

    assert "dados" not in parametros


def test_container_aplica_migrations_automaticamente(
    tmp_path,
):
    container = criar_container_sqlalchemy(
        tmp_path
    )

    try:
        tabelas = set(
            inspect(
                container.banco_sqlalchemy.engine
            ).get_table_names()
        )

        assert {
            "usuarios",
            "clientes",
            "veiculos",
            "alugueis",
            "manutencoes",
            "tokens_recuperacao_senha",
        }.issubset(
            tabelas
        )

    finally:
        container.banco_sqlalchemy.fechar()


def test_container_cria_admin_sem_persistencia_antiga(
    tmp_path,
):
    container = criar_container_sqlalchemy(
        tmp_path
    )

    try:
        admin = (
            container.auth_service
            .buscar_por_usuario(
                "admin"
            )
        )

        assert admin is not None
        assert admin.id == 1
        assert admin.role == Role.ADMIN
        assert admin.ativo is True

    finally:
        container.banco_sqlalchemy.fechar()


def test_container_cadastra_cliente_sem_gerenciador_dados(
    tmp_path,
):
    container = criar_container_sqlalchemy(
        tmp_path
    )

    try:
        cliente = (
            container.cliente_service
            .criar_conta(
                nome="Lucas Silva",
                usuario="lucas",
                email="lucas@email.com",
                senha="Senha123",
            )
        )

        encontrado = (
            container.cliente_repository
            .buscar_por_id(
                cliente.id
            )
        )

        conta = (
            container.auth_service
            .buscar_por_usuario(
                "lucas"
            )
        )

        assert encontrado is not None
        assert encontrado.usuario == "lucas"
        assert conta is not None
        assert conta.role == Role.CLIENTE

    finally:
        container.banco_sqlalchemy.fechar()


def test_container_cadastra_veiculo_sem_gerenciador_dados(
    tmp_path,
):
    container = criar_container_sqlalchemy(
        tmp_path
    )

    try:
        veiculo = (
            container.veiculo_service
            .cadastrar(
                tipo="carro",
                modelo="Onix",
                ano=2025,
                diaria=150,
                preco_km=2,
            )
        )

        encontrado = (
            container.veiculo_service
            .buscar_por_id(
                veiculo.id
            )
        )

        assert encontrado is not None
        assert encontrado.modelo == "Onix"

    finally:
        container.banco_sqlalchemy.fechar()
