# Apresentação de portfólio

Este roteiro ajuda a apresentar a Locadora em entrevista de Backend ou Full Stack sem tentar explicar todo o repositório de uma vez.

## Pitch de 30 segundos

> A Locadora é um sistema completo de gestão de veículos que eu usei para evoluir de um projeto Python simples para uma aplicação web com FastAPI, PostgreSQL e arquitetura em camadas. Além das funcionalidades de negócio, implementei autenticação com sessões persistentes, RBAC, auditoria, Redis, jobs, Transactional Outbox, concorrência com locks no PostgreSQL, CI, Docker hardening, testes de carga e escala horizontal com múltiplas réplicas. A principal preocupação foi não adicionar tecnologia só por aparência: cada evolução foi testada e documentada.

## Pitch de 2 minutos

A aplicação cobre clientes, veículos, aluguéis, reservas, manutenção, vistorias, danos, multas, cauções, pagamentos, relatórios e notificações.

No backend, os endpoints FastAPI chamam Services, que concentram regras de aplicação, e Repositories, que isolam SQLAlchemy. Alembic controla o schema. PostgreSQL é a fonte de verdade e Redis é usado apenas para estado reconstruível, como cache e rate limiting.

A autenticação usa access JWT curto em memória no navegador e refresh token rotativo em cookie HttpOnly. As sessões são persistidas no banco e podem ser revogadas. Há RBAC granular, audit logs, rate limiting, headers de segurança e recuperação de senha.

Para consistência, fluxos concorrentes usam locks seletivos no PostgreSQL e constraints no banco. Para efeitos assíncronos, a aplicação registra eventos em Transactional Outbox na mesma transação da mudança de negócio e os processa em workers separados.

A qualidade é validada por pytest, PostgreSQL real, Playwright, Ruff, pip-audit, coverage mínimo e GitHub Actions. No fechamento, foram 844 testes convencionais com 86,73% de coverage e a arquitetura horizontal foi executada com duas APIs atrás de Nginx, compartilhando PostgreSQL e Redis.

## O que abrir primeiro no GitHub

1. `README.md` — visão geral e como executar;
2. `docs/arquitetura.md` — desenho técnico completo;
3. `docs/decisoes-arquiteturais.md` — trade-offs e maturidade de decisão;
4. `modulos/servicos/` — regras de aplicação;
5. `modulos/repositories/` — persistência e concorrência;
6. `modulos/outbox.py` e worker — mensageria durável;
7. `.github/workflows/ci.yml` — gate automatizado;
8. `tests/` — estratégia de validação.

## Cinco pontos fortes para destacar

### 1. Evolução arquitetural consciente

O projeto não nasceu com todas as abstrações. Elas foram introduzidas conforme surgiram problemas concretos: persistência, autorização, observabilidade, concorrência, tarefas assíncronas e escala.

### 2. Segurança aplicada ao fluxo real

Não é apenas “tem JWT”. Há separação entre access/refresh, cookie HttpOnly, rotação de refresh, revogação de sessões, RBAC, rate limiting, recuperação segura, headers, auditoria e cuidado para não registrar secrets.

### 3. Consistência de dados

A aplicação trata corridas reais no PostgreSQL com locks e constraints. Isso é mais importante do que apenas possuir CRUDs funcionais.

### 4. Mensageria sem duplicar infraestrutura cedo demais

Transactional Outbox resolve atomicidade e entrega durável usando PostgreSQL. A arquitetura pode incorporar um broker no futuro sem que ele seja necessário hoje.

### 5. Evidência de qualidade

As decisões são acompanhadas por testes, coverage, E2E, CI, integração PostgreSQL, benchmark e validação real de múltiplas réplicas.

## Perguntas de entrevista e respostas curtas

### “Por que você não usou microserviços?”

Porque não havia necessidade de deploy, escala ou equipes independentes por domínio. Eu preferi manter um monólito modular com fronteiras internas, eventos, outbox e workers. Isso entrega desacoplamento sem pagar antecipadamente o custo de rede, tracing distribuído, autenticação entre serviços e consistência eventual.

### “Por que usar Redis se já existe PostgreSQL?”

Redis atende estado temporário e compartilhado com baixa latência, como cache e rate limit. Dados que precisam de durabilidade continuam no PostgreSQL.

### “Como você evita dois aluguéis simultâneos para o mesmo carro?”

O fluxo revalida estado dentro da transação e usa lock de linha no PostgreSQL. Além disso, existe uma restrição única parcial no banco como última barreira de consistência.

### “O que acontece se o worker cair depois de um aluguel ser salvo?”

O evento durável foi gravado na tabela outbox no mesmo commit. Outro ciclo/worker pode processá-lo depois. A entrega é at-least-once, então handlers duráveis precisam ser idempotentes.

### “Como a sessão funciona com duas APIs?”

As réplicas compartilham o mesmo segredo JWT e o estado persistente de sessões no PostgreSQL. O teste de escala fez login pelo gateway e chamadas autenticadas foram atendidas por ambas as instâncias.

### “Como você sabe que uma otimização melhorou?”

O projeto possui runner de carga e comparador de resultados. Alterações de consulta que não mostraram ganho consistente foram revertidas. A decisão é medir antes e depois com a mesma carga.

## Demonstração técnica sugerida

Em uma apresentação de 5 a 10 minutos:

1. mostre o dashboard e um fluxo de negócio curto;
2. abra o Swagger e mostre o versionamento `/api/v1`;
3. mostre a estrutura Router → Service → Repository;
4. abra uma migration e uma parte do teste PostgreSQL;
5. mostre o workflow do GitHub Actions;
6. mostre `docs/decisoes-arquiteturais.md` e explique por que não adotou microserviços;
7. se houver tempo, suba duas réplicas no Docker e execute `scripts.horizontal.check_replicas`.

## O que não vender como algo que o projeto não é

- o deploy público atual não é multi-réplica;
- os testes E2E atuais não representam toda a aplicação full-stack em navegador;
- a Outbox não é Kafka/RabbitMQ e não tenta ser;
- a baseline de carga local não define capacidade de produção;
- coverage de 86,73% não significa ausência de bugs;
- a arquitetura está preparada para crescer, mas não precisa virar microserviços agora.

Ser explícito sobre essas limitações melhora a credibilidade técnica do projeto.

## Próximas evoluções justificáveis

Se o projeto continuar evoluindo, boas mudanças devem vir de uma necessidade concreta. Exemplos:

- E2E full-stack com banco descartável real;
- métricas Prometheus/OpenTelemetry se houver ambiente para observabilidade contínua;
- object storage e automação de backup fora do servidor;
- deploy multi-réplica real quando custo/disponibilidade justificarem;
- broker externo se surgirem múltiplos consumidores independentes;
- TypeScript/React apenas se a evolução do frontend justificar a troca.
