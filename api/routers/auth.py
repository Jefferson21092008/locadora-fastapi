from fastapi import (
    APIRouter,
    Depends,
)

from api.dependencias import (
    get_cliente_atual,
    get_container,
    get_usuario_atual,
)
from api.erros import (
    nao_autorizado,
)
from api.schemas.auth import (
    AlterarUsuarioRequest,
    LoginRequest,
    MensagemAuthResponse,
    RecuperacaoSenhaRequest,
    RedefinirSenhaRequest,
    TokenResponse,
    UsuarioAutenticadoResponse,
)
from api.seguranca import (
    criar_token_acesso,
)
from modulos.container import (
    Container,
)


router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"],
)


MENSAGEM_CREDENCIAIS_INVALIDAS = (
    "Usuário ou senha incorretos."
)

MENSAGEM_RECUPERACAO = (
    "Se a conta estiver disponível, "
    "as instruções de recuperação "
    "serão enviadas."
)


# ================================================================
# LOGIN
# ================================================================


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Realizar login",
    description=(
        "Autentica um usuário da locadora utilizando "
        "nome de usuário e senha. Em caso de sucesso, "
        "retorna um token JWT do tipo Bearer que pode "
        "ser utilizado nas rotas protegidas da API."
    ),
    responses={
        401: {
            "description": (
                "Usuário ou senha incorretos."
            ),
        },
        422: {
            "description": (
                "Dados enviados não passaram "
                "pela validação."
            ),
        },
    },
)
def login(
    dados: LoginRequest,
    container: Container = Depends(
        get_container
    ),
):
    usuario = (
        container.auth_service
        .buscar_por_usuario(
            dados.usuario
        )
    )

    if usuario is None:
        nao_autorizado(
            MENSAGEM_CREDENCIAIS_INVALIDAS
        )

    autenticado = (
        container.auth_service
        .autenticar(
            nome_usuario=dados.usuario,
            senha=dados.senha,
            role=usuario.role,
        )
    )

    if not autenticado:
        nao_autorizado(
            MENSAGEM_CREDENCIAIS_INVALIDAS
        )

    token = criar_token_acesso(
        usuario=usuario,
        secret=(
            container.config
            .jwt_secret
        ),
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )


# ================================================================
# USUÁRIO ATUAL
# ================================================================


@router.get(
    "/me",
    response_model=(
        UsuarioAutenticadoResponse
    ),
    summary="Consultar usuário autenticado",
    description=(
        "Retorna os dados básicos do usuário "
        "identificado pelo token JWT enviado no "
        "cabeçalho Authorization."
    ),
    responses={
        401: {
            "description": (
                "Autenticação necessária, token "
                "inválido ou usuário indisponível."
            ),
        },
    },
)
def meu_usuario(
    usuario=Depends(
        get_usuario_atual
    ),
):
    return UsuarioAutenticadoResponse(
        id=usuario.id,
        usuario=usuario.usuario,
        role=usuario.role.value,
        ativo=usuario.ativo,
    )


# ================================================================
# ALTERAR NOME DE USUÁRIO
# ================================================================


@router.patch(
    "/me/usuario",
    response_model=(
        UsuarioAutenticadoResponse
    ),
    summary="Alterar nome de usuário",
    description=(
        "Altera o nome de usuário da "
        "conta autenticada de cliente. "
        "A senha atual é obrigatória."
    ),
    responses={
        400: {
            "description": (
                "Senha incorreta, usuário "
                "inválido ou já utilizado."
            ),
        },
        401: {
            "description": (
                "Autenticação necessária."
            ),
        },
        403: {
            "description": (
                "Operação disponível apenas "
                "para clientes."
            ),
        },
    },
)
def alterar_meu_usuario(
    dados: AlterarUsuarioRequest,
    container: Container = Depends(
        get_container
    ),
    cliente=Depends(
        get_cliente_atual
    ),
):
    cliente = (
        container.cliente_service
        .renomear_usuario(
            cliente=cliente,
            novo_usuario=(
                dados.novo_usuario
            ),
            senha_atual=(
                dados.senha_atual
            ),
        )
    )

    usuario = (
        container.auth_service
        .buscar_por_id(
            cliente.usuario_id
        )
    )

    return UsuarioAutenticadoResponse(
        id=usuario.id,
        usuario=usuario.usuario,
        role=usuario.role.value,
        ativo=usuario.ativo,
    )


# ================================================================
# SOLICITAR RECUPERAÇÃO DE SENHA
# ================================================================


@router.post(
    "/esqueci-senha",
    response_model=MensagemAuthResponse,
    summary="Solicitar recuperação de senha",
    description=(
        "Inicia o fluxo de recuperação de senha. "
        "Por segurança, a resposta é sempre genérica "
        "e não informa se o usuário existe. "
        "O token gerado não é exposto pela API."
    ),
    responses={
        422: {
            "description": (
                "Os dados enviados não passaram "
                "pela validação."
            ),
        },
    },
)
def solicitar_recuperacao_senha(
    dados: RecuperacaoSenhaRequest,
    container: Container = Depends(
        get_container
    ),
):
    (
        container.recuperacao_senha_service
        .solicitar_recuperacao(
            dados.usuario
        )
    )

    return MensagemAuthResponse(
        mensagem=MENSAGEM_RECUPERACAO
    )


# ================================================================
# REDEFINIR SENHA
# ================================================================


@router.post(
    "/redefinir-senha",
    response_model=MensagemAuthResponse,
    summary="Redefinir senha",
    description=(
        "Redefine a senha utilizando um token "
        "temporário de recuperação. O token precisa "
        "existir, não pode ter sido utilizado e deve "
        "estar dentro do prazo de validade."
    ),
    responses={
        400: {
            "description": (
                "Token inválido ou expirado, "
                "ou nova senha inválida."
            ),
        },
        422: {
            "description": (
                "Os dados enviados não passaram "
                "pela validação."
            ),
        },
    },
)
def redefinir_senha(
    dados: RedefinirSenhaRequest,
    container: Container = Depends(
        get_container
    ),
):
    mensagem = (
        container.recuperacao_senha_service
        .redefinir_senha(
            token=dados.token,
            nova_senha=dados.nova_senha,
        )
    )

    return MensagemAuthResponse(
        mensagem=mensagem
    )