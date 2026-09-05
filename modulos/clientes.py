import re


class Cliente:
    """Representa o perfil de um cliente da locadora."""

    def __init__(
        self,
        id_cliente,
        nome,
        usuario,
        email=None,
        ativo=True,
        usuario_id=None,
    ):
        self.id = id_cliente

        self.nome = (
            str(nome)
            .strip()
        )

        self.usuario = (
            str(usuario)
            .strip()
        )

        self.email = (
            str(email or "")
            .strip()
        )

        self.ativo = bool(
            ativo
        )

        self.usuario_id = (
            usuario_id
        )

    # ================================================================
    # VALIDAÇÕES
    # ================================================================

    def validar_dados(self):
        if not self.nome:
            return (
                False,
                "O nome não pode ficar vazio.",
            )

        if len(self.nome) < 3:
            return (
                False,
                "O nome deve possuir "
                "pelo menos 3 caracteres.",
            )

        if not self.usuario:
            return (
                False,
                "O usuário não pode "
                "ficar vazio.",
            )

        if len(self.usuario) < 3:
            return (
                False,
                "O usuário deve possuir "
                "pelo menos 3 caracteres.",
            )

        if not self.email:
            return (
                False,
                "O e-mail não pode "
                "ficar vazio.",
            )

        if not self.validar_email(
            self.email
        ):
            return (
                False,
                "E-mail inválido.",
            )

        return True, ""

    @staticmethod
    def validar_email(email):
        padrao = (
            r"^[\w.-]+@"
            r"[\w.-]+\."
            r"[a-zA-Z]{2,}$"
        )

        return (
            re.match(
                padrao,
                str(email).strip(),
            )
            is not None
        )

    # ================================================================
    # CRIAÇÃO
    # ================================================================

    @classmethod
    def criar(
        cls,
        id_cliente,
        nome,
        usuario,
        email="",
        usuario_id=None,
    ):
        cliente = cls(
            id_cliente=id_cliente,
            nome=nome,
            usuario=usuario,
            email=email,
            ativo=True,
            usuario_id=usuario_id,
        )

        valido, mensagem = (
            cliente.validar_dados()
        )

        if not valido:
            return (
                None,
                mensagem,
            )

        return (
            cliente,
            "",
        )

    # ================================================================
    # STATUS DO PERFIL
    # ================================================================

    def desativar(self):
        if not self.ativo:
            return (
                False,
                "A conta já está desativada.",
            )

        self.ativo = False

        return (
            True,
            "Conta desativada "
            "com sucesso.",
        )

    def reativar(self):
        if self.ativo:
            return (
                False,
                "A conta já está ativa.",
            )

        self.ativo = True

        return (
            True,
            "Conta reativada "
            "com sucesso.",
        )

    # ================================================================
    # SERIALIZAÇÃO
    # ================================================================

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "usuario": self.usuario,
            "email": self.email,
            "ativo": self.ativo,
            "usuario_id": self.usuario_id,
        }

    @classmethod
    def from_dict(
        cls,
        dados,
        id_padrao=0,
    ):
        return cls(
            id_cliente=dados.get(
                "id",
                id_padrao,
            ),
            nome=dados.get(
                "nome",
                "",
            ),
            usuario=dados.get(
                "usuario",
                "",
            ),
            email=dados.get(
                "email",
                "",
            ),
            ativo=bool(
                dados.get(
                    "ativo",
                    True,
                )
            ),
            usuario_id=dados.get(
                "usuario_id"
            ),
        )

    # ================================================================
    # REPRESENTAÇÃO
    # ================================================================

    def __str__(self):
        status = (
            "ATIVO"
            if self.ativo
            else "DESATIVADO"
        )

        return (
            f"Cliente #{self.id} - "
            f"{self.nome} "
            f"(@{self.usuario}) "
            f"[{status}]"
        )