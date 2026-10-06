class ErroAplicacao(Exception):
    """Erro base da aplicação."""

    def __init__(
        self,
        mensagem,
    ):
        self.mensagem = mensagem

        super().__init__(
            mensagem
        )


class RegraDeNegocio(
    ErroAplicacao
):
    """Regra de negócio inválida."""

    pass


class ConflitoConcorrencia(
    RegraDeNegocio
):
    """Operação rejeitada porque o estado mudou concorrentemente."""

    pass


class RecursoNaoEncontrado(
    ErroAplicacao
):
    """Recurso solicitado não existe."""

    pass
