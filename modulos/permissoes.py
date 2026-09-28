from enum import Enum


class Permissao(str, Enum):
    CLIENTES_LER = "clientes:ler"
    CLIENTES_GERENCIAR_STATUS = (
        "clientes:gerenciar_status"
    )
    VEICULOS_CRIAR = "veiculos:criar"
    VEICULOS_EDITAR = "veiculos:editar"
    VEICULOS_GERENCIAR_STATUS = (
        "veiculos:gerenciar_status"
    )
    ALUGUEIS_LER = "alugueis:ler"
    ALUGUEIS_CRIAR = "alugueis:criar"
    ALUGUEIS_PROPRIOS_LER = (
        "alugueis:proprios:ler"
    )
    ALUGUEIS_DEVOLVER = (
        "alugueis:devolver"
    )
    MANUTENCOES_LER = "manutencoes:ler"
    MANUTENCOES_CRIAR = "manutencoes:criar"
    MANUTENCOES_EDITAR = "manutencoes:editar"
    MANUTENCOES_FINALIZAR = (
        "manutencoes:finalizar"
    )
    RESERVAS_LER = "reservas:ler"
    RESERVAS_CRIAR = "reservas:criar"
    RESERVAS_PROPRIAS_LER = "reservas:proprias:ler"
    RESERVAS_CANCELAR = "reservas:cancelar"
    VISTORIAS_LER = "vistorias:ler"
    VISTORIAS_REGISTRAR = "vistorias:registrar"
    DANOS_GERENCIAR = "danos:gerenciar"
    MULTAS_GERENCIAR = "multas:gerenciar"
    CAUCOES_GERENCIAR = "caucoes:gerenciar"
    FINANCEIRO_LER = "financeiro:ler"
    FINANCEIRO_RECEBER = "financeiro:receber"
    FINANCEIRO_ESTORNAR = "financeiro:estornar"
    RELATORIOS_LER = "relatorios:ler"
    AUDITORIA_LER = "auditoria:ler"
    CONTA_RENOMEAR = "conta:renomear"
    SESSOES_GERENCIAR = (
        "sessoes:gerenciar"
    )


_PERMISSOES_POR_ROLE = {
    "admin": frozenset(
        {
            Permissao.CLIENTES_LER,
            Permissao.CLIENTES_GERENCIAR_STATUS,
            Permissao.VEICULOS_CRIAR,
            Permissao.VEICULOS_EDITAR,
            Permissao.VEICULOS_GERENCIAR_STATUS,
            Permissao.ALUGUEIS_LER,
            Permissao.MANUTENCOES_LER,
            Permissao.MANUTENCOES_CRIAR,
            Permissao.MANUTENCOES_EDITAR,
            Permissao.MANUTENCOES_FINALIZAR,
            Permissao.RESERVAS_LER,
            Permissao.RESERVAS_CANCELAR,
            Permissao.VISTORIAS_LER,
            Permissao.VISTORIAS_REGISTRAR,
            Permissao.DANOS_GERENCIAR,
            Permissao.MULTAS_GERENCIAR,
            Permissao.CAUCOES_GERENCIAR,
            Permissao.FINANCEIRO_LER,
            Permissao.FINANCEIRO_RECEBER,
            Permissao.FINANCEIRO_ESTORNAR,
            Permissao.RELATORIOS_LER,
            Permissao.AUDITORIA_LER,
            Permissao.SESSOES_GERENCIAR,
        }
    ),
    "cliente": frozenset(
        {
            Permissao.ALUGUEIS_CRIAR,
            Permissao.ALUGUEIS_PROPRIOS_LER,
            Permissao.ALUGUEIS_DEVOLVER,
            Permissao.RESERVAS_CRIAR,
            Permissao.RESERVAS_PROPRIAS_LER,
            Permissao.RESERVAS_CANCELAR,
            Permissao.CONTA_RENOMEAR,
            Permissao.SESSOES_GERENCIAR,
        }
    ),
}


def _normalizar_role(role):
    valor = getattr(
        role,
        "value",
        role,
    )

    return str(valor).strip().lower()


def permissoes_do_role(role):
    return _PERMISSOES_POR_ROLE.get(
        _normalizar_role(role),
        frozenset(),
    )


def possui_permissao(
    role,
    permissao,
):
    if not isinstance(
        permissao,
        Permissao,
    ):
        try:
            permissao = Permissao(
                str(permissao)
            )
        except ValueError:
            return False

    return permissao in permissoes_do_role(
        role
    )


def listar_permissoes(role):
    return sorted(
        permissao.value
        for permissao
        in permissoes_do_role(role)
    )
