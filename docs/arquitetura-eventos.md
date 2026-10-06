# Etapa 26 — Arquitetura orientada a eventos

Esta etapa introduz eventos de aplicação dentro do monólito da Locadora. O
objetivo é reduzir acoplamento entre o fluxo que conclui uma regra de negócio e
as reações secundárias a essa mudança, sem transformar o projeto em
microserviços e sem adicionar um broker externo antes de haver necessidade.

## Princípio usado

Um evento representa um **fato que já aconteceu**. Os services continuam sendo
responsáveis pelas regras de negócio e os repositories continuam sendo
responsáveis pela persistência. Depois que a escrita principal termina com
sucesso, o service publica um evento no barramento interno.

```text
Router
  ↓
Service
  ↓
Repository / transação
  ↓ commit concluído
EventoAplicacao
  ↓
BarramentoEventos
  ├── handler A
  ├── handler B
  └── handler futuro
```

O evento não substitui retorno de função, transação, constraint ou tratamento de
concorrência. As proteções da Etapa 25 continuam sendo a fonte de verdade para
consistência dos dados.

## Envelope dos eventos

`modulos.eventos.EventoAplicacao` define um envelope comum com:

- `id_evento`: UUID gerado para a ocorrência;
- `nome`: fato no padrão `agregado.acao`;
- `versao`: versão do contrato, começando em 1;
- `ocorrido_em`: timestamp UTC com timezone;
- `agregado_tipo` e `agregado_id`: referência ao objeto principal;
- `dados`: snapshot mínimo necessário aos consumidores.

Exemplo conceitual:

```json
{
  "id_evento": "...",
  "nome": "aluguel.finalizado",
  "versao": 1,
  "ocorrido_em": "2026-10-06T03:00:00+00:00",
  "agregado": {
    "tipo": "aluguel",
    "id": 42
  },
  "dados": {
    "cliente_id": 5,
    "veiculo_id": 9,
    "valor": 350.0
  }
}
```

Os payloads usam identificadores e dados operacionais mínimos. Senhas, tokens,
URLs privadas, e-mails e outros segredos não devem ser publicados em eventos.

## Catálogo inicial

A Etapa 26 publica fatos dos fluxos transacionais mais importantes:

- `aluguel.criado`;
- `aluguel.finalizado`;
- `reserva.criada`;
- `reserva.cancelada`;
- `reserva.convertida`;
- `manutencao.aberta`;
- `manutencao.atualizada`;
- `manutencao.finalizada`;
- `pagamento.registrado`;
- `pagamento.estornado`.

A conversão de reserva é publicada somente depois que o aluguel foi persistido
com sucesso. Assim, uma tentativa de aluguel que falha e restaura a reserva não
deixa um evento falso de conversão confirmado.

## Barramento em memória

`BarramentoEventos` é síncrono, em memória e compartilhado pelo `Container`.
Assinaturas são registradas durante a inicialização da aplicação. O barramento
aceita handlers por nome exato e também assinatura coringa `*`, útil para testes,
observabilidade e integrações futuras.

A lista de handlers é protegida por lock durante alterações de assinatura. O
despacho copia a lista antes de executar os callbacks, evitando manter o lock
enquanto código de negócio de um handler roda.

### Política de falhas

Os eventos são publicados depois que a operação principal já foi persistida.
Por esse motivo, uma exceção de handler **não é propagada para o chamador**. O
barramento registra a falha em log, continua os demais handlers e devolve um
`ResultadoPublicacao` com a quantidade de execuções e falhas.

Isso evita um problema perigoso: responder `500` ao cliente depois que o banco
já confirmou a operação. Para efeitos que precisem de garantia de entrega,
retry e durabilidade, a solução correta será a etapa de mensageria/outbox, não
transformar o handler em parte da transação já concluída.

## Primeiro consumidor: invalidação do dashboard

`modulos.event_handlers` registra um consumidor que invalida
`RelatorioService.CHAVE_CACHE_DASHBOARD` quando fatos que alteram as métricas do
dashboard acontecem, como aluguel e manutenção.

```text
aluguel.finalizado
       ↓
BarramentoEventos
       ↓
InvalidarDashboardAoMudarOperacao
       ↓
CacheService.invalidar(...)
       ↓
Redis / fallback do cache
```

Antes, o dashboard dependia apenas do TTL curto ou de atualização manual para
perceber mudanças. Agora essas operações podem invalidar a entrada imediatamente
sem `AluguelService` ou `ManutencaoService` conhecerem Redis ou
`RelatorioService`.

O TTL continua sendo uma proteção adicional. Nem toda mutação da aplicação foi
transformada em evento nesta primeira etapa, e falhas de cache continuam sendo
tratadas como não críticas.

## O que esta etapa deliberadamente não faz

A Etapa 26 **não** adiciona Kafka, RabbitMQ, Redis Streams, SQS ou outro broker.
Também não cria microserviços, não persiste cada evento como event sourcing e
não oferece garantia de entrega entre processos.

Se a API reiniciar, um evento que existia apenas em memória não pode ser
reexecutado. Isso é uma limitação conhecida e intencional do desenho atual.

A próxima etapa pode usar este contrato estável de eventos para introduzir
mensageria durável. O caminho natural é uma estratégia de outbox, para que a
mudança de negócio e o registro do evento durável sejam confirmados na mesma
transação antes de um worker publicar externamente.

## Regras para novos eventos

1. O nome descreve algo que já aconteceu, nunca uma ordem futura.
2. O evento só é publicado depois da persistência principal ter sucesso.
3. O payload deve ser pequeno, versionável e sem segredos.
4. Handlers não devem esconder regra crítica que deveria estar no domínio ou no
   banco.
5. Um handler não deve depender da ordem de execução de outro handler.
6. Side effects que exigem entrega garantida devem esperar a camada durável de
   mensageria.
7. Mudança incompatível no contrato deve criar nova versão do evento.

## Testes

A suíte cobre:

- validação e serialização do envelope;
- assinatura exata e coringa;
- não duplicação e remoção de handlers;
- isolamento de falha de um consumidor;
- publicação somente depois de persistência bem-sucedida;
- eventos de reserva e pagamento;
- registro do barramento único no `Container`;
- invalidação do cache do dashboard por eventos relevantes.

Não há migration nova nesta etapa.
