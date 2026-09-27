from types import SimpleNamespace

import pytest

from fastapi import HTTPException

from api.dependencias import exigir_permissao
from modulos.permissoes import Permissao


def _usuario(role):
    return SimpleNamespace(
        id=1,
        usuario="teste",
        ativo=True,
        role=SimpleNamespace(
            value=role
        ),
    )


def test_dependencia_permite_role_com_permissao():
    dependencia = exigir_permissao(
        Permissao.RELATORIOS_LER
    )
    usuario = _usuario("admin")

    assert dependencia(
        usuario=usuario
    ) is usuario


def test_dependencia_bloqueia_role_sem_permissao():
    dependencia = exigir_permissao(
        Permissao.RELATORIOS_LER
    )

    with pytest.raises(
        HTTPException
    ) as erro:
        dependencia(
            usuario=_usuario(
                "cliente"
            )
        )

    assert erro.value.status_code == 403
    assert erro.value.detail == (
        "Usuário sem permissão "
        "para esta operação."
    )
