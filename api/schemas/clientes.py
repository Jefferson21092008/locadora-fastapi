import re

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class ClienteCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nome": "João da Silva",
                    "usuario": "joao123",
                    "email": "joao@email.com",
                    "senha": "Senha123",
                }
            ]
        }
    )

    nome: str = Field(
        min_length=2,
        max_length=100,
        description=(
            "Nome completo do cliente."
        ),
        examples=[
            "João da Silva"
        ],
    )

    usuario: str = Field(
        min_length=3,
        max_length=30,
        description=(
            "Nome de usuário utilizado para login. "
            "Aceita letras, números, ponto, hífen "
            "e underline."
        ),
        examples=[
            "joao123"
        ],
    )

    email: str = Field(
        min_length=5,
        max_length=254,
        description=(
            "Endereço de e-mail do cliente."
        ),
        examples=[
            "joao@email.com"
        ],
    )

    senha: str = Field(
        min_length=8,
        max_length=128,
        description=(
            "Senha da conta. Deve possuir pelo menos "
            "uma letra e um número."
        ),
        examples=[
            "Senha123"
        ],
    )

    # ============================================================
    # LIMPEZA DOS TEXTOS
    # ============================================================

    @field_validator(
        "nome",
        "usuario",
        "email",
        mode="before",
    )
    @classmethod
    def limpar_textos(
        cls,
        valor,
    ):
        if isinstance(
            valor,
            str,
        ):
            return valor.strip()

        return valor

    # ============================================================
    # NOME
    # ============================================================

    @field_validator(
        "nome"
    )
    @classmethod
    def validar_nome(
        cls,
        valor,
    ):
        if not any(
            caractere.isalpha()
            for caractere in valor
        ):
            raise ValueError(
                "O nome deve conter "
                "pelo menos uma letra."
            )

        return valor

    # ============================================================
    # USUÁRIO
    # ============================================================

    @field_validator(
        "usuario"
    )
    @classmethod
    def validar_usuario(
        cls,
        valor,
    ):
        if not re.fullmatch(
            r"[A-Za-z0-9_.-]+",
            valor,
        ):
            raise ValueError(
                "O usuário pode conter "
                "apenas letras, números, "
                "ponto, hífen e underline."
            )

        return valor.lower()

    # ============================================================
    # E-MAIL
    # ============================================================

    @field_validator(
        "email"
    )
    @classmethod
    def validar_email(
        cls,
        valor,
    ):
        valor = valor.lower()

        if valor.count("@") != 1:
            raise ValueError(
                "E-mail inválido."
            )

        usuario_email, dominio = (
            valor.split("@")
        )

        if (
            not usuario_email
            or not dominio
            or "." not in dominio
            or dominio.startswith(".")
            or dominio.endswith(".")
        ):
            raise ValueError(
                "E-mail inválido."
            )

        return valor

    # ============================================================
    # SENHA
    # ============================================================

    @field_validator(
        "senha"
    )
    @classmethod
    def validar_senha(
        cls,
        valor,
    ):
        possui_letra = any(
            caractere.isalpha()
            for caractere in valor
        )

        possui_numero = any(
            caractere.isdigit()
            for caractere in valor
        )

        if not possui_letra:
            raise ValueError(
                "A senha deve conter "
                "pelo menos uma letra."
            )

        if not possui_numero:
            raise ValueError(
                "A senha deve conter "
                "pelo menos um número."
            )

        return valor


class ClienteResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "nome": "João da Silva",
                    "usuario": "joao123",
                    "email": "joao@email.com",
                    "ativo": True,
                }
            ]
        }
    )

    id: int = Field(
        description=(
            "Identificador único do cliente."
        ),
        examples=[
            1
        ],
    )

    nome: str = Field(
        description=(
            "Nome do cliente."
        ),
        examples=[
            "João da Silva"
        ],
    )

    usuario: str = Field(
        description=(
            "Nome de usuário associado "
            "ao cliente."
        ),
        examples=[
            "joao123"
        ],
    )

    email: str = Field(
        description=(
            "E-mail cadastrado pelo cliente."
        ),
        examples=[
            "joao@email.com"
        ],
    )

    ativo: bool = Field(
        description=(
            "Indica se o cadastro do cliente "
            "está ativo."
        ),
        examples=[
            True
        ],
    )
