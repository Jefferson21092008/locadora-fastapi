# Validação final

Este documento registra o estado de qualidade usado no fechamento da trilha principal da Locadora em 06/10/2026.

## Resumo

| Verificação | Resultado |
| --- | ---: |
| Testes convencionais | 844 passed |
| Coverage total | 86,73% |
| Coverage mínima exigida | 85% |
| Testes E2E Chromium | 2 passed |
| Ruff | aprovado |
| pip-audit | nenhuma vulnerabilidade conhecida |
| Testes PostgreSQL de integração | 9 passed |
| Escala horizontal | 2 réplicas observadas |
| Sessão autenticada entre réplicas | validada |
| `git diff --check` | sem erro de whitespace |

Os avisos de conversão `LF → CRLF` exibidos pelo Git no Windows são apenas avisos de final de linha da working copy e não foram tratados como falha de qualidade.

## Suíte convencional

Comando:

```bash
python -m pytest --ignore=tests/e2e
```

Resultado de fechamento:

```text
844 passed
```

A suíte cobre domínio, Services, Repositories SQLAlchemy, API, autenticação, permissões, auditoria, cache, workers, outbox, migrations, concorrência, configuração e infraestrutura.

## Coverage

Comando:

```bash
python -m pytest --ignore=tests/e2e --cov=api --cov=modulos --cov-report=term-missing --cov-fail-under=85
```

Resultado:

```text
TOTAL: 86,73%
Required test coverage of 85% reached.
844 passed
```

Coverage é usado como piso de regressão, não como substituto para testes de comportamento relevantes.

## E2E

Comando:

```bash
python -m pytest tests/e2e --browser chromium -v
```

Resultado:

```text
2 passed
```

Os cenários exercitam o frontend em Chromium, incluindo login válido e tratamento de credenciais inválidas.

## Dependências

Comando:

```bash
python -m pip_audit -r requirements.txt --progress-spinner off
```

Resultado:

```text
No known vulnerabilities found
```

O repositório também usa Dependabot para acompanhar atualizações de Python, GitHub Actions e imagens Docker.

## PostgreSQL real

A suíte de integração PostgreSQL foi executada contra banco descartável real e concluiu:

```text
9 passed
```

Esses testes validam comportamento que SQLite não reproduz completamente, incluindo migrations e mecanismos específicos de concorrência do PostgreSQL.

Nunca use banco de produção em `LOCADORA_TEST_DATABASE_URL`.

## Escala horizontal real

O ambiente foi iniciado com duas réplicas da API e dois workers de outbox:

```bash
docker compose --env-file .env.docker up -d --build --scale api=2 --scale outbox-worker=2
```

A topologia validada continha:

- 2 APIs;
- 1 gateway Nginx;
- 1 PostgreSQL;
- 1 Redis;
- 1 background worker;
- 2 outbox workers.

O validador executou 30 requisições em `/ready`:

```text
réplica A = 15
réplica B = 15
Escala horizontal validada com sucesso.
```

Depois, o mesmo teste foi executado com `--verificar-auth`: um login foi realizado através do gateway e as chamadas autenticadas seguintes atingiram ambas as réplicas.

Resultado:

```text
/ready: 15 / 15
sessão autenticada: 15 / 15
Escala horizontal validada com sucesso.
```

Isso demonstra que a autenticação não depende de estado de sessão mantido apenas na memória de uma única API.

## Healthcheck dos workers

Os workers usam a mesma imagem da API, mas não expõem HTTP. O Compose desabilita explicitamente o healthcheck HTTP herdado nos serviços `background-worker` e `outbox-worker`.

O estado esperado é:

```text
api                 healthy
api                 healthy
gateway             healthy
db                  healthy
cache               healthy
background-worker   Up
outbox-worker       Up
outbox-worker       Up
```

`Up` sem `healthy/unhealthy` é intencional para workers sem endpoint HTTP.

## Testes de carga

A infraestrutura de carga mede:

- throughput;
- taxa de sucesso;
- média e mediana;
- p95 e p99;
- máximo;
- distribuição de status HTTP.

A baseline de 10 usuários × 30 requisições manteve 100% de sucesso nos cenários avaliados. Como o ambiente local apresentou variação significativa entre execuções, otimizações experimentais que não provaram ganho consistente foram revertidas.

Essa decisão faz parte da validação: performance é tratada por medição comparável, não por mudanças especulativas.

## Gate antes de merge

O fluxo de desenvolvimento adotado durante a trilha principal foi:

1. branch de feature;
2. testes focados;
3. Ruff;
4. suíte completa;
5. coverage mínimo de 85%;
6. E2E quando aplicável;
7. `pip-audit`;
8. `git diff --check`;
9. commit somente após tudo verde;
10. Pull Request;
11. GitHub Actions verde;
12. merge em `main`.

Esse processo foi usado para reduzir mudanças grandes sem evidência e manter cada etapa reversível/revisável.
