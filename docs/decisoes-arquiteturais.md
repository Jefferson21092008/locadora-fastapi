# Decisões arquiteturais

Este documento registra decisões importantes da Locadora, o problema que cada uma resolve, os trade-offs aceitos e os sinais que justificariam revisitar a escolha.

## 1. Monólito modular em vez de microserviços

### Decisão

Manter a aplicação como um monólito modular, com fronteiras internas entre Router, Service, Repository, domínio, workers e infraestrutura.

### Por quê

O domínio atual é atendido por uma única aplicação e não existe evidência de que partes específicas precisem de deploy, escala, equipe ou disponibilidade independentes. Separar serviços agora adicionaria custo operacional sem resolver um gargalo comprovado.

A base já possui mecanismos que reduzem acoplamento sem exigir rede entre serviços:

- Services separados por capacidade;
- Repositories isolando persistência;
- eventos de aplicação versionados;
- Transactional Outbox;
- workers dedicados;
- PostgreSQL e Redis compartilhados;
- múltiplas réplicas HTTP atrás de gateway.

### Trade-offs aceitos

- o deploy continua sendo de uma aplicação principal;
- uma mudança pode exigir publicar a mesma imagem para capacidades diferentes;
- falhas graves de processo precisam ser tratadas por réplica/worker, não por isolamento de serviço.

### Quando reavaliar

Microserviços passam a ser justificáveis se houver evidência de um ou mais destes sinais:

- equipes diferentes precisam entregar partes do domínio independentemente;
- uma capacidade possui perfil de carga muito diferente do restante;
- requisitos de disponibilidade ou segurança exigem isolamento de processo/deploy;
- ciclos de release independentes passam a reduzir risco de negócio;
- volume de eventos externos exige broker e consumidores independentes;
- fronteiras de domínio estão estáveis o suficiente para evitar um “monólito distribuído”.

## 2. PostgreSQL como fonte de verdade

### Decisão

Persistir no PostgreSQL todo estado que precisa de durabilidade e consistência: dados de negócio, sessões, jobs persistentes, auditoria e eventos outbox.

### Por quê

Esses dados participam de invariantes ou precisam sobreviver a reinícios. Mantê-los no mesmo banco também permite transações atômicas entre a alteração de negócio e a criação de eventos outbox.

### Consequência

O banco é uma dependência central e deve receber atenção em backup, migrations, pool de conexões, concorrência e monitoramento.

## 3. Redis apenas para estado reconstruível

### Decisão

Usar Redis/Valkey para cache e rate limiting distribuído, sem transformá-lo em fonte de verdade do domínio.

### Por quê

Cache e contadores podem ser reconstruídos. Isso permite degradar de forma controlada caso Redis fique indisponível sem perder aluguéis, pagamentos, sessões persistentes ou mensagens duráveis.

### Consequência

O sistema diferencia claramente indisponibilidade de cache de indisponibilidade do banco. Em modo horizontal, `/ready` exige Redis porque ele é necessário para comportamento distribuído consistente.

## 4. Transactional Outbox em vez de broker prematuro

### Decisão

Persistir eventos duráveis em `eventos_outbox` no mesmo commit da mutação e processá-los por worker.

### Por quê

Publicar diretamente em um broker depois do commit cria uma janela em que a alteração pode ser persistida e o evento se perder. Publicar antes do commit cria o problema inverso.

A Outbox elimina essa lacuna usando a transação relacional já necessária para o domínio.

### Semântica

A entrega é **at-least-once**. Portanto, efeitos duráveis devem ser idempotentes.

### Quando considerar broker

Um broker como RabbitMQ, Kafka, SQS ou equivalente faria sentido quando houver múltiplos consumidores independentes, alto volume, integração entre sistemas, retenção/replay específicos ou necessidade de desacoplar a taxa de produção da taxa de consumo em escala maior.

## 5. Locks seletivos e invariantes no banco

### Decisão

Usar `SELECT ... FOR UPDATE` apenas nos fluxos críticos e reforçar invariantes essenciais com constraints/índices do PostgreSQL.

### Por quê

Elevar globalmente o nível de isolamento teria custo maior. Locks localizados serializam apenas operações que realmente disputam o mesmo recurso.

Exemplos:

- operações que disputam o mesmo veículo serializam pela linha do veículo;
- pagamentos concorrentes serializam pela linha do aluguel;
- índice único parcial impede mais de um aluguel ativo por veículo.

### Resultado esperado

Conflitos de negócio são tratados como conflito de concorrência e expostos como HTTP `409`, em vez de permitir estados silenciosamente inconsistentes.

## 6. Workers separados das réplicas HTTP

### Decisão

No modo horizontal, background jobs e outbox usam processos próprios em vez de threads iniciadas por cada réplica FastAPI.

### Por quê

Se cada réplica HTTP iniciasse seus próprios schedulers, aumentar de 2 para 5 APIs também multiplicaria o número de loops de background. Isso acoplaria escala web e escala de processamento.

Separar processos permite dimensionar APIs e workers de forma independente.

## 7. Migrations fora das réplicas horizontais

### Decisão

Bloquear migrations automáticas dentro de cada API quando `LOCADORA_ESCALA_HORIZONTAL_ENABLED=true`.

### Por quê

Alembic é uma operação de mudança de schema, não uma responsabilidade que deve ser executada simultaneamente por N réplicas.

No Compose existe um serviço `migrate` dedicado. Em produção multi-réplica, a migration deve acontecer em etapa/processo único antes de liberar a nova versão das APIs.

## 8. Pool de banco limitado por processo

### Decisão

Tornar configuráveis `pool_size`, `max_overflow` e timeout do SQLAlchemy para PostgreSQL.

### Por quê

Escala horizontal multiplica conexões. Um pool que parece pequeno em uma instância pode se tornar grande quando multiplicado por APIs e workers.

A capacidade deve ser pensada aproximadamente como:

```text
conexões potenciais ≈ processos × (pool_size + max_overflow)
```

O valor real depende de quais processos usam pool e de como o provedor limita conexões.

## 9. Access token em memória e refresh token HttpOnly

### Decisão

Não persistir access token em `localStorage`/`sessionStorage`. Usar access JWT em memória e refresh token rotativo em cookie `HttpOnly`.

### Por quê

Isso reduz a exposição do token longo ao JavaScript. A sessão persistente no banco permite revogar refresh tokens e invalidar access tokens vinculados por `sid`.

### Trade-off

Reloads exigem restaurar a sessão por refresh. O frontend implementa esse fluxo e serializa renovações para reduzir corridas.

## 10. Medir antes de otimizar

### Decisão

Manter infraestrutura de benchmark e reverter otimizações que não mostraram ganho consistente.

### Por quê

Resultados locais mostraram variação relevante entre execuções. Duas alterações de consulta foram testadas e não demonstraram melhoria estável em p95/p99.

A decisão foi manter o código mais simples e preservar o runner de carga para futuras medições em ambiente controlado.

## 11. Deploy público simples, arquitetura evolutiva

### Decisão

Manter o deploy público atual simples, em single-instance, embora o código tenha sido validado para múltiplas réplicas.

### Por quê

Escala horizontal deve responder a necessidade de capacidade/disponibilidade, não ser ativada apenas para demonstrar complexidade. O projeto prova a arquitetura em Docker sem impor custo operacional desnecessário ao ambiente público atual.

## Resumo

O princípio comum às decisões é: **adicionar complexidade somente quando ela resolve um problema observável**.

A Locadora já possui pontos de extensão para crescer — eventos, outbox, workers, cache distribuído, readiness, pool configurável e réplicas HTTP — sem antecipar custos de uma arquitetura distribuída completa.
