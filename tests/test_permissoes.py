from types import SimpleNamespace

from modulos.permissoes import (
    Permissao,
    listar_permissoes,
    permissoes_do_role,
    possui_permissao,
)
from modulos.usuarios import Role


def test_admin_recebe_permissoes_administrativas():
    permissoes = permissoes_do_role(
        Role.ADMIN
    )

    assert Permissao.CLIENTES_LER in permissoes
    assert Permissao.VEICULOS_CRIAR in permissoes
    assert Permissao.ALUGUEIS_LER in permissoes
    assert Permissao.MANUTENCOES_LER in permissoes
    assert Permissao.MANUTENCOES_EDITAR in permissoes
    assert Permissao.RESERVAS_LER in permissoes
    assert Permissao.RESERVAS_CANCELAR in permissoes
    assert Permissao.NOTIFICACOES_LER in permissoes
    assert Permissao.VISTORIAS_LER in permissoes
    assert Permissao.VISTORIAS_REGISTRAR in permissoes
    assert Permissao.DANOS_GERENCIAR in permissoes
    assert Permissao.MULTAS_GERENCIAR in permissoes
    assert Permissao.CAUCOES_GERENCIAR in permissoes
    assert Permissao.FINANCEIRO_LER in permissoes
    assert Permissao.FINANCEIRO_RECEBER in permissoes
    assert Permissao.FINANCEIRO_ESTORNAR in permissoes
    assert Permissao.NOTIFICACOES_LER in permissoes
    assert Permissao.RELATORIOS_LER in permissoes
    assert Permissao.AUDITORIA_LER in permissoes


def test_cliente_recebe_apenas_permissoes_do_proprio_fluxo():
    permissoes = permissoes_do_role(
        Role.CLIENTE
    )

    assert Permissao.ALUGUEIS_CRIAR in permissoes
    assert (
        Permissao.ALUGUEIS_PROPRIOS_LER
        in permissoes
    )
    assert Permissao.ALUGUEIS_DEVOLVER in permissoes
    assert Permissao.RESERVAS_CRIAR in permissoes
    assert Permissao.RESERVAS_PROPRIAS_LER in permissoes
    assert Permissao.RESERVAS_CANCELAR in permissoes
    assert Permissao.CONTA_RENOMEAR in permissoes
    assert Permissao.CLIENTES_LER not in permissoes
    assert Permissao.VISTORIAS_LER not in permissoes
    assert Permissao.CAUCOES_GERENCIAR not in permissoes
    assert Permissao.FINANCEIRO_LER not in permissoes
    assert Permissao.RELATORIOS_LER not in permissoes


def test_permissao_aceita_role_com_atributo_value():
    role = SimpleNamespace(
        value="admin"
    )

    assert possui_permissao(
        role,
        Permissao.VEICULOS_EDITAR,
    )


def test_role_desconhecida_nao_recebe_permissoes():
    assert permissoes_do_role(
        "operador-desconhecido"
    ) == frozenset()

    assert not possui_permissao(
        "operador-desconhecido",
        Permissao.CLIENTES_LER,
    )


def test_listar_permissoes_retorna_valores_ordenados():
    permissoes = listar_permissoes(
        Role.CLIENTE
    )

    assert permissoes == sorted(
        permissoes
    )
    assert "conta:renomear" in permissoes
    assert "sessoes:gerenciar" in permissoes
