from datetime import date, timedelta

from sqlalchemy import (
    case,
    func,
    or_,
    select,
)

from modulos.concorrencia import (
    buscar_por_id_para_atualizacao,
)
from modulos.consultas import ResultadoPaginado
from modulos.excecoes import ConflitoConcorrencia
from modulos.models.aluguel_model import AluguelModel
from modulos.models.manutencao_model import ManutencaoModel
from modulos.models.reserva_model import ReservaModel
from modulos.models.veiculo_model import VeiculoModel
from modulos.reservas import Reserva


class ReservaRepository:
    """Acesso às reservas futuras usando SQLAlchemy."""

    def __init__(self, banco_sqlalchemy):
        if banco_sqlalchemy is None:
            raise ValueError(
                "BancoSQLAlchemy é obrigatório."
            )

        self.banco_sqlalchemy = banco_sqlalchemy

    @staticmethod
    def _para_entidade(model):
        if model is None:
            return None

        return Reserva.from_dict(
            {
                "id": model.id,
                "cliente_id": model.cliente_id,
                "cliente_usuario": model.cliente_usuario,
                "cliente_nome": model.cliente_nome,
                "veiculo_id": model.veiculo_id,
                "veiculo_tipo": model.veiculo_tipo,
                "veiculo_modelo": model.veiculo_modelo,
                "data_inicio": model.data_inicio,
                "data_fim": model.data_fim,
                "status": model.status,
                "criada_em": model.criada_em,
                "cancelada_em": model.cancelada_em,
                "convertida_em": model.convertida_em,
            }
        )

    @classmethod
    def _para_entidades(cls, models):
        return [
            cls._para_entidade(model)
            for model in models
        ]

    def registrar(self, reserva):
        dados = reserva.to_dict()
        model = ReservaModel(
            cliente_id=dados["cliente_id"],
            cliente_usuario=dados["cliente_usuario"],
            cliente_nome=dados["cliente_nome"],
            veiculo_id=dados["veiculo_id"],
            veiculo_tipo=dados["veiculo_tipo"],
            veiculo_modelo=dados["veiculo_modelo"],
            data_inicio=dados["data_inicio"],
            data_fim=dados["data_fim"],
            status=dados["status"],
            criada_em=dados["criada_em"],
            cancelada_em=dados.get("cancelada_em"),
            convertida_em=dados.get("convertida_em"),
        )

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            try:
                # A linha do veículo funciona como ponto único de
                # serialização para reserva, aluguel e manutenção.
                veiculo = buscar_por_id_para_atualizacao(
                    sessao,
                    VeiculoModel,
                    dados["veiculo_id"],
                )

                if veiculo is None:
                    raise ConflitoConcorrencia(
                        "O veículo não existe mais."
                    )

                if not veiculo.ativo:
                    raise ConflitoConcorrencia(
                        "O veículo foi desativado enquanto a reserva "
                        "era processada."
                    )

                reserva_conflitante = sessao.scalar(
                    select(ReservaModel).where(
                        ReservaModel.veiculo_id
                        == dados["veiculo_id"],
                        ReservaModel.status == "ativa",
                        ReservaModel.data_inicio < dados["data_fim"],
                        ReservaModel.data_fim > dados["data_inicio"],
                    )
                )

                if reserva_conflitante is not None:
                    raise ConflitoConcorrencia(
                        "O veículo recebeu outra reserva para esse "
                        "período. Atualize a tela e tente novamente."
                    )

                aluguel_conflitante = sessao.scalar(
                    select(AluguelModel).where(
                        AluguelModel.veiculo_id
                        == dados["veiculo_id"],
                        AluguelModel.status == "ativo",
                        AluguelModel.data_inicio < dados["data_fim"],
                        AluguelModel.data_prevista > dados["data_inicio"],
                    )
                )

                if aluguel_conflitante is not None:
                    raise ConflitoConcorrencia(
                        "O veículo entrou em aluguel e passou a "
                        "conflitar com esse período."
                    )

                manutencao = sessao.scalar(
                    select(ManutencaoModel).where(
                        ManutencaoModel.veiculo_id
                        == dados["veiculo_id"],
                        ManutencaoModel.status == "ativa",
                    )
                )

                if manutencao is not None:
                    if not manutencao.data_prevista:
                        raise ConflitoConcorrencia(
                            "O veículo entrou em manutenção sem "
                            "previsão de conclusão."
                        )

                    fim_manutencao = (
                        date.fromisoformat(
                            manutencao.data_prevista
                        )
                        + timedelta(days=1)
                    )
                    inicio_manutencao = date.fromisoformat(
                        manutencao.data_inicio
                    )
                    inicio_reserva = date.fromisoformat(
                        dados["data_inicio"]
                    )
                    fim_reserva = date.fromisoformat(
                        dados["data_fim"]
                    )

                    if (
                        inicio_manutencao < fim_reserva
                        and fim_manutencao > inicio_reserva
                    ):
                        raise ConflitoConcorrencia(
                            "O veículo entrou em manutenção e passou "
                            "a conflitar com esse período."
                        )

                sessao.add(model)
                sessao.flush()
                novo_id = model.id
                sessao.commit()
                return novo_id
            except Exception:
                sessao.rollback()
                raise

    def buscar_por_id(self, id_reserva):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            return self._para_entidade(
                sessao.get(
                    ReservaModel,
                    id_reserva,
                )
            )

    def listar_do_cliente(self, cliente_id):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            comando = (
                select(ReservaModel)
                .where(
                    ReservaModel.cliente_id
                    == cliente_id
                )
                .order_by(
                    ReservaModel.data_inicio.desc(),
                    ReservaModel.id.desc(),
                )
            )
            return self._para_entidades(
                sessao.scalars(
                    comando
                ).all()
            )

    def listar_colecao(self):
        with self.banco_sqlalchemy.criar_sessao() as sessao:
            comando = (
                select(ReservaModel)
                .order_by(
                    ReservaModel.data_inicio.desc(),
                    ReservaModel.id.desc(),
                )
            )
            return self._para_entidades(
                sessao.scalars(
                    comando
                ).all()
            )

    def buscar_conflitante(
        self,
        veiculo_id,
        data_inicio,
        data_fim,
        ignorar_id=None,
    ):
        filtros = [
            ReservaModel.veiculo_id
            == veiculo_id,
            ReservaModel.status
            == "ativa",
            ReservaModel.data_inicio
            < data_fim,
            ReservaModel.data_fim
            > data_inicio,
        ]

        if ignorar_id is not None:
            filtros.append(
                ReservaModel.id
                != ignorar_id
            )

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            comando = (
                select(ReservaModel)
                .where(*filtros)
                .order_by(
                    ReservaModel.data_inicio,
                    ReservaModel.id,
                )
            )
            return self._para_entidade(
                sessao.scalar(comando)
            )

    def possui_ativa_cliente(self, cliente_id):
        hoje = date.today().isoformat()

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            comando = (
                select(
                    func.count(
                        ReservaModel.id
                    )
                )
                .where(
                    ReservaModel.cliente_id
                    == cliente_id,
                    ReservaModel.status
                    == "ativa",
                    ReservaModel.data_fim
                    > hoje,
                )
            )
            return int(
                sessao.scalar(comando)
                or 0
            ) > 0

    def possui_ativa_veiculo(self, veiculo_id):
        hoje = date.today().isoformat()

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            comando = (
                select(
                    func.count(
                        ReservaModel.id
                    )
                )
                .where(
                    ReservaModel.veiculo_id
                    == veiculo_id,
                    ReservaModel.status
                    == "ativa",
                    ReservaModel.data_fim
                    > hoje,
                )
            )
            return int(
                sessao.scalar(comando)
                or 0
            ) > 0

    def atualizar_status(
        self,
        reserva,
        status_esperado=None,
        exigir_sem_aluguel_ativo=False,
    ):
        dados = reserva.to_dict()

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            try:
                existente = sessao.get(
                    ReservaModel,
                    dados["id"],
                )
                if existente is None:
                    raise RuntimeError(
                        "Reserva não encontrada."
                    )

                buscar_por_id_para_atualizacao(
                    sessao,
                    VeiculoModel,
                    existente.veiculo_id,
                )
                model = buscar_por_id_para_atualizacao(
                    sessao,
                    ReservaModel,
                    dados["id"],
                )

                if model is None:
                    raise RuntimeError(
                        "Reserva não encontrada."
                    )

                if (
                    status_esperado is not None
                    and model.status != status_esperado
                ):
                    raise ConflitoConcorrencia(
                        "O estado da reserva mudou enquanto a operação "
                        "era processada."
                    )

                if exigir_sem_aluguel_ativo:
                    aluguel_ativo = sessao.scalar(
                        select(AluguelModel.id).where(
                            AluguelModel.veiculo_id
                            == model.veiculo_id,
                            AluguelModel.status == "ativo",
                        )
                    )
                    if aluguel_ativo is not None:
                        raise ConflitoConcorrencia(
                            "A reserva não pode ser reativada porque o "
                            "veículo já possui aluguel ativo."
                        )

                if (
                    dados["status"] == "ativa"
                    and model.status == "convertida"
                ):
                    outra_reserva = sessao.scalar(
                        select(ReservaModel.id).where(
                            ReservaModel.veiculo_id
                            == model.veiculo_id,
                            ReservaModel.status == "ativa",
                            ReservaModel.id != model.id,
                            ReservaModel.data_inicio < model.data_fim,
                            ReservaModel.data_fim > model.data_inicio,
                        )
                    )
                    if outra_reserva is not None:
                        raise ConflitoConcorrencia(
                            "A reserva não pode ser reativada porque outra "
                            "reserva ocupa o mesmo período."
                        )

                model.status = dados["status"]
                model.cancelada_em = dados.get(
                    "cancelada_em"
                )
                model.convertida_em = dados.get(
                    "convertida_em"
                )
                sessao.commit()

            except Exception:
                sessao.rollback()
                raise

    def consultar(
        self,
        pagina=1,
        por_pagina=12,
        busca="",
        status="todos",
        ordenar="data_inicio",
        direcao="asc",
        cliente_id=None,
    ):
        hoje = date.today().isoformat()
        filtros = []

        if cliente_id is not None:
            filtros.append(
                ReservaModel.cliente_id
                == cliente_id
            )

        termo = str(
            busca or ""
        ).strip().lower()

        if termo:
            filtros.append(
                or_(
                    func.lower(
                        ReservaModel.veiculo_modelo
                    ).contains(termo),
                    func.lower(
                        ReservaModel.veiculo_tipo
                    ).contains(termo),
                    func.lower(
                        ReservaModel.cliente_nome
                    ).contains(termo),
                    func.lower(
                        ReservaModel.cliente_usuario
                    ).contains(termo),
                )
            )

        if status == "ativa":
            filtros.extend(
                [
                    ReservaModel.status
                    == "ativa",
                    ReservaModel.data_fim
                    > hoje,
                ]
            )
        elif status == "expirada":
            filtros.extend(
                [
                    ReservaModel.status
                    == "ativa",
                    ReservaModel.data_fim
                    <= hoje,
                ]
            )
        elif status in {
            "cancelada",
            "convertida",
        }:
            filtros.append(
                ReservaModel.status
                == status
            )

        colunas_ordenacao = {
            "id": ReservaModel.id,
            "data_inicio": (
                ReservaModel.data_inicio
            ),
            "data_fim": (
                ReservaModel.data_fim
            ),
            "veiculo": (
                ReservaModel.veiculo_modelo
            ),
            "cliente": (
                ReservaModel.cliente_nome
            ),
        }
        coluna = colunas_ordenacao.get(
            ordenar,
            ReservaModel.data_inicio,
        )
        ordem = (
            coluna.desc()
            if direcao == "desc"
            else coluna.asc()
        )

        with self.banco_sqlalchemy.criar_sessao() as sessao:
            total = int(
                sessao.scalar(
                    select(
                        func.count(
                            ReservaModel.id
                        )
                    ).where(*filtros)
                )
                or 0
            )

            comando = (
                select(ReservaModel)
                .where(*filtros)
                .order_by(
                    ordem,
                    ReservaModel.id.asc(),
                )
                .offset(
                    (pagina - 1)
                    * por_pagina
                )
                .limit(por_pagina)
            )
            items = self._para_entidades(
                sessao.scalars(
                    comando
                ).all()
            )

            resumo_filtros = []
            if cliente_id is not None:
                resumo_filtros.append(
                    ReservaModel.cliente_id
                    == cliente_id
                )

            resumo = sessao.execute(
                select(
                    func.count(
                        ReservaModel.id
                    ),
                    func.sum(
                        case(
                            (
                                (
                                    ReservaModel.status
                                    == "ativa"
                                )
                                & (
                                    ReservaModel.data_fim
                                    > hoje
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    func.sum(
                        case(
                            (
                                (
                                    ReservaModel.status
                                    == "ativa"
                                )
                                & (
                                    ReservaModel.data_fim
                                    <= hoje
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    func.sum(
                        case(
                            (
                                ReservaModel.status
                                == "cancelada",
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    func.sum(
                        case(
                            (
                                ReservaModel.status
                                == "convertida",
                                1,
                            ),
                            else_=0,
                        )
                    ),
                ).where(
                    *resumo_filtros
                )
            ).one()

        return ResultadoPaginado(
            items=items,
            total=total,
            resumo={
                "total": int(
                    resumo[0] or 0
                ),
                "ativas": int(
                    resumo[1] or 0
                ),
                "expiradas": int(
                    resumo[2] or 0
                ),
                "canceladas": int(
                    resumo[3] or 0
                ),
                "convertidas": int(
                    resumo[4] or 0
                ),
            },
        )
