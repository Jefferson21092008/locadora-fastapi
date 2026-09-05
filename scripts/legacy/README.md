# Scripts legados

Este diretório preserva códigos usados durante etapas antigas da Locadora.

`migrar_json_sqlite.py` representa a migração original dos arquivos JSON para
SQLite. Ele depende da antiga classe `BancoDados`, que já foi removida do fluxo
atual. Portanto, o script é mantido apenas como histórico e não deve ser
executado na arquitetura atual.

A evolução do banco agora é controlada exclusivamente pelas migrations do
Alembic.
