from modulos.usuarios import Role


class AdminService:
    def __init__(
        self,
        auth_service,
    ):
        self.auth_service = auth_service

    def autenticar(
        self,
        usuario,
        senha,
    ):
        return (
            self.auth_service
            .autenticar(
                nome_usuario=usuario,
                senha=senha,
                role=Role.ADMIN,
            )
        )

    def alterar_senha(
        self,
        usuario,
        senha_atual,
        nova_senha,
    ):
        return (
            self.auth_service
            .alterar_senha(
                nome_usuario=usuario,
                senha_atual=senha_atual,
                nova_senha=nova_senha,
                role=Role.ADMIN,
            )
        )