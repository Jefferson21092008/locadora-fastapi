from datetime import datetime
from enum import Enum

from modulos.seguranca import (
    SegurancaSenha,
)


class Role(str, Enum):
    CLIENTE = "cliente"
    ADMIN = "admin"


class Usuario:
    def __init__(
        self,
        id_usuario,
        usuario,
        senha_hash,
        role=Role.CLIENTE,
        ativo=True,
        criado_em=None,
    ):
        self.id = id_usuario

        self.usuario = (
            str(usuario)
            .strip()
        )

        self._senha_hash = (
            senha_hash
        )

        if isinstance(
            role,
            Role,
        ):
            self.role = role
        else:
            self.role = Role(
                str(role).lower()
            )

        self.ativo = bool(
            ativo
        )

        self.criado_em = (
            criado_em
            or datetime.now().isoformat(
                timespec="seconds"
            )
        )

    # ================================================================
    # CRIAÇÃO
    # ================================================================

    @classmethod
    def criar(
        cls,
        id_usuario,
        usuario,
        senha,
        role=Role.CLIENTE,
    ):
        senha_hash = (
            SegurancaSenha
            .gerar_hash(
                senha
            )
        )

        return cls(
            id_usuario=id_usuario,
            usuario=usuario,
            senha_hash=senha_hash,
            role=role,
        )

    # ================================================================
    # VALIDAÇÃO
    # ================================================================

    @staticmethod
    def validar_nome_usuario(
        usuario,
    ):
        usuario = str(
            usuario
        ).strip()

        if not usuario:
            return (
                False,
                "O usuário não pode "
                "ficar vazio.",
            )

        if len(usuario) < 3:
            return (
                False,
                "O usuário deve possuir "
                "pelo menos 3 caracteres.",
            )

        if len(usuario) > 100:
            return (
                False,
                "O usuário deve possuir "
                "no máximo 100 caracteres.",
            )

        return (
            True,
            "",
        )

    def validar_dados(self):
        return (
            self.validar_nome_usuario(
                self.usuario
            )
        )
    # ================================================================
    # VALIDAÇÃO DE SENHA
    # ================================================================

    @staticmethod
    def validar_nova_senha(
        senha,
    ):
        senha = str(
            senha
        )

        if len(senha) < 8:
            return (
                False,
                "A senha deve possuir "
                "pelo menos 8 caracteres.",
            )

        tem_letra = any(
            caractere.isalpha()
            for caractere
            in senha
        )

        if not tem_letra:
            return (
                False,
                "A senha deve possuir "
                "pelo menos uma letra.",
            )

        tem_numero = any(
            caractere.isdigit()
            for caractere
            in senha
        )

        if not tem_numero:
            return (
                False,
                "A senha deve possuir "
                "pelo menos um número.",
            )

        return (
            True,
            "",
        )

    # ================================================================
    # SENHA
    # ================================================================

    def validar_senha(
        self,
        senha,
    ):
        return (
            SegurancaSenha
            .verificar(
                senha,
                self._senha_hash,
            )
        )

    def atualizar_hash_senha(
        self,
        senha,
    ):
        if not self.validar_senha(
            senha
        ):
            return False

        if (
            SegurancaSenha
            .eh_hash_atual(
                self._senha_hash
            )
        ):
            return False

        self._senha_hash = (
            SegurancaSenha
            .gerar_hash(
                senha
            )
        )

        return True

    def alterar_senha(
        self,
        nova_senha,
    ):
        valido, mensagem = (
            self.validar_nova_senha(
                nova_senha
            )
        )

        if not valido:
            return (
                False,
                mensagem,
            )

        self._senha_hash = (
            SegurancaSenha
            .gerar_hash(
                nova_senha
            )
        )

        return (
            True,
            "Senha alterada com sucesso.",
        )

    # ================================================================
    # ESTADO
    # ================================================================

    def desativar(self):
        if not self.ativo:
            return False

        self.ativo = False

        return True

    def reativar(self):
        if self.ativo:
            return False

        self.ativo = True

        return True

    # ================================================================
    # ROLE
    # ================================================================

    def eh_admin(self):
        return (
            self.role
            == Role.ADMIN
        )

    def eh_cliente(self):
        return (
            self.role
            == Role.CLIENTE
        )

    # ================================================================
    # SERIALIZAÇÃO
    # ================================================================

    def to_dict(self):
        return {
            "id": self.id,
            "usuario": self.usuario,
            "senha_hash": self._senha_hash,
            "role": self.role.value,
            "ativo": self.ativo,
            "criado_em": self.criado_em,
        }

    @classmethod
    def from_dict(
        cls,
        dados,
    ):
        return cls(
            id_usuario=dados.get(
                "id",
                0,
            ),

            usuario=dados.get(
                "usuario",
                "",
            ),

            senha_hash=dados.get(
                "senha_hash",
                "",
            ),

            role=dados.get(
                "role",
                Role.CLIENTE.value,
            ),

            ativo=bool(
                dados.get(
                    "ativo",
                    True,
                )
            ),

            criado_em=dados.get(
                "criado_em"
            ),
        )