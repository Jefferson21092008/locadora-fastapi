from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ================================================================
# LOGIN
# ================================================================


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "usuario": "joao123",
                    "senha": "Senha123",
                }
            ]
        }
    )

    usuario: str = Field(
        min_length=1,
        max_length=100,
        description=(
            "Nome de usuário utilizado "
            "para autenticação."
        ),
        examples=[
            "joao123"
        ],
    )

    senha: str = Field(
        min_length=1,
        max_length=128,
        description=(
            "Senha da conta do usuário."
        ),
        examples=[
            "Senha123"
        ],
    )

    @field_validator(
        "usuario",
        mode="before",
    )
    @classmethod
    def limpar_usuario(
        cls,
        valor,
    ):
        if isinstance(
            valor,
            str,
        ):
            return valor.strip()

        return valor


# ================================================================
# TOKEN
# ================================================================


class TokenResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": (
                        "eyJhbGciOiJIUzI1NiIs"
                        "InR5cCI6IkpXVCJ9.exemplo.assinatura"
                    ),
                    "token_type": "bearer",
                }
            ]
        }
    )

    access_token: str = Field(
        min_length=1,
        description=(
            "Token JWT utilizado para acessar "
            "rotas protegidas da API."
        ),
    )

    token_type: str = Field(
        min_length=1,
        description=(
            "Tipo do token retornado pela API."
        ),
        examples=[
            "bearer"
        ],
    )


# ================================================================
# USUÁRIO AUTENTICADO
# ================================================================


class UsuarioAutenticadoResponse(
    BaseModel
):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "usuario": "joao123",
                    "role": "cliente",
                    "ativo": True,
                }
            ]
        }
    )

    id: int = Field(
        gt=0,
        description=(
            "Identificador único do usuário."
        ),
        examples=[
            1
        ],
    )

    usuario: str = Field(
        description=(
            "Nome de usuário da conta autenticada."
        ),
        examples=[
            "joao123"
        ],
    )

    role: Literal[
        "admin",
        "cliente",
    ] = Field(
        description=(
            "Perfil de acesso do usuário."
        ),
        examples=[
            "cliente"
        ],
    )

    ativo: bool = Field(
        description=(
            "Indica se a conta do usuário "
            "está ativa."
        ),
        examples=[
            True
        ],
    )


# ================================================================
# SOLICITAÇÃO DE RECUPERAÇÃO DE SENHA
# ================================================================


class RecuperacaoSenhaRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "usuario": "joao123",
                }
            ]
        }
    )

    usuario: str = Field(
        min_length=1,
        max_length=100,
        description=(
            "Nome de usuário da conta que deseja "
            "iniciar a recuperação de senha."
        ),
        examples=[
            "joao123"
        ],
    )

    @field_validator(
        "usuario",
        mode="before",
    )
    @classmethod
    def limpar_usuario(
        cls,
        valor,
    ):
        if isinstance(
            valor,
            str,
        ):
            return valor.strip()

        return valor


# ================================================================
# REDEFINIÇÃO DE SENHA
# ================================================================


class RedefinirSenhaRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "token": "token_de_recuperacao_recebido",
                    "nova_senha": "NovaSenha123",
                }
            ]
        }
    )

    token: str = Field(
        min_length=1,
        max_length=512,
        description=(
            "Token temporário gerado para "
            "recuperação de senha."
        ),
        examples=[
            "token_de_recuperacao_recebido"
        ],
    )

    nova_senha: str = Field(
        min_length=8,
        max_length=128,
        description=(
            "Nova senha da conta. Deve conter "
            "pelo menos uma letra e um número."
        ),
        examples=[
            "NovaSenha123"
        ],
    )

    @field_validator(
        "token",
        mode="before",
    )
    @classmethod
    def limpar_token(
        cls,
        valor,
    ):
        if isinstance(
            valor,
            str,
        ):
            return valor.strip()

        return valor

    @field_validator(
        "nova_senha"
    )
    @classmethod
    def validar_nova_senha(
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


# ================================================================
# MENSAGEM
# ================================================================


class MensagemAuthResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "mensagem": (
                        "Se a conta estiver disponível, "
                        "as instruções de recuperação "
                        "serão enviadas."
                    )
                }
            ]
        }
    )

    mensagem: str = Field(
        min_length=1,
        description=(
            "Mensagem informativa sobre "
            "a operação realizada."
        ),
    )
