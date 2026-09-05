# ================================================================
# CORES
# ================================================================

VERMELHO = "\033[1;31m"
VERDE = "\033[1;32m"
AMARELO = "\033[1;33m"
AZUL = "\033[1;34m"
CIANO = "\033[1;36m"
BRANCO = "\033[1;37m"
RESET = "\033[m"


# ================================================================
# FUNÇÕES DE ENTRADA
# ================================================================

def leia_int(mensagem):
    while True:
        try:
            valor = int(input(mensagem))
            return valor

        except ValueError:
            print(
                f"{VERMELHO}"
                "Erro! Digite um número inteiro."
                f"{RESET}"
            )


def leia_float(mensagem):
    while True:
        try:
            valor = input(mensagem).strip()

            # Permite:
            # 10.50
            # ou
            # 10,50
            valor = valor.replace(",", ".")

            return float(valor)

        except ValueError:
            print(
                f"{VERMELHO}"
                "Erro! Digite um número válido."
                f"{RESET}"
            )


# ================================================================
# TÍTULO
# ================================================================

def titulo(texto):
    tamanho = len(texto) + 8

    print(
        f"\n{AZUL}"
        f"{'=' * tamanho}"
    )

    print(
        f"=== {texto} ==="
    )

    print(
        f"{'=' * tamanho}"
        f"{RESET}"
    )


# ================================================================
# MENU PRINCIPAL
# ================================================================

def menu_principal():
    print(
        f"""
{AZUL}=========== MENU PRINCIPAL ==========={RESET}

{BRANCO}[ 1 ] Login do cliente
[ 2 ] Criar conta
[ 3 ] Área do administrador
[ 4 ] Encerrar programa{RESET}
"""
    )

    return leia_int(
        f"{BRANCO}"
        "Escolha uma opção: "
        f"{RESET}"
    )


# ================================================================
# MENU DO CLIENTE
# ================================================================

def menu_cliente():
    print(
        f"""
{AZUL}=========== ÁREA DO CLIENTE ==========={RESET}

{BRANCO}[ 1 ] Ver veículos disponíveis
[ 2 ] Buscar veículo
[ 3 ] Alugar veículo
[ 4 ] Devolver veículo
[ 5 ] Ver meus aluguéis
[ 6 ] Meus dados
[ 7 ] Alterar senha
[ 8 ] Sair{RESET}
"""
    )

    return leia_int(
        f"{BRANCO}"
        "Escolha uma opção: "
        f"{RESET}"
    )


# ================================================================
# MENU DO ADMINISTRADOR
# ================================================================

def menu_admin():
    print(
        f"""
{AZUL}=========== ÁREA DO ADMINISTRADOR ==========={RESET}

{BRANCO}[ 1 ] Cadastrar veículo
[ 2 ] Editar veículo
[ 3 ] Desativar veículo
[ 4 ] Reativar veículo
[ 5 ] Mostrar frota
[ 6 ] Ver veículos alugados
[ 7 ] Relatórios
[ 8 ] Ver clientes
[ 9 ] Desativar cliente
[ 10 ] Reativar cliente
[ 11 ] Abrir manutenção
[ 12 ] Finalizar manutenção
[ 13 ] Manutenções ativas
[ 14 ] Histórico de manutenção
[ 15 ] Alterar senha do administrador
[ 16 ] Sair{RESET}
"""
    )

    return leia_int(
        f"{BRANCO}"
        "Escolha uma opção: "
        f"{RESET}"
    )