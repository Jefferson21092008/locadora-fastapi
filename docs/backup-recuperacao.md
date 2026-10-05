# Backup e recuperação

A Etapa 21 formaliza um procedimento de backup e restore para a Locadora sem
transformar o filesystem do Web Service em fonte de verdade.

## Princípios

1. PostgreSQL/Neon continua sendo a fonte de verdade em produção.
2. Redis/Valkey guarda apenas cache e rate limit; não precisa entrar no backup.
3. Backups locais não são versionados nem copiados para a imagem Docker.
4. Um backup só é considerado utilizável depois de passar na verificação.
5. Restore é uma operação destrutiva e exige confirmação explícita.
6. O teste de recuperação deve usar primeiro um banco descartável.

## CLI operacional

O módulo `modulos.backup_cli` funciona sem depender das credenciais de admin/JWT
porque usa somente a URL do banco necessária à operação.

### Criar

```bash
python -m modulos.backup_cli criar
```

Por padrão, a URL vem primeiro de `LOCADORA_BACKUP_DATABASE_URL` e, se ela não
existir, de `LOCADORA_DATABASE_URL`. Os arquivos vão para `backups/` e são
mantidos os sete backups mais recentes. Em Neon, use preferencialmente a
connection string direta (sem o sufixo `-pooler`) para `pg_dump`/`pg_restore`,
mantendo a URL pooled da aplicação separada da URL operacional de backup.

É possível sobrescrever os valores:

```bash
python -m modulos.backup_cli criar \
  --database-url "postgresql+psycopg://..." \
  --diretorio backups \
  --manter 10
```

Para PostgreSQL, o comando usa `pg_dump` no formato custom (`.dump`), sem owner
e sem privileges. A senha não é colocada na linha de comando: ela é repassada ao
cliente PostgreSQL por variável de ambiente do processo.

No Windows, o utilitário tenta localizar automaticamente instalações em
`C:\Program Files\PostgreSQL\<versão>\bin`. Também é possível configurar:

```text
LOCADORA_PG_DUMP
LOCADORA_PG_RESTORE
```

Para SQLite, o backup usa a API nativa `sqlite3.Connection.backup()` e executa
`PRAGMA integrity_check` antes de considerar o arquivo pronto.

## Metadata e checksum

Cada backup recebe um sidecar:

```text
<arquivo>.metadata.json
```

A metadata contém apenas informações operacionais não secretas:

- backend;
- nome do banco;
- timestamp UTC;
- tamanho do arquivo;
- SHA-256;
- revisão Alembic quando identificável.

Ela não armazena host, URL, usuário ou senha do banco.

## Verificar

```bash
python -m modulos.backup_cli verificar backups/ARQUIVO
```

A verificação confere SHA-256 e tamanho. Depois:

- SQLite executa `PRAGMA integrity_check`;
- PostgreSQL executa `pg_restore --list` para validar a estrutura do dump.

Uma cópia cujo checksum não confere deve ser descartada e refeita.

## Listar e retenção

```bash
python -m modulos.backup_cli listar --diretorio backups
```

Ao criar um backup, a retenção é aplicada automaticamente. O padrão mantém os
sete mais recentes. Também existe limpeza explícita:

```bash
python -m modulos.backup_cli limpar \
  --diretorio backups \
  --manter 7 \
  --confirmar
```

## Restore seguro

O destino é sempre informado explicitamente; o CLI não restaura silenciosamente
sobre `LOCADORA_DATABASE_URL`.

Exemplo SQLite:

```bash
python -m modulos.backup_cli restaurar \
  backups/locadora_sqlite_locadora_YYYYMMDDTHHMMSSZ.sqlite3 \
  --destino-url "sqlite:///dados/restore_teste.db" \
  --confirmar
```

Exemplo PostgreSQL:

```bash
python -m modulos.backup_cli restaurar \
  backups/locadora_postgresql_neondb_YYYYMMDDTHHMMSSZ.dump \
  --destino-url "postgresql+psycopg://USUARIO:SENHA@HOST/BANCO_TESTE" \
  --confirmar
```

O restore PostgreSQL usa `pg_restore` com `--clean --if-exists`, sem owner e sem
privileges, dentro de uma única transação e com `--exit-on-error`.

Por isso, **não use primeiro o banco de produção**. Crie um banco descartável,
restaure, rode as migrations/verificações e confira os dados antes de qualquer
recuperação real.

## Recovery drill recomendado

Execute periodicamente:

1. criar backup;
2. verificar backup;
3. criar banco PostgreSQL descartável;
4. restaurar nesse banco;
5. apontar `LOCADORA_TEST_DATABASE_URL` para o banco restaurado;
6. executar os testes de integração PostgreSQL;
7. confirmar a revisão Alembic;
8. excluir o banco descartável após o teste.

Um backup que nunca foi restaurado é apenas uma hipótese de recuperação.

## Produção com Neon

O banco de produção atual está no Neon. A recuperação deve ter duas camadas:

- recursos nativos de histórico/restore do provedor para recuperação rápida;
- dumps lógicos independentes criados com este CLI quando for necessário manter
  uma cópia fora da janela de histórico do provedor.

Antes de uma operação destrutiva em produção, prefira recuperar ou criar uma
cópia isolada no Neon e validar o estado dos dados. Depois, se necessário, faça
recuperação parcial ou restauração completa de forma controlada.

A janela de retenção e os recursos disponíveis variam conforme o plano e a
configuração do projeto Neon; confirme isso no painel antes de depender de um
ponto histórico específico. Para os dumps lógicos, mantenha uma connection
string direta separada em `LOCADORA_BACKUP_DATABASE_URL`; ela é segredo e nunca
deve ser versionada.

## Render

O Web Service Free do Render usa filesystem efêmero. Portanto, **não grave o
único backup em `backups/` dentro do serviço de produção**: esse arquivo pode ser
perdido em restart, spin-down ou deploy.

O diretório local desta etapa é apropriado para:

- desenvolvimento;
- operação manual em máquina confiável;
- geração temporária antes de mover o arquivo para armazenamento durável.

Automatizar cópias para object storage exige credenciais e política de retenção
próprias e não foi inventado nesta etapa. Dumps de produção podem conter dados
pessoais e financeiros; armazene-os com acesso restrito e criptografia no
armazenamento escolhido.

## O que não entra no backup

Redis/Valkey não entra no procedimento porque contém apenas dados reconstruíveis
(cache e rate limit). A fila de background jobs, notificações, financeiro,
reservas e demais dados persistentes estão no PostgreSQL e entram no dump.
