from fastapi import (
    APIRouter,
    Depends,
)

from api.dependencias import (
    get_admin_atual,
    get_container,
)

from api.schemas.manutencoes import (
    ManutencaoCreate,
    ManutencaoFinalizar,
    ManutencaoResponse,
)

from modulos.container import Container


router = APIRouter(
    prefix="/manutencoes",
    tags=["Manutenções"],
)


# ================================================================
# SERIALIZAÇÃO
# ================================================================


def transformar_manutencao(
    manutencao,
):
    return ManutencaoResponse(
        id=manutencao.id,

        veiculo_id=(
            manutencao.veiculo_id
        ),

        motivo=manutencao.motivo,

        quilometragem=(
            manutencao.quilometragem
        ),

        custo=manutencao.custo,

        data_inicio=(
            manutencao.data_inicio
        ),

        data_fim=(
            manutencao.data_fim
        ),

        status=manutencao.status,
    )


# ================================================================
# LISTAR TODAS
# ================================================================


@router.get(
    "",
    response_model=list[
        ManutencaoResponse
    ],
    summary="Listar manutenções",
    description=(
        "Retorna todas as manutenções registradas "
        "na locadora, incluindo manutenções ativas "
        "e finalizadas. Esta operação é restrita "
        "a administradores."
    ),
    responses={
        401: {
            "description": (
                "Autenticação necessária ou "
                "token inválido."
            ),
        },
        403: {
            "description": (
                "Acesso permitido apenas "
                "para administradores."
            ),
        },
    },
)
def listar_manutencoes(
    container: Container = Depends(
        get_container
    ),

    usuario_admin=Depends(
        get_admin_atual
    ),
):
    manutencoes = (
        container.manutencao_service
        .listar_manutencoes()
    )

    return [
        transformar_manutencao(
            manutencao
        )
        for manutencao
        in manutencoes
    ]


# ================================================================
# LISTAR ATIVAS
# ================================================================


@router.get(
    "/ativas",
    response_model=list[
        ManutencaoResponse
    ],
    summary="Listar manutenções ativas",
    description=(
        "Retorna apenas as manutenções que ainda "
        "estão em andamento. Esta operação é "
        "restrita a administradores."
    ),
    responses={
        401: {
            "description": (
                "Autenticação necessária ou "
                "token inválido."
            ),
        },
        403: {
            "description": (
                "Acesso permitido apenas "
                "para administradores."
            ),
        },
    },
)
def listar_manutencoes_ativas(
    container: Container = Depends(
        get_container
    ),

    usuario_admin=Depends(
        get_admin_atual
    ),
):
    manutencoes = (
        container.manutencao_service
        .listar_ativas()
    )

    return [
        transformar_manutencao(
            manutencao
        )
        for manutencao
        in manutencoes
    ]


# ================================================================
# HISTÓRICO POR VEÍCULO
# ================================================================


@router.get(
    "/veiculo/{id_veiculo}",
    response_model=list[
        ManutencaoResponse
    ],
    summary="Listar manutenções de um veículo",
    description=(
        "Retorna o histórico de manutenções associado "
        "ao veículo informado. Esta operação é "
        "restrita a administradores."
    ),
    responses={
        401: {
            "description": (
                "Autenticação necessária ou "
                "token inválido."
            ),
        },
        403: {
            "description": (
                "Acesso permitido apenas "
                "para administradores."
            ),
        },
        422: {
            "description": (
                "Identificador enviado não passou "
                "pela validação."
            ),
        },
    },
)
def listar_manutencoes_do_veiculo(
    id_veiculo: int,

    container: Container = Depends(
        get_container
    ),

    usuario_admin=Depends(
        get_admin_atual
    ),
):
    manutencoes = (
        container.manutencao_service
        .listar_por_veiculo(
            id_veiculo
        )
    )

    return [
        transformar_manutencao(
            manutencao
        )
        for manutencao
        in manutencoes
    ]


# ================================================================
# ABRIR MANUTENÇÃO
# ================================================================


@router.post(
    "",
    status_code=201,
    response_model=ManutencaoResponse,
    summary="Abrir manutenção",
    description=(
        "Registra uma nova manutenção para um veículo. "
        "O veículo precisa existir e estar em condição "
        "válida para entrar em manutenção. Esta operação "
        "é restrita a administradores."
    ),
    responses={
        400: {
            "description": (
                "A manutenção não pode ser aberta "
                "devido a uma regra de negócio, como "
                "já existir uma manutenção ativa."
            ),
        },
        401: {
            "description": (
                "Autenticação necessária ou "
                "token inválido."
            ),
        },
        403: {
            "description": (
                "Acesso permitido apenas "
                "para administradores."
            ),
        },
        404: {
            "description": (
                "Veículo não encontrado."
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
def abrir_manutencao(
    dados: ManutencaoCreate,

    container: Container = Depends(
        get_container
    ),

    usuario_admin=Depends(
        get_admin_atual
    ),
):
    manutencao = (
        container.manutencao_service
        .abrir(
            id_veiculo=(
                dados.id_veiculo
            ),

            motivo=dados.motivo,
        )
    )

    return transformar_manutencao(
        manutencao
    )


# ================================================================
# FINALIZAR MANUTENÇÃO
# ================================================================


@router.patch(
    "/{id_veiculo}/finalizar",
    response_model=ManutencaoResponse,
    summary="Finalizar manutenção",
    description=(
        "Finaliza a manutenção ativa de um veículo, "
        "registrando seu custo e liberando o veículo "
        "conforme as regras da aplicação. Esta operação "
        "é restrita a administradores."
    ),
    responses={
        400: {
            "description": (
                "A finalização viola uma regra "
                "de negócio."
            ),
        },
        401: {
            "description": (
                "Autenticação necessária ou "
                "token inválido."
            ),
        },
        403: {
            "description": (
                "Acesso permitido apenas "
                "para administradores."
            ),
        },
        404: {
            "description": (
                "Veículo não encontrado ou o veículo "
                "não possui manutenção ativa."
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
def finalizar_manutencao(
    id_veiculo: int,

    dados: ManutencaoFinalizar,

    container: Container = Depends(
        get_container
    ),

    usuario_admin=Depends(
        get_admin_atual
    ),
):
    manutencao = (
        container.manutencao_service
        .finalizar(
            id_veiculo=id_veiculo,
            custo=dados.custo,
        )
    )

    return transformar_manutencao(
        manutencao
    )
