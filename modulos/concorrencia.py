from sqlalchemy import select


def buscar_por_id_para_atualizacao(
    sessao,
    model,
    identificador,
):
    """Obtém uma linha para alteração, usando FOR UPDATE quando suportado.

    PostgreSQL serializa as operações concorrentes sobre a mesma linha.
    O SQLAlchemy omite a cláusula em SQLite, que continua útil como banco
    local/teste, mas não oferece o mesmo bloqueio fino do PostgreSQL.

    ``populate_existing`` força a atualização do objeto caso ele já esteja
    no identity map da sessão antes da aquisição do lock.
    """
    comando = (
        select(model)
        .where(model.id == identificador)
        .with_for_update()
        .execution_options(
            populate_existing=True
        )
    )
    return sessao.scalar(comando)
