from datetime import date, timedelta


class Aluguel:
    """Representa um aluguel, ativo ou finalizado."""

    PERCENTUAL_MULTA_ATRASO = 0.20

    def __init__(
        self,
        id_aluguel,
        cliente_id,
        cliente_usuario,
        cliente_nome,
        veiculo_id,
        veiculo_tipo,
        veiculo_modelo,
        dias,
        status="ativo",
        km=0.0,
        pagamento=None,
        valor=0.0,
        data_inicio=None,
        data_prevista=None,
        data_fim=None,
        dias_atraso=0,
        multa=0.0,
    ):
        self.id = id_aluguel

        self.cliente_id = cliente_id
        self.cliente_usuario = cliente_usuario
        self.cliente_nome = cliente_nome

        self.veiculo_id = veiculo_id
        self.veiculo_tipo = veiculo_tipo
        self.veiculo_modelo = veiculo_modelo

        self.dias = dias
        self.status = status

        self.km = km
        self.pagamento = pagamento
        self.valor = valor

        self.data_inicio = (
            data_inicio
            or date.today().isoformat()
        )

        self.data_prevista = (
            data_prevista
            or self.calcular_data_prevista()
        )

        self.data_fim = data_fim

        self.dias_atraso = dias_atraso
        self.multa = multa

    # ================================================================
    # STATUS
    # ================================================================

    @property
    def ativo(self):
        return self.status == "ativo"

    # ================================================================
    # DATAS
    # ================================================================

    def calcular_data_prevista(self):
        inicio = date.fromisoformat(
            self.data_inicio
        )

        prevista = inicio + timedelta(
            days=self.dias
        )

        return prevista.isoformat()

    def calcular_dias_atraso(
        self,
        data_referencia=None,
    ):
        if data_referencia is None:
            data_referencia = date.today()

        elif isinstance(
            data_referencia,
            str,
        ):
            data_referencia = (
                date.fromisoformat(
                    data_referencia
                )
            )

        prevista = date.fromisoformat(
            self.data_prevista
        )

        atraso = (
            data_referencia - prevista
        ).days

        return max(
            atraso,
            0,
        )

    def calcular_multa(
        self,
        diaria,
        data_referencia=None,
    ):
        dias_atraso = (
            self.calcular_dias_atraso(
                data_referencia
            )
        )

        multa_por_dia = (
            diaria
            * self.PERCENTUAL_MULTA_ATRASO
        )

        return (
            dias_atraso
            * multa_por_dia
        )

    # ================================================================
    # CLIENTE
    # ================================================================

    def pertence_ao_cliente(
        self,
        cliente,
    ):
        return (
            self.cliente_id == cliente.id
            or self.cliente_usuario
            == cliente.usuario
        )

    # ================================================================
    # FINALIZAÇÃO
    # ================================================================

    def finalizar(
        self,
        km,
        valor,
        forma_pagamento,
        dias_atraso=0,
        multa=0.0,
    ):
        self.km = km
        self.valor = valor
        self.pagamento = forma_pagamento

        self.dias_atraso = (
            dias_atraso
        )

        self.multa = multa

        self.status = "finalizado"

        self.data_fim = (
            date.today().isoformat()
        )

    # ================================================================
    # JSON
    # ================================================================

    def to_dict(self):
        return {
            "id": self.id,

            "cliente_id": self.cliente_id,
            "cliente_usuario": self.cliente_usuario,
            "cliente_nome": self.cliente_nome,

            "veiculo_id": self.veiculo_id,
            "veiculo_tipo": self.veiculo_tipo,
            "veiculo_modelo": self.veiculo_modelo,

            "dias": self.dias,
            "status": self.status,

            "km": self.km,
            "pagamento": self.pagamento,
            "valor": self.valor,

            "data_inicio": self.data_inicio,
            "data_prevista": self.data_prevista,
            "data_fim": self.data_fim,

            "dias_atraso": self.dias_atraso,
            "multa": self.multa,
        }

    @classmethod
    def from_dict(
        cls,
        dados,
        id_padrao=None,
    ):
        # Formato atual
        if (
            "cliente_usuario" in dados
            or "status" in dados
        ):
            return cls(
                id_aluguel=dados.get(
                    "id",
                    id_padrao,
                ),

                cliente_id=dados.get(
                    "cliente_id",
                    0,
                ),

                cliente_usuario=dados.get(
                    "cliente_usuario",
                    "",
                ),

                cliente_nome=dados.get(
                    "cliente_nome",
                    "",
                ),

                veiculo_id=dados.get(
                    "veiculo_id",
                    0,
                ),

                veiculo_tipo=dados.get(
                    "veiculo_tipo",
                    "",
                ),

                veiculo_modelo=dados.get(
                    "veiculo_modelo",
                    "",
                ),

                dias=dados.get(
                    "dias",
                    0,
                ),

                status=dados.get(
                    "status",
                    "finalizado",
                ),

                km=float(
                    dados.get(
                        "km",
                        0,
                    )
                ),

                pagamento=dados.get(
                    "pagamento"
                ),

                valor=float(
                    dados.get(
                        "valor",
                        0,
                    )
                ),

                data_inicio=dados.get(
                    "data_inicio"
                ),

                data_prevista=dados.get(
                    "data_prevista"
                ),

                data_fim=dados.get(
                    "data_fim"
                ),

                dias_atraso=dados.get(
                    "dias_atraso",
                    0,
                ),

                multa=float(
                    dados.get(
                        "multa",
                        0,
                    )
                ),
            )

        # Compatibilidade com histórico antigo
        return cls(
            id_aluguel=dados.get(
                "id",
                id_padrao,
            ),

            cliente_id=0,

            cliente_usuario=dados.get(
                "cliente",
                "",
            ),

            cliente_nome=dados.get(
                "nome",
                "",
            ),

            veiculo_id=0,

            veiculo_tipo=dados.get(
                "tipo",
                "",
            ),

            veiculo_modelo=dados.get(
                "modelo",
                "",
            ),

            dias=dados.get(
                "dias",
                0,
            ),

            status="finalizado",

            km=float(
                dados.get(
                    "km",
                    0,
                )
            ),

            pagamento=dados.get(
                "pagamento"
            ),

            valor=float(
                dados.get(
                    "valor",
                    0,
                )
            ),
        )

    # ================================================================
    # REPRESENTAÇÃO
    # ================================================================

    def __str__(self):
        return (
            f"Aluguel #{self.id} - "
            f"{self.veiculo_tipo} "
            f"{self.veiculo_modelo} - "
            f"{self.status.upper()}"
        )