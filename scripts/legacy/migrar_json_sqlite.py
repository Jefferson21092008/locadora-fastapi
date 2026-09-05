import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

from modulos.banco import BancoDados


BASE_DIR = Path(__file__).resolve().parent
DADOS_DIR = BASE_DIR / "dados"


# ================================================================
# LEITURA DOS JSONS
# ================================================================

def carregar_json(nome_arquivo):
    caminho = DADOS_DIR / nome_arquivo

    if not caminho.exists():
        return []

    with open(
        caminho,
        "r",
        encoding="utf-8",
    ) as arquivo:
        return json.load(arquivo)


# ================================================================
# COMPATIBILIDADE COM DADOS ANTIGOS
# ================================================================

def gerar_hash(senha):
    return hashlib.sha256(
        senha.encode("utf-8")
    ).hexdigest()


def preparar_email(cliente):
    """
    Alguns clientes antigos podem não possuir e-mail.

    Como a nova tabela exige e-mail UNIQUE e NOT NULL,
    criamos um endereço temporário apenas para registros antigos.
    """

    email = cliente.get(
        "email",
        "",
    ).strip()

    if email:
        return email

    return (
        f"legacy_{cliente['id']}"
        "@sem-email.local"
    )


def obter_cliente_id(
    aluguel,
    clientes,
):
    cliente_id = aluguel.get(
        "cliente_id",
        0,
    )

    # Formato atual
    if any(
        cliente.get("id") == cliente_id
        for cliente in clientes
    ):
        return cliente_id

    # Compatibilidade com histórico antigo
    usuario = aluguel.get(
        "cliente_usuario",
        aluguel.get("cliente", ""),
    )

    encontrados = [
        cliente
        for cliente in clientes
        if cliente.get(
            "usuario",
            "",
        ).lower() == usuario.lower()
    ]

    if len(encontrados) == 1:
        return encontrados[0]["id"]

    return None


def obter_veiculo_id(
    aluguel,
    veiculos,
):
    veiculo_id = aluguel.get(
        "veiculo_id",
        0,
    )

    # Formato atual
    if any(
        veiculo.get("id") == veiculo_id
        for veiculo in veiculos
    ):
        return veiculo_id

    # Compatibilidade com histórico antigo
    modelo = aluguel.get(
        "veiculo_modelo",
        aluguel.get("modelo", ""),
    ).lower()

    tipo = aluguel.get(
        "veiculo_tipo",
        aluguel.get("tipo", ""),
    ).lower()

    encontrados = [
        veiculo
        for veiculo in veiculos
        if (
            veiculo.get(
                "modelo",
                "",
            ).lower() == modelo
            and veiculo.get(
                "tipo",
                "",
            ).lower() == tipo
        )
    ]

    if len(encontrados) == 1:
        return encontrados[0]["id"]

    return None


def preparar_datas(aluguel):
    data_inicio = aluguel.get(
        "data_inicio"
    )

    data_prevista = aluguel.get(
        "data_prevista"
    )

    data_fim = aluguel.get(
        "data_fim"
    )

    dias = int(
        aluguel.get(
            "dias",
            1,
        )
    )

    if data_inicio and not data_prevista:
        inicio = date.fromisoformat(
            data_inicio
        )

        data_prevista = (
            inicio
            + timedelta(days=dias)
        ).isoformat()

    return (
        data_inicio,
        data_prevista,
        data_fim,
    )


# ================================================================
# MIGRAÇÃO
# ================================================================

def migrar():
    clientes = carregar_json(
        "clientes.json"
    )

    veiculos = carregar_json(
        "veiculos.json"
    )

    alugueis = carregar_json(
        "alugueis.json"
    )

    banco = BancoDados()

    # Garante que as tabelas existem.
    banco.criar_tabelas()

    conn = banco.conectar()

    try:
        cursor = conn.cursor()

        # ============================================================
        # SEGURANÇA
        # ============================================================

        cursor.execute(
            "SELECT COUNT(*) FROM clientes"
        )
        clientes_existentes = (
            cursor.fetchone()[0]
        )

        cursor.execute(
            "SELECT COUNT(*) FROM veiculos"
        )
        veiculos_existentes = (
            cursor.fetchone()[0]
        )

        cursor.execute(
            "SELECT COUNT(*) FROM alugueis"
        )
        alugueis_existentes = (
            cursor.fetchone()[0]
        )

        if (
            clientes_existentes > 0
            or veiculos_existentes > 0
            or alugueis_existentes > 0
        ):
            print(
                "\nMigração cancelada."
            )
            print(
                "O banco já possui dados."
            )
            print(
                "Isso evita registros duplicados."
            )
            return

        # ============================================================
        # CLIENTES
        # ============================================================

        for cliente in clientes:
            senha_hash = cliente.get(
                "senha_hash"
            )

            # Compatibilidade com dados muito antigos
            if senha_hash is None:
                senha_hash = gerar_hash(
                    cliente.get(
                        "senha",
                        "",
                    )
                )

            cursor.execute(
                """
                INSERT INTO clientes (
                    id,
                    nome,
                    usuario,
                    email,
                    senha_hash,
                    ativo
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    cliente["id"],
                    cliente.get(
                        "nome",
                        "",
                    ),
                    cliente.get(
                        "usuario",
                        "",
                    ),
                    preparar_email(
                        cliente
                    ),
                    senha_hash,
                    int(
                        cliente.get(
                            "ativo",
                            True,
                        )
                    ),
                ),
            )

        # ============================================================
        # VEÍCULOS
        # ============================================================

        for veiculo in veiculos:
            cursor.execute(
                """
                INSERT INTO veiculos (
                    id,
                    tipo,
                    modelo,
                    ano,
                    diaria,
                    preco_km,
                    disponivel,
                    alugado_por,
                    ativo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    veiculo["id"],
                    veiculo.get(
                        "tipo",
                        "",
                    ),
                    veiculo.get(
                        "modelo",
                        "",
                    ),
                    int(
                        veiculo.get(
                            "ano",
                            1900,
                        )
                    ),
                    float(
                        veiculo.get(
                            "diaria",
                            0,
                        )
                    ),
                    float(
                        veiculo.get(
                            "preco_km",
                            0,
                        )
                    ),
                    int(
                        veiculo.get(
                            "disponivel",
                            True,
                        )
                    ),
                    veiculo.get(
                        "alugado_por"
                    ),
                    int(
                        veiculo.get(
                            "ativo",
                            True,
                        )
                    ),
                ),
            )

        # ============================================================
        # ALUGUÉIS
        # ============================================================

        alugueis_migrados = 0
        alugueis_ignorados = 0

        for aluguel in alugueis:

            cliente_id = obter_cliente_id(
                aluguel,
                clientes,
            )

            veiculo_id = obter_veiculo_id(
                aluguel,
                veiculos,
            )

            # Não inventamos relacionamentos.
            if (
                cliente_id is None
                or veiculo_id is None
            ):
                alugueis_ignorados += 1

                print(
                    "\nAVISO:"
                    f" aluguel #{aluguel.get('id')}"
                    " não pôde ser relacionado"
                    " a cliente/veículo."
                )

                continue

            (
                data_inicio,
                data_prevista,
                data_fim,
            ) = preparar_datas(
                aluguel
            )

            # A tabela exige essas datas.
            if (
                not data_inicio
                or not data_prevista
            ):
                alugueis_ignorados += 1

                print(
                    "\nAVISO:"
                    f" aluguel #{aluguel.get('id')}"
                    " possui datas antigas"
                    " incompatíveis."
                )

                continue

            cursor.execute(
                """
                INSERT INTO alugueis (
                    id,
                    cliente_id,
                    veiculo_id,
                    cliente_usuario,
                    cliente_nome,
                    veiculo_tipo,
                    veiculo_modelo,
                    dias,
                    status,
                    km,
                    pagamento,
                    valor,
                    data_inicio,
                    data_prevista,
                    data_fim,
                    dias_atraso,
                    multa
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    aluguel["id"],
                    cliente_id,
                    veiculo_id,

                    aluguel.get(
                        "cliente_usuario",
                        aluguel.get(
                            "cliente",
                            "",
                        ),
                    ),

                    aluguel.get(
                        "cliente_nome",
                        aluguel.get(
                            "nome",
                            "",
                        ),
                    ),

                    aluguel.get(
                        "veiculo_tipo",
                        aluguel.get(
                            "tipo",
                            "",
                        ),
                    ),

                    aluguel.get(
                        "veiculo_modelo",
                        aluguel.get(
                            "modelo",
                            "",
                        ),
                    ),

                    int(
                        aluguel.get(
                            "dias",
                            1,
                        )
                    ),

                    aluguel.get(
                        "status",
                        "finalizado",
                    ),

                    float(
                        aluguel.get(
                            "km",
                            0,
                        )
                    ),

                    aluguel.get(
                        "pagamento"
                    ),

                    float(
                        aluguel.get(
                            "valor",
                            0,
                        )
                    ),

                    data_inicio,
                    data_prevista,
                    data_fim,

                    int(
                        aluguel.get(
                            "dias_atraso",
                            0,
                        )
                    ),

                    float(
                        aluguel.get(
                            "multa",
                            0,
                        )
                    ),
                ),
            )

            alugueis_migrados += 1

        # ============================================================
        # CONFIRMAÇÃO
        # ============================================================

        conn.commit()

        print(
            "\n=============================="
        )
        print(
            " MIGRAÇÃO CONCLUÍDA"
        )
        print(
            "=============================="
        )

        print(
            f"Clientes: {len(clientes)}"
        )

        print(
            f"Veículos: {len(veiculos)}"
        )

        print(
            f"Aluguéis migrados: "
            f"{alugueis_migrados}"
        )

        print(
            f"Aluguéis ignorados: "
            f"{alugueis_ignorados}"
        )

    except Exception as erro:
        conn.rollback()

        print(
            "\nErro durante a migração."
        )

        print(
            f"Todas as alterações foram "
            f"desfeitas."
        )

        print(
            f"Erro: {erro}"
        )

    finally:
        conn.close()


# ================================================================
# EXECUÇÃO
# ================================================================

if __name__ == "__main__":
    migrar()