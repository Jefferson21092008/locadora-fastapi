from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
)

from api.auditoria import (
    registrar_auditoria,
)

from api.dependencias import (
    exigir_permissao,
    get_cliente_atual,
    get_container,
    get_usuario_atual,
)
from api.erros import (
    muitas_tentativas,
    nao_autorizado,
    recurso_nao_encontrado,
)
from api.observabilidade import (
    registrar_evento,
    request_id_atual,
)
from api.schemas.auth import (
    AlterarUsuarioRequest,
    LoginRequest,
    MensagemAuthResponse,
    RecuperacaoSenhaRequest,
    RedefinirSenhaRequest,
    SessaoResponse,
    TokenResponse,
    UsuarioAutenticadoResponse,
)
from api.seguranca import (
    criar_token_acesso,
)
from api.rate_limit import (
    obter_ip_cliente,
    rate_limiter,
)
from modulos.container import (
    Container,
)
from modulos.excecoes import (
    RegraDeNegocio,
)
from modulos.permissoes import (
    Permissao,
    listar_permissoes,
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

MENSAGEM_SESSAO_INVALIDA = (
    "Sessão inválida ou expirada."
)

REFRESH_COOKIE = (
    "locadora_refresh_token"
)


def _cookie_seguro(
    container,
):
    public_url = str(
        getattr(
            container.config,
            "public_url",
            "",
        )
    ).strip().lower()

    return public_url.startswith(
        "https://"
    )


def _definir_refresh_cookie(
    response,
    container,
    refresh_token,
):
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=(
            container.sessao_service
            .validade_refresh_segundos()
        ),
        httponly=True,
        secure=_cookie_seguro(
            container
        ),
        samesite="lax",
        path="/",
    )


def _remover_refresh_cookie(
    response,
    container,
):
    response.delete_cookie(
        key=REFRESH_COOKIE,
        httponly=True,
        secure=_cookie_seguro(
            container
        ),
        samesite="lax",
        path="/",
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
                429: {
            "description": (
                "Limite de tentativas excedido."
            ),
        },
    },
)
def login(
    request: Request,
    response: Response,
    dados: LoginRequest,
    container: Container = Depends(
        get_container
    ),
):
    ip = obter_ip_cliente(
        request
    )

    chave_limite = (
        f"login:{ip}:"
        f"{dados.usuario.strip().lower()}"
    )

    if rate_limiter.atingiu_limite(
        chave=chave_limite,
        limite=5,
        janela_segundos=60,
    ):
        registrar_evento(
            "auth.login.rate_limited",
            request_id=request_id_atual(
                request
            ),
            status_code=429,
        )
        muitas_tentativas()

    usuario = (
        container.auth_service
        .buscar_por_usuario(
            dados.usuario
        )
    )

    if usuario is None:
        rate_limiter.registrar(
            chave_limite
        )

        registrar_evento(
            "auth.login.failed",
            request_id=request_id_atual(
                request
            ),
            status_code=401,
        )

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
        rate_limiter.registrar(
            chave_limite
        )

        registrar_evento(
            "auth.login.failed",
            request_id=request_id_atual(
                request
            ),
            status_code=401,
        )

        nao_autorizado(
            MENSAGEM_CREDENCIAIS_INVALIDAS
        )

    rate_limiter.limpar(
        chave_limite
    )

    registrar_evento(
        "auth.login.succeeded",
        request_id=request_id_atual(
            request
        ),
        user_id=usuario.id,
        role=usuario.role.value,
        status_code=200,
    )

    sessao = (
        container.sessao_service
        .criar(
            usuario.id
        )
    )

    token = criar_token_acesso(
        usuario=usuario,
        secret=(
            container.config
            .jwt_secret
        ),
        sessao_id=sessao["id"],
    )

    _definir_refresh_cookie(
        response=response,
        container=container,
        refresh_token=(
            sessao["refresh_token"]
        ),
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )


# ================================================================
# REFRESH TOKEN E SESSÕES
# ================================================================


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar access token",
    description=(
        "Rotaciona o refresh token armazenado em cookie HttpOnly "
        "e emite um novo access token JWT."
    ),
    responses={
        401: {
            "description": (
                "Sessão inválida ou expirada."
            ),
        },
    },
)
def renovar_token(
    request: Request,
    response: Response,
    container: Container = Depends(
        get_container
    ),
):
    refresh_token = request.cookies.get(
        REFRESH_COOKIE
    )

    try:
        sessao = (
            container.sessao_service
            .renovar(
                refresh_token
            )
        )

    except RegraDeNegocio:
        _remover_refresh_cookie(
            response=response,
            container=container,
        )

        registrar_evento(
            "auth.refresh.failed",
            request_id=request_id_atual(
                request
            ),
            status_code=401,
        )

        nao_autorizado(
            MENSAGEM_SESSAO_INVALIDA
        )

    usuario = (
        container.auth_service
        .buscar_por_id(
            sessao["usuario_id"]
        )
    )

    if (
        usuario is None
        or not usuario.ativo
    ):
        container.sessao_service.revogar(
            id_sessao=sessao["id"],
            usuario_id=(
                sessao["usuario_id"]
            ),
        )
        _remover_refresh_cookie(
            response=response,
            container=container,
        )
        nao_autorizado(
            MENSAGEM_SESSAO_INVALIDA
        )

    token = criar_token_acesso(
        usuario=usuario,
        secret=(
            container.config
            .jwt_secret
        ),
        sessao_id=sessao["id"],
    )

    _definir_refresh_cookie(
        response=response,
        container=container,
        refresh_token=(
            sessao["refresh_token"]
        ),
    )

    registrar_evento(
        "auth.refresh.succeeded",
        request_id=request_id_atual(
            request
        ),
        user_id=usuario.id,
        role=usuario.role.value,
        status_code=200,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )


@router.post(
    "/logout",
    response_model=MensagemAuthResponse,
    summary="Encerrar sessão atual",
)
def logout(
    request: Request,
    response: Response,
    container: Container = Depends(
        get_container
    ),
):
    refresh_token = request.cookies.get(
        REFRESH_COOKIE
    )

    container.sessao_service.revogar_por_token(
        refresh_token
    )

    _remover_refresh_cookie(
        response=response,
        container=container,
    )

    registrar_evento(
        "auth.logout",
        request_id=request_id_atual(
            request
        ),
        status_code=200,
    )

    return MensagemAuthResponse(
        mensagem=(
            "Sessão encerrada com sucesso."
        )
    )


@router.get(
    "/sessoes",
    response_model=list[SessaoResponse],
    summary="Listar sessões ativas",
)
def listar_sessoes(
    usuario=Depends(
        exigir_permissao(
            Permissao.SESSOES_GERENCIAR
        )
    ),
    container: Container = Depends(
        get_container
    ),
):
    return [
        SessaoResponse(
            id=sessao["id"],
            criado_em=(
                sessao["criado_em"]
            ),
            expira_em=(
                sessao["expira_em"]
            ),
            ultimo_uso_em=(
                sessao["ultimo_uso_em"]
            ),
        )
        for sessao in (
            container.sessao_service
            .listar_ativas(
                usuario.id
            )
        )
    ]


@router.delete(
    "/sessoes/{id_sessao}",
    response_model=MensagemAuthResponse,
    summary="Revogar uma sessão",
)
def revogar_sessao(
    id_sessao: int,
    usuario=Depends(
        exigir_permissao(
            Permissao.SESSOES_GERENCIAR
        )
    ),
    container: Container = Depends(
        get_container
    ),
):
    revogada = (
        container.sessao_service
        .revogar(
            id_sessao=id_sessao,
            usuario_id=usuario.id,
        )
    )

    if not revogada:
        recurso_nao_encontrado(
            "Sessão não encontrada."
        )

    return MensagemAuthResponse(
        mensagem=(
            "Sessão revogada com sucesso."
        )
    )


@router.delete(
    "/sessoes",
    response_model=MensagemAuthResponse,
    summary="Revogar todas as sessões",
)
def revogar_todas_sessoes(
    usuario=Depends(
        exigir_permissao(
            Permissao.SESSOES_GERENCIAR
        )
    ),
    container: Container = Depends(
        get_container
    ),
):
    container.sessao_service.revogar_todas(
        usuario.id
    )

    return MensagemAuthResponse(
        mensagem=(
            "Todas as sessões foram revogadas."
        )
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
        permissoes=listar_permissoes(
            usuario.role
        ),
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
    request: Request,
    dados: AlterarUsuarioRequest,
    container: Container = Depends(
        get_container
    ),
    cliente=Depends(
        get_cliente_atual
    ),
    _usuario_autorizado=Depends(
        exigir_permissao(
            Permissao.CONTA_RENOMEAR
        )
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

    registrar_auditoria(
        request=request,
        container=container,
        ator=cliente,
        acao="conta.usuario_alterado",
        recurso="usuario",
        recurso_id=usuario.id,
        campos_alterados=(
            "usuario",
        ),
    )

    return UsuarioAutenticadoResponse(
        id=usuario.id,
        usuario=usuario.usuario,
        role=usuario.role.value,
        permissoes=listar_permissoes(
            usuario.role
        ),
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
        429: {
            "description": (
                "Limite de tentativas excedido."
            ),
        },
    },
)
def solicitar_recuperacao_senha(
    request: Request,
    dados: RecuperacaoSenhaRequest,
    container: Container = Depends(
        get_container
    ),
):
    ip = obter_ip_cliente(
        request
    )

    chave_limite = (
        f"recuperacao:{ip}:"
        f"{dados.usuario.strip().lower()}"
    )

    if rate_limiter.atingiu_limite(
        chave=chave_limite,
        limite=3,
        janela_segundos=900,
    ):
        registrar_evento(
            (
                "auth.password_recovery."
                "rate_limited"
            ),
            request_id=request_id_atual(
                request
            ),
            status_code=429,
        )
        muitas_tentativas()

    rate_limiter.registrar(
        chave_limite
    )

    (
        container.recuperacao_senha_service
        .solicitar_recuperacao(
            dados.usuario
        )
    )

    registrar_evento(
        "auth.password_recovery.requested",
        request_id=request_id_atual(
            request
        ),
        status_code=200,
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
        429: {
            "description": (
                "Limite de tentativas excedido."
            ),
        },
    },
)

def redefinir_senha(
    request: Request,
    dados: RedefinirSenhaRequest,
    container: Container = Depends(
        get_container
    ),
):
    ip = obter_ip_cliente(
        request
    )

    chave_limite = (
        f"redefinicao:{ip}:"
        f"{dados.token}"
    )

    if rate_limiter.atingiu_limite(
        chave=chave_limite,
        limite=5,
        janela_segundos=900,
    ):
        registrar_evento(
            (
                "auth.password_reset."
                "rate_limited"
            ),
            request_id=request_id_atual(
                request
            ),
            status_code=429,
        )
        muitas_tentativas()

    rate_limiter.registrar(
        chave_limite
    )

    mensagem = (
        container.recuperacao_senha_service
        .redefinir_senha(
            token=dados.token,
            nova_senha=dados.nova_senha,
        )
    )

    rate_limiter.limpar(
        chave_limite
    )

    registrar_evento(
        "auth.password_reset.succeeded",
        request_id=request_id_atual(
            request
        ),
        status_code=200,
    )

    return MensagemAuthResponse(
        mensagem=mensagem
    )
