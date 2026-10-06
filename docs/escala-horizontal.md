# Escala horizontal

A Etapa 28 prepara a Locadora para executar mais de uma réplica da API usando o
mesmo PostgreSQL e o mesmo Redis/Valkey. O objetivo não é transformar o projeto
em microserviços: cada réplica continua executando o mesmo monólito modular.

## Desenho

```text
                 ┌──────────────────┐
cliente ────────> │ gateway / Nginx  │
                 └────────┬─────────┘
                          │
               ┌──────────┴──────────┐
               │                     │
          API réplica A         API réplica B
               │                     │
               ├──────────┬──────────┤
               │          │          │
          PostgreSQL    Redis     serviços externos
               │          │
        ┌──────┴───┐      │
        │          │      │
 background    outbox     │
   worker       worker    │
```

As réplicas web são stateless: usuários, refresh sessions, filas, outbox e dados
de negócio vivem no PostgreSQL; cache e rate limiting distribuído usam Redis.
Todas as réplicas precisam usar o mesmo `LOCADORA_JWT_SECRET` e o mesmo namespace
Redis do ambiente.

## Regras de segurança operacional

Quando `LOCADORA_ESCALA_HORIZONTAL_ENABLED=true`, a configuração exige:

- PostgreSQL compartilhado;
- Redis/Valkey compartilhado;
- `LOCADORA_WORKERS_EMBUTIDOS=false`;
- `LOCADORA_CONTAINER_APLICAR_MIGRATIONS=false`.

Além disso, o entrypoint recusa executar migrations dentro de cada réplica se a
escala horizontal estiver habilitada. Migrations devem rodar uma única vez em
uma etapa dedicada antes de liberar as réplicas.

Isso evita que N réplicas iniciem simultaneamente Alembic, scheduler de
notificações e worker da outbox dentro dos processos HTTP.

## Workers separados

O Compose executa `background-worker` e `outbox-worker` como processos separados
da API:

```text
python -m modulos.background_worker
python -m modulos.outbox_worker
```

A outbox e a fila de background continuam usando `FOR UPDATE SKIP LOCKED` no
PostgreSQL. Portanto mais de um worker pode disputar trabalho sem reservar a
mesma linha ao mesmo tempo. A fila de notificações também mantém chave de
deduplicação para o agendamento diário.

A entrega da outbox continua sendo at-least-once. Escalar workers não muda essa
semântica; efeitos duráveis continuam precisando ser idempotentes.

Os containers de worker desabilitam explicitamente o `HEALTHCHECK` HTTP herdado
da imagem da API, porque esses processos não expõem `/health` ou `/ready`. A
saúde operacional deles é representada pelo processo permanecer em execução; se
o processo encerrar, a política `restart: unless-stopped` o reinicia.

## Pool de conexões

Cada réplica possui seu próprio pool SQLAlchemy. Como o total de conexões cresce
aproximadamente com o número de processos, os limites são configuráveis:

```text
LOCADORA_DB_POOL_SIZE
LOCADORA_DB_MAX_OVERFLOW
LOCADORA_DB_POOL_TIMEOUT_SEGUNDOS
```

No Compose horizontal o padrão é `3 + 2` conexões por processo, em vez de deixar
cada nova réplica ampliar o consumo de PostgreSQL sem controle. Em produção, o
valor deve respeitar o limite de conexões do provedor e a quantidade de réplicas
e workers.

## Gateway local

O Compose publica somente o `gateway` na porta do host. As réplicas `api` ficam
na rede interna e expõem a porta 8000 apenas para os outros containers.

O Nginx usa o DNS interno do Docker e `least_conn` para distribuir conexões entre
as réplicas disponíveis.

Para subir duas APIs e dois workers da outbox:

```bash
docker compose --env-file .env.docker up -d --build --scale api=2 --scale outbox-worker=2
```

O background worker normalmente permanece com uma única réplica, pois seu papel
inclui o scheduler diário. A fila é concorrente, mas não existe benefício em
duplicar o scheduler sem necessidade.

## Identidade da réplica

Toda resposta HTTP recebe:

```text
X-Locadora-Instance: api-xxxxxxxxxxxx
```

Quando `LOCADORA_INSTANCIA_ID` não é definido, o identificador público é um hash
curto do hostname do processo. O hostname bruto do container não é exposto.

Os logs HTTP também registram `instance_id`, permitindo descobrir qual réplica
atendeu uma requisição sem registrar headers ou payloads sensíveis.

## Health e readiness

`/health` continua validando a API e o PostgreSQL.

`/ready` valida o banco e, quando a escala horizontal está ativa, também exige
Redis disponível. Uma réplica sem acesso ao estado compartilhado não deve ser
considerada pronta para receber tráfego.

## Teste real local

Depois de subir duas réplicas, execute:

```bash
python -m scripts.horizontal.check_replicas --requests 30 --min-instances 2
```

O script chama `/ready`, coleta `X-Locadora-Instance` e falha se não observar ao
menos duas réplicas.

Para testar que uma sessão criada por uma réplica continua válida quando a
requisição cai em outra réplica, informe credenciais locais somente no terminal:

```bash
set LOCADORA_SCALE_USUARIO=admin
set LOCADORA_SCALE_SENHA=SUA_SENHA_LOCAL
python -m scripts.horizontal.check_replicas --requests 30 --min-instances 2 --verificar-auth
set LOCADORA_SCALE_USUARIO=
set LOCADORA_SCALE_SENHA=
```

A senha não é gravada em arquivo nem impressa pelo script.

Por segurança, o utilitário aceita somente `localhost`/loopback por padrão. Um
alvo remoto exige `--allow-remote` explícito.

## Produção atual

`render.yaml` continua descrevendo o deploy single-instance atual e declara
`LOCADORA_ESCALA_HORIZONTAL_ENABLED=false`. Isso preserva o funcionamento do
serviço existente.

Quando o provedor for configurado com múltiplas réplicas, a promoção deve ser
feita junto com três mudanças operacionais: migrations em etapa única,
`LOCADORA_WORKERS_EMBUTIDOS=false` e workers dedicados. Apenas aumentar o número
de instâncias web sem essas mudanças não é considerado um deploy horizontal
válido.

## Migration

A Etapa 28 não cria tabela nem migration. O Alembic head permanece:

```text
20261006_0011_eventos_outbox
```
