from fastapi import (
    APIRouter,
    Depends,
    Request,
)

from api.auditoria import (
    registrar_auditoria,
)
from api.dependencias import (
    exigir_permissao,
    get_container,
)
from api.schemas.vistorias import (
    AluguelVistoriaResponse,
    CaucaoResponse,
    CaucaoUpsert,
    DanoCreate,
    DanoResponse,
    IndicadoresVistoriaResponse,
    InspecaoCreate,
    InspecaoResponse,
    MultaTransitoCreate,
    MultaTransitoResponse,
    ResumoVistoriaResponse,
)
from modulos.container import (
    Container,
)
from modulos.permissoes import (
    Permissao,
)


router = APIRouter(
    prefix="/vistorias",
    tags=["Vistorias"],
)


def transformar_inspecao(
    inspecao,
):
    return InspecaoResponse(
        id=inspecao.id,
        aluguel_id=(
            inspecao.aluguel_id
        ),
        tipo=inspecao.tipo,
        quilometragem=(
            inspecao.quilometragem
        ),
        combustivel_percentual=(
            inspecao.combustivel_percentual
        ),
        observacoes=(
            inspecao.observacoes
        ),
        criada_em=(
            inspecao.criada_em
        ),
    )


def transformar_dano(
    dano,
):
    return DanoResponse(
        id=dano.id,
        aluguel_id=(
            dano.aluguel_id
        ),
        descricao=dano.descricao,
        valor_estimado=(
            dano.valor_estimado
        ),
        status=dano.status,
        criada_em=dano.criada_em,
        cancelada_em=(
            dano.cancelada_em
        ),
    )


def transformar_multa(
    multa,
):
    return MultaTransitoResponse(
        id=multa.id,
        aluguel_id=(
            multa.aluguel_id
        ),
        descricao=multa.descricao,
        valor=multa.valor,
        data_ocorrencia=(
            multa.data_ocorrencia
        ),
        status=multa.status,
        criada_em=multa.criada_em,
        cancelada_em=(
            multa.cancelada_em
        ),
    )


def transformar_caucao(
    caucao,
):
    if caucao is None:
        return None

    return CaucaoResponse(
        id=caucao.id,
        aluguel_id=(
            caucao.aluguel_id
        ),
        valor=caucao.valor,
        valor_liberado=(
            caucao.valor_liberado
        ),
        valor_retido=(
            caucao.valor_retido
        ),
        status=caucao.status,
        observacoes=(
            caucao.observacoes
        ),
        criada_em=caucao.criada_em,
        atualizada_em=(
            caucao.atualizada_em
        ),
    )


def transformar_aluguel(
    aluguel,
):
    return AluguelVistoriaResponse(
        id=aluguel.id,
        cliente_id=(
            aluguel.cliente_id
        ),
        cliente_nome=(
            aluguel.cliente_nome
        ),
        cliente_usuario=(
            aluguel.cliente_usuario
        ),
        veiculo_id=(
            aluguel.veiculo_id
        ),
        veiculo_tipo=(
            aluguel.veiculo_tipo
        ),
        veiculo_modelo=(
            aluguel.veiculo_modelo
        ),
        status=aluguel.status,
        data_inicio=(
            aluguel.data_inicio
        ),
        data_prevista=(
            aluguel.data_prevista
        ),
        data_fim=aluguel.data_fim,
    )


def transformar_resumo(
    resumo,
):
    return ResumoVistoriaResponse(
        aluguel=transformar_aluguel(
            resumo["aluguel"]
        ),
        inspecoes=[
            transformar_inspecao(
                item
            )
            for item
            in resumo["inspecoes"]
        ],
        danos=[
            transformar_dano(
                item
            )
            for item
            in resumo["danos"]
        ],
        multas=[
            transformar_multa(
                item
            )
            for item
            in resumo["multas"]
        ],
        caucao=transformar_caucao(
            resumo["caucao"]
        ),
        indicadores=(
            IndicadoresVistoriaResponse(
                **resumo[
                    "indicadores"
                ]
            )
        ),
    )


@router.get(
    "/alugueis/{id_aluguel}",
    response_model=ResumoVistoriaResponse,
    summary=(
        "Consultar vistoria e ocorrências "
        "de um aluguel"
    ),
)
def consultar_vistoria(
    id_aluguel: int,
    container: Container = Depends(
        get_container
    ),
    _usuario_autorizado=Depends(
        exigir_permissao(
            Permissao.VISTORIAS_LER
        )
    ),
):
    resumo = (
        container.vistoria_service
        .obter_resumo(
            id_aluguel
        )
    )

    return transformar_resumo(
        resumo
    )


@router.post(
    "/alugueis/{id_aluguel}/inspecoes",
    status_code=201,
    response_model=InspecaoResponse,
    summary="Registrar inspeção do aluguel",
)
def registrar_inspecao(
    request: Request,
    id_aluguel: int,
    dados: InspecaoCreate,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.VISTORIAS_REGISTRAR
        )
    ),
):
    inspecao = (
        container.vistoria_service
        .registrar_inspecao(
            id_aluguel=id_aluguel,
            tipo=dados.tipo,
            quilometragem=(
                dados.quilometragem
            ),
            combustivel_percentual=(
                dados.combustivel_percentual
            ),
            observacoes=(
                dados.observacoes
            ),
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="vistoria.inspecao_registrada",
        recurso="aluguel",
        recurso_id=id_aluguel,
        campos_alterados=(
            "tipo",
            "quilometragem",
            "combustivel_percentual",
            "observacoes",
        ),
    )

    return transformar_inspecao(
        inspecao
    )


@router.post(
    "/alugueis/{id_aluguel}/danos",
    status_code=201,
    response_model=DanoResponse,
    summary="Registrar dano do aluguel",
)
def registrar_dano(
    request: Request,
    id_aluguel: int,
    dados: DanoCreate,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.DANOS_GERENCIAR
        )
    ),
):
    dano = (
        container.vistoria_service
        .registrar_dano(
            id_aluguel=id_aluguel,
            descricao=dados.descricao,
            valor_estimado=(
                dados.valor_estimado
            ),
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="vistoria.dano_registrado",
        recurso="dano",
        recurso_id=dano.id,
        campos_alterados=(
            "aluguel_id",
            "descricao",
            "valor_estimado",
        ),
    )

    return transformar_dano(
        dano
    )


@router.patch(
    "/danos/{id_dano}/cancelar",
    response_model=DanoResponse,
    summary="Cancelar registro de dano",
)
def cancelar_dano(
    request: Request,
    id_dano: int,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.DANOS_GERENCIAR
        )
    ),
):
    dano = (
        container.vistoria_service
        .cancelar_dano(
            id_dano
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="vistoria.dano_cancelado",
        recurso="dano",
        recurso_id=dano.id,
        campos_alterados=(
            "status",
            "cancelada_em",
        ),
    )

    return transformar_dano(
        dano
    )


@router.post(
    "/alugueis/{id_aluguel}/multas",
    status_code=201,
    response_model=MultaTransitoResponse,
    summary="Registrar multa de trânsito",
)
def registrar_multa(
    request: Request,
    id_aluguel: int,
    dados: MultaTransitoCreate,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.MULTAS_GERENCIAR
        )
    ),
):
    multa = (
        container.vistoria_service
        .registrar_multa(
            id_aluguel=id_aluguel,
            descricao=dados.descricao,
            valor=dados.valor,
            data_ocorrencia=(
                dados.data_ocorrencia
            ),
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="vistoria.multa_registrada",
        recurso="multa_transito",
        recurso_id=multa.id,
        campos_alterados=(
            "aluguel_id",
            "descricao",
            "valor",
            "data_ocorrencia",
        ),
    )

    return transformar_multa(
        multa
    )


@router.patch(
    "/multas/{id_multa}/cancelar",
    response_model=MultaTransitoResponse,
    summary="Cancelar multa de trânsito",
)
def cancelar_multa(
    request: Request,
    id_multa: int,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.MULTAS_GERENCIAR
        )
    ),
):
    multa = (
        container.vistoria_service
        .cancelar_multa(
            id_multa
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="vistoria.multa_cancelada",
        recurso="multa_transito",
        recurso_id=multa.id,
        campos_alterados=(
            "status",
            "cancelada_em",
        ),
    )

    return transformar_multa(
        multa
    )


@router.put(
    "/alugueis/{id_aluguel}/caucao",
    response_model=CaucaoResponse,
    summary="Definir ou atualizar caução",
)
def definir_caucao(
    request: Request,
    id_aluguel: int,
    dados: CaucaoUpsert,
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.CAUCOES_GERENCIAR
        )
    ),
):
    caucao = (
        container.vistoria_service
        .definir_caucao(
            id_aluguel=id_aluguel,
            valor=dados.valor,
            valor_liberado=(
                dados.valor_liberado
            ),
            observacoes=(
                dados.observacoes
            ),
        )
    )

    registrar_auditoria(
        request=request,
        container=container,
        ator=usuario_admin,
        acao="vistoria.caucao_atualizada",
        recurso="caucao",
        recurso_id=caucao.id,
        campos_alterados=(
            "valor",
            "valor_liberado",
            "status",
            "observacoes",
        ),
    )

    return transformar_caucao(
        caucao
    )
