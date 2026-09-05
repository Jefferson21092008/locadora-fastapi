import hashlib

from modulos.seguranca import (
    SegurancaSenha,
)


def test_gerar_hash_pbkdf2():
    senha = "senha123"

    hash_senha = (
        SegurancaSenha
        .gerar_hash(
            senha
        )
    )

    assert hash_senha != senha

    assert hash_senha.startswith(
        "pbkdf2_sha256$"
    )


def test_hashes_da_mesma_senha_sao_diferentes():
    senha = "senha123"

    hash_1 = (
        SegurancaSenha
        .gerar_hash(
            senha
        )
    )

    hash_2 = (
        SegurancaSenha
        .gerar_hash(
            senha
        )
    )

    assert hash_1 != hash_2


def test_validar_senha_correta():
    senha = "senha123"

    hash_senha = (
        SegurancaSenha
        .gerar_hash(
            senha
        )
    )

    assert (
        SegurancaSenha
        .verificar(
            senha,
            hash_senha,
        )
        is True
    )


def test_rejeitar_senha_errada():
    hash_senha = (
        SegurancaSenha
        .gerar_hash(
            "senha123"
        )
    )

    assert (
        SegurancaSenha
        .verificar(
            "errada123",
            hash_senha,
        )
        is False
    )


def test_aceitar_hash_sha256_legado():
    senha = "senha123"

    hash_antigo = (
        hashlib.sha256(
            senha.encode(
                "utf-8"
            )
        ).hexdigest()
    )

    assert (
        SegurancaSenha
        .verificar(
            senha,
            hash_antigo,
        )
        is True
    )