import hashlib
import hmac
import secrets


class SegurancaSenha:
    ALGORITMO = "pbkdf2_sha256"

    ITERACOES = 600_000

    TAMANHO_SALT = 16

    # ================================================================
    # CRIAÇÃO
    # ================================================================

    @classmethod
    def gerar_hash(
        cls,
        senha,
    ):
        salt = secrets.token_bytes(
            cls.TAMANHO_SALT
        )

        hash_senha = hashlib.pbkdf2_hmac(
            "sha256",
            senha.encode(
                "utf-8"
            ),
            salt,
            cls.ITERACOES,
        )

        return (
            f"{cls.ALGORITMO}"
            f"${cls.ITERACOES}"
            f"${salt.hex()}"
            f"${hash_senha.hex()}"
        )

    # ================================================================
    # VERIFICAÇÃO
    # ================================================================

    @classmethod
    def verificar(
        cls,
        senha,
        hash_salvo,
    ):
        if not hash_salvo:
            return False

        if cls.eh_hash_atual(
            hash_salvo
        ):
            return cls._verificar_pbkdf2(
                senha,
                hash_salvo,
            )

        if cls.eh_hash_legado(
            hash_salvo
        ):
            return cls._verificar_sha256(
                senha,
                hash_salvo,
            )

        return False

    # ================================================================
    # PBKDF2
    # ================================================================

    @classmethod
    def _verificar_pbkdf2(
        cls,
        senha,
        hash_salvo,
    ):
        try:
            (
                algoritmo,
                iteracoes,
                salt_hex,
                hash_hex,
            ) = hash_salvo.split(
                "$"
            )

            if (
                algoritmo
                != cls.ALGORITMO
            ):
                return False

            salt = bytes.fromhex(
                salt_hex
            )

            hash_esperado = (
                bytes.fromhex(
                    hash_hex
                )
            )

            hash_informado = (
                hashlib.pbkdf2_hmac(
                    "sha256",
                    senha.encode(
                        "utf-8"
                    ),
                    salt,
                    int(
                        iteracoes
                    ),
                )
            )

            return hmac.compare_digest(
                hash_informado,
                hash_esperado,
            )

        except (
            ValueError,
            TypeError,
        ):
            return False

    # ================================================================
    # SHA-256 ANTIGO
    # ================================================================

    @staticmethod
    def _verificar_sha256(
        senha,
        hash_salvo,
    ):
        hash_informado = (
            hashlib.sha256(
                senha.encode(
                    "utf-8"
                )
            ).hexdigest()
        )

        return hmac.compare_digest(
            hash_informado,
            hash_salvo,
        )

    # ================================================================
    # IDENTIFICAÇÃO DO FORMATO
    # ================================================================

    @classmethod
    def eh_hash_atual(
        cls,
        hash_salvo,
    ):
        return str(
            hash_salvo
        ).startswith(
            f"{cls.ALGORITMO}$"
        )

    @staticmethod
    def eh_hash_legado(
        hash_salvo,
    ):
        hash_salvo = str(
            hash_salvo
        )

        if len(hash_salvo) != 64:
            return False

        try:
            int(
                hash_salvo,
                16,
            )

            return True

        except ValueError:
            return False