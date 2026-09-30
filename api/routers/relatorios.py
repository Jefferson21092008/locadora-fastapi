from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
)

from api.dependencias import (
    exigir_permissao,
    get_container,
)

from api.schemas.relatorios import (
    DashboardMetricasResponse,
    ClienteMaisAlugaResponse,
    CustoManutencaoResponse,
    FaturamentoPorTipoResponse,
    ResultadoVeiculoResponse,
    ResumoFinanceiroResponse,
    ResumoGeralResponse,
    VeiculoMaisAlugadoResponse,
)

from modulos.permissoes import (
    Permissao,
)

from modulos.container import Container


router = APIRouter(
    prefix="/relatorios",
    tags=["Relatórios"],
)


# ================================================================
# DASHBOARD
# ================================================================


@router.get(
    "/dashboard",
    response_model=DashboardMetricasResponse,
    summary="Consultar métricas do dashboard",
    description=(
        "Retorna indicadores operacionais e financeiros "
        "agregados diretamente no banco para alimentar o "
        "dashboard administrativo."
    ),
    responses={
        401: {
            "description": "Autenticação necessária.",
        },
        403: {
            "description": "Usuário sem permissão para relatórios.",
        },
    },
)
def metricas_dashboard(
    atualizar: bool = Query(
        False,
        description=(
            "Ignora o cache e recalcula as métricas "
            "diretamente no banco."
        ),
    ),
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.RELATORIOS_LER
        )
    ),
):
    return (
        container.relatorio_service
        .metricas_dashboard(
            forcar_atualizacao=atualizar
        )
    )


# ================================================================
# RESUMO GERAL
# ================================================================


@router.get(
    "/resumo",
    response_model=ResumoGeralResponse,
    summary="Consultar resumo geral",
    description=(
        "Retorna uma visão geral dos principais dados "
        "da locadora, reunindo indicadores operacionais "
        "em um único relatório. Esta operação é restrita "
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
def resumo_geral(
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.RELATORIOS_LER
        )
    ),
):
    return (
        container.relatorio_service
        .gerar_resumo()
    )


# ================================================================
# VEÍCULOS MAIS ALUGADOS
# ================================================================


@router.get(
    "/veiculos-mais-alugados",
    response_model=list[
        VeiculoMaisAlugadoResponse
    ],
    summary="Listar veículos mais alugados",
    description=(
        "Retorna um ranking dos veículos com maior "
        "quantidade de aluguéis registrados. O parâmetro "
        "`limite` define quantos resultados podem ser "
        "retornados. Esta operação é restrita "
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
        422: {
            "description": (
                "O parâmetro limite não passou "
                "pela validação."
            ),
        },
    },
)
def veiculos_mais_alugados(
    limite: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.RELATORIOS_LER
        )
    ),
):
    return (
        container.relatorio_service
        .veiculos_mais_alugados(
            limite
        )
    )


# ================================================================
# FATURAMENTO POR TIPO
# ================================================================


@router.get(
    "/faturamento-por-tipo",
    response_model=list[
        FaturamentoPorTipoResponse
    ],
    summary="Consultar faturamento por tipo",
    description=(
        "Agrupa o faturamento da locadora pelo tipo "
        "de veículo, permitindo comparar quanto cada "
        "categoria gerou em receitas. Esta operação "
        "é restrita a administradores."
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
def faturamento_por_tipo(
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.RELATORIOS_LER
        )
    ),
):
    return (
        container.relatorio_service
        .faturamento_por_tipo()
    )


# ================================================================
# CUSTOS DE MANUTENÇÃO
# ================================================================


@router.get(
    "/custos-manutencao",
    response_model=list[
        CustoManutencaoResponse
    ],
    summary="Consultar custos de manutenção",
    description=(
        "Retorna os custos de manutenção associados "
        "à frota, permitindo acompanhar os gastos "
        "registrados por veículo. Esta operação "
        "é restrita a administradores."
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
def custos_manutencao(
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.RELATORIOS_LER
        )
    ),
):
    return (
        container.relatorio_service
        .custos_manutencao()
    )


# ================================================================
# CLIENTES QUE MAIS ALUGAM
# ================================================================


@router.get(
    "/clientes-mais-alugam",
    response_model=list[
        ClienteMaisAlugaResponse
    ],
    summary="Listar clientes que mais alugam",
    description=(
        "Retorna um ranking dos clientes com maior "
        "quantidade de aluguéis registrados. O parâmetro "
        "`limite` define quantos resultados podem ser "
        "retornados. Esta operação é restrita "
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
        422: {
            "description": (
                "O parâmetro limite não passou "
                "pela validação."
            ),
        },
    },
)
def clientes_mais_alugam(
    limite: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.RELATORIOS_LER
        )
    ),
):
    return (
        container.relatorio_service
        .clientes_mais_alugam(
            limite
        )
    )


# ================================================================
# RESUMO FINANCEIRO
# ================================================================


@router.get(
    "/resumo-financeiro",
    response_model=ResumoFinanceiroResponse,
    summary="Consultar resumo financeiro",
    description=(
        "Retorna os principais indicadores financeiros "
        "da locadora, reunindo receitas, custos de "
        "manutenção e resultado bruto. Esta operação "
        "é restrita a administradores."
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
def resumo_financeiro(
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.RELATORIOS_LER
        )
    ),
):
    return (
        container.relatorio_service
        .resumo_financeiro()
    )


# ================================================================
# RESULTADO POR VEÍCULO
# ================================================================


@router.get(
    "/resultado-por-veiculo",
    response_model=list[
        ResultadoVeiculoResponse
    ],
    summary="Consultar resultado por veículo",
    description=(
        "Retorna o desempenho financeiro individual "
        "dos veículos da frota, considerando receitas "
        "e custos de manutenção registrados. Esta "
        "operação é restrita a administradores."
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
def resultado_por_veiculo(
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.RELATORIOS_LER
        )
    ),
):
    return (
        container.relatorio_service
        .resultado_por_veiculo()
    )

# ================================================================
# EXPORTAÇÕES
# ================================================================


@router.get(
    "/resultado-por-veiculo/exportar/{formato}",
    summary="Exportar resultado por veículo",
    description=(
        "Gera o relatório completo de resultado por veículo "
        "nos formatos CSV, Excel ou PDF. A operação é restrita "
        "a usuários com permissão de relatórios."
    ),
    responses={
        200: {
            "description": "Arquivo gerado para download.",
            "content": {
                "text/csv": {},
                (
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ): {},
                "application/pdf": {},
            },
        },
        401: {
            "description": "Autenticação necessária.",
        },
        403: {
            "description": "Usuário sem permissão para relatórios.",
        },
        422: {
            "description": "Formato de exportação inválido.",
        },
    },
)
def exportar_resultado_por_veiculo(
    formato: Literal[
        "csv",
        "xlsx",
        "pdf",
    ],
    container: Container = Depends(
        get_container
    ),
    usuario_admin=Depends(
        exigir_permissao(
            Permissao.RELATORIOS_LER
        )
    ),
):
    arquivo = (
        container
        .exportacao_relatorios_service
        .exportar_resultado_por_veiculo(
            formato
        )
    )

    return Response(
        content=arquivo.conteudo,
        media_type=arquivo.media_type,
        headers={
            "Content-Disposition": (
                'attachment; filename="'
                f"{arquivo.nome_arquivo}"
                '"'
            ),
            "Cache-Control": "no-store",
        },
    )
