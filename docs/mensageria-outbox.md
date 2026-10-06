# Etapa 27 — Mensageria durável com Transactional Outbox

A Etapa 27 transforma os eventos internos da Etapa 26 em mensagens duráveis sem
introduzir um broker externo ou microserviços. A estratégia usada é
**Transactional Outbox**: a alteração de negócio e o registro do evento são
confirmados na mesma transação SQL.

## Problema resolvido

Publicar um evento apenas depois do `commit` deixa uma janela de perda:

```text
1. banco confirma aluguel
2. processo cai
3. evento aluguel.criado nunca é entregue
```

Tentar publicar antes do `commit` também é incorreto, porque o consumidor pode
reagir a uma alteração que depois sofre rollback.

Com a outbox:

```text
Service
  ↓ prepara EventoAplicacao
Repository / transação
  ├── altera tabelas de negócio
  ├── grava eventos_outbox
  └── COMMIT único
          ↓
     OutboxWorker
          ↓
 BarramentoEventos
          ↓
       handlers
```

Se o processo cair depois do commit, a mensagem continua em `eventos_outbox` e
pode ser retomada pelo worker.

## Persistência atômica

`modulos.outbox.operacao_com_outbox` mantém o lote de eventos associado à
operação atual. Os repositories que realizam mutações chamam
`persistir_eventos_outbox(...)` **antes do mesmo commit** da alteração de
negócio.

Eventos com IDs gerados pelo banco são materializados depois do `flush`, quando
o identificador já existe, mas ainda dentro da transação. Isso é usado em
reservas, aluguéis, manutenções e pagamentos.

Uma falha ao serializar ou inserir o evento causa rollback da transação inteira.
Assim não existe estado em que a alteração principal foi confirmada, mas o
registro durável do evento não foi criado.

## Tabela `eventos_outbox`

A migration `20261006_0011_eventos_outbox` cria a tabela com:

- UUID único do evento;
- nome e versão do contrato;
- envelope JSON completo;
- status de processamento;
- número e limite de tentativas;
- instante em que pode ser processado;
- lock lógico, erro anterior e timestamps operacionais.

Estados possíveis:

```text
pendente → processando → processado
                │
                ├── erro temporário → pendente
                └── limite atingido → falhou
```

O índice `idx_eventos_outbox_status_disponivel` prioriza a busca das mensagens
prontas para consumo.

## Reserva concorrente de mensagens

No PostgreSQL, `OutboxRepository.reservar_proxima()` usa:

```sql
SELECT ... FOR UPDATE SKIP LOCKED
```

Isso permite que mais de um worker dispute a fila sem selecionar a mesma linha
ao mesmo tempo. A propriedade será importante na etapa de escala horizontal.

SQLite continua útil para testes comuns, mas não reproduz exatamente a semântica
de lock do PostgreSQL.

## Entrega e retry

`OutboxService` entrega o mesmo `EventoAplicacao` ao barramento usando o UUID
persistido. Se algum handler falhar, a mensagem não é marcada como processada.
Ela volta para `pendente` com backoff exponencial limitado.

Configuração padrão:

```text
retry 1: 5 s
retry 2: 10 s
retry 3: 20 s
retry 4: 40 s
retry 5: falha definitiva se o limite for atingido
```

Os valores de base e teto são configuráveis. Um lock de `processando` que fica
abandonado por queda do processo também é recuperado depois do timeout.

## Semântica de entrega

A garantia é **at-least-once**. Existe uma janela inevitável em que um handler
pode concluir e o processo morrer antes de marcar a mensagem como processada.
Nesse caso o evento será entregue novamente.

Por isso handlers que recebem eventos duráveis devem ser idempotentes. O handler
atual de invalidação do cache do dashboard já possui essa característica:
invalidar a mesma chave duas vezes produz o mesmo estado final.

A outbox não promete `exactly-once` para efeitos externos.

## Barramento em modo adiado

O `Container` usa `BarramentoEventos(despacho_imediato=False)`. Services ainda
entregam o evento ao barramento depois que a operação termina, mas o barramento
não executa handlers naquele caminho. O `OutboxWorker` força o despacho somente
ao consumir a mensagem persistida.

Isso evita executar o mesmo efeito secundário imediatamente e depois outra vez
pela fila. Barramentos criados diretamente em testes continuam com despacho
imediato por padrão, preservando testes unitários simples.

## Worker

`modulos.outbox_worker.OutboxWorker` roda em thread no processo web quando
`LOCADORA_MENSAGERIA_ENABLED=true`. Ele também pode ser executado manualmente:

```bash
python -m modulos.outbox_worker --once
python -m modulos.outbox_worker
```

Variáveis:

```text
LOCADORA_MENSAGERIA_ENABLED
LOCADORA_MENSAGERIA_INTERVALO_SEGUNDOS
LOCADORA_MENSAGERIA_LOTE
LOCADORA_MENSAGERIA_TIMEOUT_BLOQUEIO_SEGUNDOS
LOCADORA_MENSAGERIA_RETRY_BASE_SEGUNDOS
LOCADORA_MENSAGERIA_RETRY_MAX_SEGUNDOS
```

No Docker local e em produção a mensageria fica habilitada. Em staging ela fica
desabilitada por padrão para não executar side effects automaticamente sem uma
decisão explícita de homologação.

## Relação com background jobs

A outbox e `tarefas_background` têm objetivos diferentes:

- **outbox** registra fatos produzidos por transações de negócio;
- **background jobs** representam comandos/tarefas futuras, como sincronizar
  notificações.

Ambos possuem retry e reserva concorrente, mas não devem ser misturados. Um
evento diz “algo aconteceu”; um job diz “faça algo”.

## Broker externo

A etapa não adiciona RabbitMQ, Kafka, SQS ou Redis Streams. A outbox cria a
fronteira correta para isso no futuro: um novo publisher pode consumir
`eventos_outbox` e entregar a um broker sem mudar os services de domínio.

Adicionar infraestrutura distribuída antes da Etapa 28 não traria benefício
proporcional ao tamanho atual da aplicação.

## Testes importantes

A suíte cobre:

- persistência e reconstrução do mesmo envelope/UUID;
- unicidade de `id_evento`;
- reserva, retry, conclusão e recuperação de lock expirado;
- rollback da mutação quando a gravação do evento falha;
- barramento em modo adiado e despacho forçado pelo worker;
- criação do worker a partir do `Container`;
- migration e metadata da tabela `eventos_outbox`.

Em PostgreSQL, a migration deve ser validada junto da suíte de integração antes
do merge.
