# Locadora API

[![CI](https://github.com/Jefferson21092008/locadora-fastapi/actions/workflows/ci.yml/badge.svg)](https://github.com/Jefferson21092008/locadora-fastapi/actions/workflows/ci.yml)

Sistema de gerenciamento de locadora de veículos desenvolvido em Python. O mesmo domínio e as mesmas regras de negócio atendem uma interface de linha de comando, uma API REST com FastAPI e um frontend em HTML, CSS e JavaScript.

## Aplicação online

- **Frontend:** https://locadora-fastapi.onrender.com/app/
- **API:** https://locadora-fastapi.onrender.com
- **Swagger:** https://locadora-fastapi.onrender.com/docs
- **Health check:** https://locadora-fastapi.onrender.com/health

A aplicação está publicada no **Render**, usa **PostgreSQL no Neon** e envia e-mails transacionais de recuperação de senha pela **API HTTPS da Brevo**.

## Estado atual

A migração da persistência antiga foi concluída. O fluxo principal da aplicação é:

```text
CLI / FastAPI / Frontend
        ↓
     Container
        ↓
      Services
        ↓
   Repositories
        ↓
  SQLAlchemy ORM
        ↓
SQLite / PostgreSQL
```

`BancoDados`, `GerenciadorDados`, coleções em memória e arquivos JSON não fazem mais parte do fluxo principal. O `BancoSQLAlchemy` centraliza o Engine e a fábrica de sessões. O Alembic controla a criação e a evolução do schema.

O projeto está validado localmente e em produção, com frontend, API, autenticação, banco PostgreSQL, migrations, recuperação de senha e alteração de nome de usuário funcionando de ponta a ponta.

Além das funcionalidades de negócio, a versão atual também possui cobertura mínima obrigatória no CI, documentação da arquitetura, rate limiting em endpoints sensíveis de autenticação, testes E2E de frontend executados em Chromium com Playwright, observabilidade HTTP com logs estruturados e request ID, monitoramento de erros com Sentry e auditoria persistente de ações sensíveis.

A documentação detalhada da arquitetura está disponível em [`docs/arquitetura.md`](docs/arquitetura.md).

A base visual e os tokens compartilhados do frontend estão documentados em [`docs/design-system.md`](docs/design-system.md).

As telas operacionais reutilizam essa base para manter busca, filtros, contagem de resultados, estados vazios e navegação administrativa consistentes. A auditoria também possui uma tela dedicada protegida por RBAC.

## Funcionalidades

- cadastro, consulta, ativação e desativação de clientes;
- cadastro, busca, edição e controle de veículos;
- criação e finalização de aluguéis;
- criação, consulta e cancelamento de reservas futuras de veículos;
- vistorias de retirada/devolução com quilometragem e combustível;
- registro de danos, multas de trânsito e cauções por aluguel;
- cálculo de devolução, quilometragem e multa por atraso;
- liquidação financeira de danos e multas de trânsito com pagamentos adicionais e estornos;
- abertura e finalização de manutenções;
- relatórios administrativos e financeiros;
- autenticação com access token JWT, refresh token rotativo e RBAC com permissões granulares;
- recuperação de senha por e-mail via Brevo API;
- tokens temporários, de uso único e armazenados por hash;
- alteração do nome de usuário pelo próprio cliente, com confirmação da senha atual;
- prevenção de nomes de usuário duplicados;
- atualização transacional do nome de usuário nas tabelas relacionadas;
- CLI e API REST usando a mesma camada de negócio;
- frontend responsivo com design system próprio, login JWT, renovação automática de sessão, dashboard operacional e telas de domínio com busca, filtros e feedback de resultados;
- transações e rollback em operações compostas;
- documentação OpenAPI/Swagger;
- health check para produção;
- migrations automáticas no deploy;
- testes unitários e de integração;
- integração contínua com GitHub Actions;
- rate limiting para login, recuperação e redefinição de senha;
- identificação do cliente atrás de proxy para aplicação dos limites;
- cobertura automatizada de testes com limite mínimo obrigatório no CI;
- testes E2E do frontend com Playwright e Chromium;
- logs HTTP estruturados em JSON com método, caminho, status, duração e request ID;
- cabeçalho `X-Request-ID` em respostas HTTP para correlação;
- eventos importantes de autenticação sem registrar senha, token ou corpo da requisição;
- monitoramento opcional de exceções de produção com Sentry;
- correlação de erros do Sentry com o `request_id` dos logs estruturados;
- audit logs persistentes para ações sensíveis autenticadas;
- rota administrativa `GET /api/v1/auditoria` para consulta do histórico;
- auditoria registra ator, ação, recurso, campos alterados, horário e `request_id`, sem persistir valores sensíveis;
- API versionada sob o prefixo canônico `/api/v1`, mantendo temporariamente as rotas antigas por compatibilidade;
- auditoria de dependências e atualizações automatizadas com Dependabot.

## Tecnologias

- Python 3.14;
- HTML, CSS e JavaScript;
- FastAPI e Uvicorn;
- SQLAlchemy 2;
- Alembic;
- SQLite e PostgreSQL;
- Psycopg 3;
- Docker e Docker Compose;
- Render;
- Neon;
- Brevo Transactional Email API;
- Sentry SDK para monitoramento de erros;
- GitHub Actions;
- Ruff;
- pip-audit;
- Dependabot;
- Pydantic;
- PyJWT;
- python-dotenv;
- pytest;
- pytest-cov;
- Playwright;
- pytest-playwright;
- HTTPX para testes da API e integração HTTPS com a Brevo.

## Estrutura

```text
Locadora/
├── .github/
│   ├── workflows/
│   │   └── ci.yml
│   └── dependabot.yml
├── api/
│   ├── routers/
│   ├── schemas/
│   ├── auditoria.py
│   ├── dependencias.py
│   ├── erros.py
│   ├── main.py
│   ├── monitoramento.py
│   ├── observabilidade.py
│   ├── rate_limit.py
│   └── seguranca.py
├── dados/
│   └── locadora.db
├── frontend/
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── alugueis.js
│   │   ├── api.js
│   │   ├── auditoria.js
│   │   ├── auth.js
│   │   ├── cadastro.js
│   │   ├── clientes.js
│   │   ├── dashboard.js
│   │   ├── esqueci-senha.js
│   │   ├── manutencoes.js
│   │   ├── redefinir-senha.js
│   │   ├── relatorios.js
│   │   ├── reservas.js
│   │   ├── vistorias.js
│   │   └── veiculos.js
│   ├── alugueis.html
│   ├── auditoria.html
│   ├── cadastro.html
│   ├── clientes.html
│   ├── dashboard.html
│   ├── esqueci-senha.html
│   ├── index.html
│   ├── manutencoes.html
│   ├── redefinir-senha.html
│   ├── relatorios.html
│   ├── reservas.html
│   ├── vistorias.html
│   └── veiculos.html
├── docs/
│   └── arquitetura.md
├── migrations/
│   ├── versions/
│   │   ├── 20260903_0001_schema_inicial.py
│   │   ├── 20260927_0002_audit_logs.py
│   │   ├── 20260927_0003_sessoes_refresh.py
│   │   ├── 20260928_0004_manutencao_avancada.py
│   │   ├── 20260928_0005_reservas.py
│   │   └── 20260928_0006_vistorias_ocorrencias.py
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── modulos/
│   ├── cli/
│   ├── models/
│   ├── repositories/
│   ├── servicos/
│   ├── alugueis.py
│   ├── auditoria.py
│   ├── clientes.py
│   ├── config.py
│   ├── container.py
│   ├── database.py
│   ├── excecoes.py
│   ├── interface.py
│   ├── locadora.py
│   ├── manutencoes.py
│   ├── pagamentos.py
│   ├── reservas.py
│   ├── seguranca.py
│   ├── vistorias.py
│   ├── usuarios.py
│   └── veiculos.py
├── scripts/
│   └── legacy/
│       ├── README.md
│       └── migrar_json_sqlite.py
├── tests/
│   ├── e2e/
│   │   ├── conftest.py
│   │   └── test_login.py
│   └── ...
├── .dockerignore
├── .env.docker.example
├── .env.example
├── .gitignore
├── alembic.ini
├── carros.py
├── compose.yaml
├── Dockerfile
├── README.md
├── render.yaml
├── requirements-dev.txt
└── requirements.txt
```

O diretório `scripts/legacy/` preserva apenas o histórico da antiga migração dos arquivos JSON para SQLite. Ele não participa da execução atual da aplicação e pode ser removido futuramente quando esse histórico não for mais necessário.

### Entidades

Os arquivos de domínio em `modulos/` representam clientes, veículos, aluguéis, reservas, manutenções, vistorias, usuários, pagamentos e registros de auditoria. Eles concentram regras próprias do domínio e não executam SQL.

### Models

Os Models em `modulos/models/` descrevem as tabelas do banco com o ORM do SQLAlchemy. Eles ficam separados das entidades para que a regra de negócio não dependa da persistência.

### Repositories

Os Repositories recebem `BancoSQLAlchemy`, abrem sessões e convertem Models ORM em entidades de domínio. Eles são a camada responsável por consultar e alterar o banco.

Operações compostas, como cadastro de cliente com conta ou alteração do nome de usuário, são executadas de forma transacional para evitar estados inconsistentes.

### Services

Os Services executam as regras de negócio e dependem dos contratos oferecidos pelos Repositories. Eles não precisam conhecer detalhes de SQLite, PostgreSQL, SQLAlchemy, HTTP ou interface de terminal.

### Container

O `Container` monta a infraestrutura, cria os Repositories, injeta-os nos Services e compartilha as dependências necessárias entre CLI e API.

## Configuração

Crie e ative um ambiente virtual:

```bash
python -m venv .venv
```

No Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

No Prompt de Comando do Windows:

```bat
.venv\Scripts\activate
```

Instale as dependências da aplicação:

```bash
python -m pip install -r requirements.txt
```

Para desenvolvimento, testes e verificações de qualidade:

```bash
python -m pip install -r requirements-dev.txt
```

Copie `.env.example` para `.env` e configure as variáveis necessárias.

Exemplo mínimo para desenvolvimento local:

```env
LOCADORA_ADMIN_USUARIO=admin
LOCADORA_ADMIN_SENHA=coloque_uma_senha_forte_aqui
LOCADORA_JWT_SECRET=coloque_uma_chave_secreta_forte_aqui
LOCADORA_DATABASE_URL=sqlite:///dados/locadora.db
```

Para habilitar recuperação de senha por e-mail:

```env
LOCADORA_BREVO_API_KEY=sua_chave_da_brevo
LOCADORA_EMAIL_REMETENTE=seu_remetente_verificado
LOCADORA_PUBLIC_URL=http://127.0.0.1:8000
```

Em produção, `LOCADORA_PUBLIC_URL` deve apontar para a URL pública da aplicação:

```env
LOCADORA_PUBLIC_URL=https://locadora-fastapi.onrender.com
```

Nunca envie o arquivo `.env` real ao GitHub. Ele está listado no `.gitignore`.

A aplicação valida na inicialização os segredos obrigatórios, como a senha do administrador e o segredo JWT.

## PostgreSQL

O mesmo código da aplicação funciona com SQLite e PostgreSQL.

Para PostgreSQL local em desenvolvimento:

```env
LOCADORA_DATABASE_URL=postgresql+psycopg://locadora_app:SUA_SENHA@localhost:5432/locadora_dev
LOCADORA_TEST_DATABASE_URL=postgresql+psycopg://locadora_app:SUA_SENHA@localhost:5432/locadora_test
```

Use as senhas reais somente no `.env`. Se a senha contiver caracteres especiais reservados em URL, eles precisam ser codificados.

O projeto separa os bancos por finalidade:

- `locadora_dev`: dados usados ao executar a aplicação;
- `locadora_test`: banco descartável usado somente nos testes de integração PostgreSQL.

Depois de configurar a URL de desenvolvimento, aplique o schema:

```bat
python -m alembic upgrade head
python -m alembic current
```

Inicie a API:

```bat
python -m uvicorn api.main:app --reload
```

O Alembic usa `render_as_batch` somente no SQLite. No PostgreSQL são emitidas operações nativas do banco.

URLs do tipo `postgresql://...` ou `postgres://...` são normalizadas pelo projeto para o driver `psycopg` 3 quando necessário.

## Docker Compose

O ambiente Docker executa três serviços coordenados:

1. `db` inicia o PostgreSQL 18 e aguarda o banco ficar saudável;
2. `migrate` executa `alembic upgrade head` e termina;
3. `api` inicia a FastAPI somente depois das migrations concluírem.

O PostgreSQL instalado diretamente no Windows pode continuar usando a porta `5432`. O PostgreSQL do Docker é publicado em `127.0.0.1:5433`, evitando conflito entre os dois ambientes.

Crie o arquivo privado de configuração:

```bat
copy .env.docker.example .env.docker
notepad .env.docker
```

Valide a configuração:

```bat
docker compose --env-file .env.docker config --quiet
```

Construa a imagem e inicie o ambiente:

```bat
docker compose --env-file .env.docker up --build
```

Consulte estado e logs:

```bat
docker compose --env-file .env.docker ps
docker compose --env-file .env.docker logs api
```

Endereços locais:

- frontend: `http://127.0.0.1:8000/app/`;
- Swagger: `http://127.0.0.1:8000/docs`;
- status versionado: `http://127.0.0.1:8000/api/v1/status`;
- health check: `http://127.0.0.1:8000/health`.

Para encerrar preservando os dados:

```bat
docker compose --env-file .env.docker down
```

Para apagar também o volume e reiniciar o banco do zero:

```bat
docker compose --env-file .env.docker down --volumes
```

A API é executada no container por um usuário Linux sem privilégios administrativos e não utiliza `--reload` em produção. A imagem usa build multi-stage, healthcheck próprio e copia apenas artefatos necessários ao runtime. No Compose, `api` e `migrate` usam filesystem somente leitura, `cap_drop: ALL`, `no-new-privileges`, `/tmp` temporário e limites de PIDs. Detalhes e limitações estão em [`docs/docker-hardening.md`](docs/docker-hardening.md).

## Integração contínua

O workflow `.github/workflows/ci.yml` executa automaticamente em Pull Requests destinados à `main` e após mudanças integradas nessa branch. Também pode ser iniciado manualmente pela aba **Actions** do GitHub.

O pipeline valida, entre outros pontos:

1. dependências com `pip check`;
2. qualidade do código com Ruff;
3. vulnerabilidades conhecidas com `pip-audit`;
4. migrations Alembic;
5. integração com PostgreSQL temporário;
6. suíte principal de testes com pytest;
7. cobertura de código com mínimo obrigatório de 85%;
8. testes E2E com Playwright em Chromium;
9. construção da imagem Docker;
10. configuração Docker Compose;
11. hardening da imagem: usuário efetivo, healthcheck e ausência de dependências de teste.

Os testes convencionais e os testes E2E são executados em jobs separados. O job principal ignora `tests/e2e`, enquanto o job E2E instala o Chromium e executa os testes de navegador de forma independente.

## Qualidade e segurança das dependências

Verificar o código com Ruff:

```bash
python -m ruff check .
```

Auditar as dependências:

```bash
python -m pip_audit -r requirements.txt --progress-spinner off
```

O arquivo `.github/dependabot.yml` verifica atualizações de dependências Python, GitHub Actions e imagens Docker. Pull Requests criados pelo Dependabot precisam passar pelos mesmos checks da `main`.

## Migrations com Alembic

A migration inicial funciona em dois cenários:

- cria todas as tabelas quando o banco está vazio;
- reconhece o schema SQLite legado, recria tabelas no formato atual e preserva os registros existentes.

Revisão atual validada:

```text
20260903_0001 (head)
```

Consultar a revisão atual:

```bash
python -m alembic current
```

Aplicar migrations pendentes:

```bash
python -m alembic upgrade head
```

Desfazer a migration mais recente:

```bash
python -m alembic downgrade -1
```

Gerar uma nova migration:

```bash
python -m alembic revision --autogenerate -m "descricao da alteracao"
```

Verificar se Models e banco estão sincronizados:

```bash
python -m alembic check
```

O `migrations/env.py` conecta o Alembic ao `Base.metadata`, lê `LOCADORA_DATABASE_URL`, normaliza URLs PostgreSQL para Psycopg 3 e ativa `render_as_batch` quando necessário para SQLite.

Toda migration gerada automaticamente deve ser revisada antes da execução.

## Execução

### CLI

```bash
python carros.py
```

### API

```bash
python -m uvicorn api.main:app --reload
```

Endereços locais padrão:

- API: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:8000/app/`
- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`
- Health: `http://127.0.0.1:8000/health`

## Frontend

O frontend é servido pela própria FastAPI. Não abra os arquivos HTML diretamente pelo explorador; inicie o Uvicorn e acesse `/app/` pelo navegador.

Os módulos implementados possuem:

- tela de login responsiva;
- integração com `POST /api/v1/auth/login`;
- access token JWT mantido somente em memória durante a vida da página, sem `sessionStorage` ou `localStorage`;
- refresh token rotativo mantido em cookie `HttpOnly` e nunca exposto ao JavaScript;
- restauração da sessão após navegação/reload por meio do refresh cookie, além da renovação automática após `401`;
- serialização de refresh entre abas compatíveis com Web Locks para reduzir corridas durante a rotação do cookie;
- validação da sessão com `GET /api/v1/auth/me`;
- redirecionamento de usuários sem autenticação;
- logout com revogação da sessão no backend;
- painel com quantidades carregadas de `GET /api/v1/status`;
- tela de veículos com busca por modelo, tipo, ano ou ID;
- filtros por disponibilidade, aluguel, manutenção e desativação;
- resumo da situação atual da frota;
- cadastro e edição de veículos para administradores;
- desativação e reativação de veículos para administradores;
- controles administrativos ocultos para clientes;
- histórico de aluguéis adaptado ao perfil autenticado;
- busca, filtro de status e acompanhamento de prazos;
- criação de aluguel com estimativa inicial das diárias;
- devolução com quilometragem, pagamento e parcelamento;
- visão administrativa de contratos e clientes;
- cadastro público de novas contas de cliente;
- busca e filtros de clientes para administradores;
- desativação e reativação de contas de cliente;
- painel administrativo de manutenções com busca, filtros e indicadores;
- abertura e finalização de manutenções integradas ao estado da frota;
- histórico de serviços, quilometragem e custos por veículo;
- painel administrativo com resumos operacionais e financeiros;
- rankings de veículos e clientes;
- comparação de faturamento e custos de manutenção;
- consulta do resultado bruto individual de cada veículo;
- solicitação pública de recuperação de senha por nome de usuário;
- redefinição de senha por link temporário enviado por e-mail;
- integração com Brevo via HTTPS para e-mail transacional;
- respostas de recuperação que não revelam se uma conta existe;
- alteração do nome de usuário pelo próprio cliente;
- confirmação da senha atual antes da alteração do nome de usuário;
- atualização imediata do nome exibido no painel;
- manutenção da sessão após a alteração do nome de usuário;
- tratamento de credenciais inválidas e falhas de conexão.

Como frontend e API usam a mesma origem, não é necessário liberar CORS para o fluxo atual. As telas reutilizam as funções centralizadas em `frontend/js/api.js`.

## Versionamento da API

A interface canônica da API utiliza o prefixo `/api/v1`. O frontend já consome as rotas versionadas, enquanto as rotas antigas sem o prefixo continuam temporariamente disponíveis para preservar compatibilidade durante a migração.

Exemplos canônicos:

```text
POST /api/v1/auth/login
GET /api/v1/clientes
GET /api/v1/veiculos
GET /api/v1/alugueis
GET /api/v1/status
```

O Swagger e o OpenAPI exibem apenas as rotas versionadas. Rotas operacionais, como `/health`, e arquivos estáticos em `/app`, não recebem versionamento.

## Autenticação

O login é realizado por:

```text
POST /api/v1/auth/login
```

Em caso de sucesso, a API retorna um **access token JWT** de curta duração e grava o **refresh token** em um cookie `HttpOnly`, `SameSite=Lax`. Em produção HTTPS, o cookie também recebe `Secure`. O frontend mantém o access token somente em memória enquanto a página está carregada; ele não é persistido em `sessionStorage` nem `localStorage`. O refresh token puro não é salvo no banco nem fica disponível ao JavaScript; somente seu hash SHA-256 é persistido na tabela `sessoes`.

```json
{
  "access_token": "token_jwt",
  "token_type": "bearer"
}
```

Nas rotas protegidas:

```http
Authorization: Bearer SEU_TOKEN
```

Consultar o usuário autenticado:

```text
GET /api/v1/auth/me
```

Alterar o nome de usuário de uma conta de cliente:

```text
PATCH /api/v1/auth/me/usuario
```

A alteração exige a senha atual, rejeita nomes já utilizados e atualiza os registros relacionados de forma transacional.

### Refresh token e gerenciamento de sessões

Quando o access token expira, o frontend pode renovar a autenticação por:

```text
POST /api/v1/auth/refresh
```

A renovação usa o cookie `HttpOnly`, rotaciona o refresh token a cada uso e emite um novo access token. O refresh token anterior deixa de ser aceito depois da rotação. Como o access token não é persistido no navegador, um reload ou uma nova navegação do frontend restaura a autenticação chamando esse endpoint e mantém o novo access token apenas em memória. Em navegadores com Web Locks, as renovações também são serializadas entre abas para reduzir corridas durante a rotação do refresh token.

Rotas de sessão disponíveis:

```text
POST   /api/v1/auth/logout
GET    /api/v1/auth/sessoes
DELETE /api/v1/auth/sessoes/{id_sessao}
DELETE /api/v1/auth/sessoes
```

Novos access tokens carregam o identificador `sid` da sessão. Assim, logout ou revogação tornam esses access tokens inválidos imediatamente, sem esperar os 30 minutos de expiração do JWT. Tokens emitidos antes desta etapa, que ainda não possuem `sid`, permanecem compatíveis somente até sua expiração natural.

## Recuperação de senha

O fluxo de recuperação funciona da seguinte forma:

```text
Usuário solicita recuperação
        ↓
FastAPI gera token temporário
        ↓
Token é armazenado de forma segura
        ↓
Brevo API envia e-mail por HTTPS
        ↓
Usuário abre o link de redefinição
        ↓
Sessões ativas são revogadas
        ↓
Nova senha é validada e salva
```

Variáveis usadas:

```env
LOCADORA_BREVO_API_KEY=segredo
LOCADORA_EMAIL_REMETENTE=remetente_verificado
LOCADORA_PUBLIC_URL=https://locadora-fastapi.onrender.com
```

A chave da Brevo nunca deve ser versionada. O remetente precisa estar verificado na plataforma da Brevo.

O uso da API HTTPS resolve a limitação do Render Free, que bloqueia conexões SMTP tradicionais nas portas comuns.

## Testes

A suíte automatizada está dividida entre testes convencionais e testes E2E de navegador.

### Testes convencionais

Execute:

```bash
python -m pytest --ignore=tests/e2e
```

Para executar a mesma validação de coverage usada no CI:

```bash
python -m pytest --ignore=tests/e2e --cov=api --cov=modulos --cov-report=term-missing --cov-fail-under=85
```

Estado base validado antes da Etapa 5:

```text
449 passed
Coverage total: 89,86%
Coverage mínima obrigatória: 85%
```

Validação local da Etapa 5 neste patch:

```text
451 passed
4 skipped (integração PostgreSQL sem banco de teste configurado)
Coverage total: 90,13%
Coverage mínima obrigatória: 85%
```

Validação local da Etapa 7 neste patch:

```text
464 passed
4 skipped (integração PostgreSQL sem banco de teste configurado)
Coverage total: 90,52%
Coverage mínima obrigatória: 85%
```

A suíte convencional passa a ter **468 testes**. No ambiente local sem PostgreSQL de teste, quatro testes de integração são ignorados; no CI e no ambiente de desenvolvimento configurado, eles são executados normalmente quando `LOCADORA_TEST_DATABASE_URL` está disponível.

Os testes convencionais cobrem:

- entidades de domínio;
- Services;
- Repositories SQLAlchemy;
- transações e rollback;
- Container;
- autenticação JWT;
- recuperação de senha;
- rate limiting;
- observabilidade HTTP e request ID;
- monitoramento de erros e sanitização de eventos do Sentry;
- audit logs persistentes, correlação por request ID e controle de acesso administrativo;
- Brevo API com mocks;
- alteração de nome de usuário;
- persistência da alteração em `usuarios` e `clientes`;
- continuidade do JWT após a renomeação;
- bloqueio de nome de usuário duplicado;
- frontend;
- endpoints FastAPI;
- migrations;
- integração PostgreSQL.

### Testes E2E

Os testes de navegador utilizam Playwright com Chromium:

```bash
python -m pytest tests/e2e --browser chromium -v
```

Estado atualmente validado:

```text
2 passed
```

Os testes E2E atuais validam:

- abertura real do frontend em Chromium;
- preenchimento e envio do formulário de login;
- execução do JavaScript da aplicação;
- ausência de JWT persistido em `sessionStorage` ou `localStorage`;
- restauração do access token por refresh após a navegação;
- redirecionamento para o dashboard;
- carregamento dos dados do usuário e das métricas;
- tratamento de credenciais inválidas;
- permanência na tela de login após falha;
- ausência de token após login inválido.

Nesta etapa, as respostas da API são interceptadas pelo Playwright. Assim, os testes validam o frontend em um navegador real sem depender do banco de produção. Testes E2E full-stack, usando API e banco de testes reais, podem ser adicionados em uma evolução futura.

No CI, os testes convencionais e os testes E2E são executados em jobs separados. A suíte cresce junto com cada etapa e o merge só ocorre depois que os dois grupos ficam verdes.

Os testes PostgreSQL dependem de `LOCADORA_TEST_DATABASE_URL`. O banco configurado nessa variável deve ser exclusivamente descartável para testes.

Exemplo:

```bat
python -m pytest tests	est_postgresql_integracao.py -q
```

Esses testes podem apagar e recriar o schema de teste. Nunca aponte `LOCADORA_TEST_DATABASE_URL` para o banco de produção ou para um banco com dados importantes.

## Segurança

- senhas novas usam PBKDF2-HMAC-SHA256 com salt aleatório;
- hashes SHA-256 antigos são aceitos apenas para compatibilidade;
- tokens de recuperação são aleatórios e apenas seu hash é persistido;
- refresh tokens são aleatórios, rotativos e persistidos somente por hash SHA-256;
- refresh tokens ficam em cookie `HttpOnly`, `SameSite=Lax` e `Secure` em produção HTTPS;
- o frontend não persiste access tokens em Web Storage; eles permanecem somente em memória;
- reloads restauram o access token usando o refresh token HttpOnly;
- access tokens novos ficam vinculados a uma sessão persistente por `sid`;
- logout e revogação de sessão invalidam imediatamente access tokens vinculados;
- redefinição de senha revoga todas as sessões ativas da conta;
- tokens de recuperação expiram, são de uso único e invalidam solicitações anteriores;
- respostas de login e recuperação evitam revelar se uma conta existe;
- o RBAC centraliza permissões por papel e cada operação protegida exige uma permissão explícita;
- alteração de nome de usuário exige autenticação e senha atual;
- nomes de usuário duplicados são rejeitados;
- operações compostas usam transações e rollback;
- segredos e credenciais ficam em variáveis de ambiente;
- `.env` e `.env.docker` não são versionados;
- container de produção executa com usuário sem privilégios administrativos;
- login protegido por rate limiting baseado em IP e usuário;
- recuperação e redefinição de senha possuem limites próprios de tentativas;
- excesso de tentativas retorna HTTP `429 Too Many Requests`;
- identificação do cliente considera o endereço encaminhado pelo proxy de produção;
- logs HTTP não registram query string, cabeçalhos nem corpo da requisição;
- eventos de autenticação usam apenas campos previamente permitidos e não incluem senha ou token;
- cada resposta HTTP recebe um `X-Request-ID` gerado pela aplicação;
- eventos enviados ao Sentry removem body, query string, cookies, headers e dados de usuário;
- o Sentry é ativado somente quando `LOCADORA_SENTRY_DSN` está configurada;
- respostas do frontend recebem headers de hardening como `CSP`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` e `Permissions-Policy`;
- respostas de autenticação usam `Cache-Control: no-store`;
- `HSTS` é enviado somente quando o ambiente está marcado como produção e a URL pública usa HTTPS;
- a tela de redefinição remove o token de recuperação da barra de endereço após carregá-lo;
- a decodificação JWT exige os claims básicos `sub`, `iat` e `exp`;
- audit logs não persistem senha, token, JWT, segredo, DSN ou valores dos campos alterados;
- a consulta de auditoria é restrita a administradores e não existem endpoints de edição ou exclusão desses registros;
- falhas isoladas ao persistir auditoria são registradas como `audit.write_failed` e encaminhadas ao Sentry sem transformar uma operação de negócio já concluída em falso erro HTTP;
- dependências são auditadas com `pip-audit`;
- Dependabot acompanha atualizações de dependências e ferramentas.

## Trilha do projeto

- POO e domínio: **concluído**;
- arquitetura em camadas: **concluída**;
- Repository Pattern e injeção de dependência: **concluídos**;
- FastAPI, Pydantic, JWT e OpenAPI: **concluídos**;
- migração completa para SQLAlchemy: **concluída**;
- testes automatizados: **concluídos e em evolução**;
- Alembic e migrations: **concluídos**;
- frontend com HTML, CSS e JavaScript: **concluído**;
- login, access token JWT em memória, refresh token rotativo e gerenciamento de sessões: **concluídos**;
- RBAC granular por permissões: **concluído**;
- gerenciamento da frota no frontend: **concluído**;
- criação, devolução e acompanhamento de aluguéis: **concluídos**;
- cadastro e gerenciamento de clientes: **concluídos**;
- manutenções: **concluídas**;
- relatórios operacionais e financeiros: **concluídos**;
- recuperação e redefinição de senha: **concluídas e validadas em produção**;
- envio de e-mail via Brevo API: **concluído e validado em produção**;
- alteração de nome de usuário: **concluída e validada em produção**;
- Git e GitHub: **concluídos e em uso contínuo**;
- PostgreSQL e Psycopg 3: **concluídos**;
- integração PostgreSQL: **concluída**;
- Docker e Docker Compose: **concluídos**;
- GitHub Actions: **concluído**;
- proteção da branch principal: **concluída**;
- Ruff, pip-audit e Dependabot: **concluídos**;
- deploy Render + Neon: **concluído**;
- publicação online: **concluída**;
- coverage obrigatório no CI: **concluído**;
- documentação da arquitetura: **concluída**;
- rate limiting: **concluído**;
- testes E2E com Playwright: **concluídos e integrados ao CI**;
- logs estruturados e request ID: **concluídos**;
- monitoramento de erros: **concluído e validado em produção com Sentry**;
- audit logs: **concluídos e disponíveis na interface administrativa**.

## RBAC granular

A Etapa 10 substitui a autorização espalhada por comparações diretas de `role` por um mapa central de permissões em `modulos/permissoes.py`. Os papéis atuais continuam sendo `admin` e `cliente`, mas as rotas protegidas passam a declarar capacidades específicas, como `clientes:ler`, `veiculos:editar`, `manutencoes:finalizar`, `relatorios:ler` e `auditoria:ler`.

A dependência `exigir_permissao()` aplica o controle no backend depois da autenticação. O endpoint `GET /api/v1/auth/me` também retorna as permissões efetivas do usuário, permitindo que o frontend oculte ações que aquele papel não pode executar. O backend permanece como fonte de verdade: esconder um botão não substitui a validação da API.

Nesta etapa não há migration nova. As permissões são derivadas dos dois papéis já existentes e nenhuma credencial ou segredo é armazenado nessa matriz.

## Deploy — Render + Neon

A produção usa um único Web Service no Render. O frontend é servido pela própria FastAPI e o PostgreSQL persistente fica no Neon.

O arquivo `render.yaml` configura o serviço com:

- runtime Docker;
- plano gratuito;
- região `virginia`;
- health check em `/health`;
- deploy automático após checks aprovados;
- variáveis de ambiente de produção;
- segredo JWT gerado pelo Render;
- secrets sensíveis cadastrados fora do Git.

O `Dockerfile` inicia `python -m modulos.container_entrypoint`. Esse entrypoint executa Alembic diretamente por `subprocess` quando `LOCADORA_EXECUTAR_MIGRATIONS` está habilitado e depois substitui o processo pelo Uvicorn, sem usar `sh -c`. A porta vem de `PORT`, fornecida pelo Render.

### Neon

O projeto Neon foi configurado na região compatível com o serviço do Render para reduzir latência.

A produção utiliza uma **connection string direta** do Neon em `LOCADORA_DATABASE_URL`, adequada ao uso atual com SQLAlchemy, Psycopg 3 e Alembic.

Exemplo conceitual:

```text
LOCADORA_DATABASE_URL=postgresql://USUARIO:SENHA@HOST/neondb?sslmode=require
```

A URL real nunca deve ser colocada no README, em commits ou mensagens públicas.

### Variáveis do Render

Principais variáveis de produção:

```text
LOCADORA_ADMIN_USUARIO=admin
LOCADORA_ADMIN_SENHA=<segredo>
LOCADORA_JWT_SECRET=<gerado pelo Render>
LOCADORA_DATABASE_URL=<segredo do Neon>
LOCADORA_BREVO_API_KEY=<segredo da Brevo>
LOCADORA_EMAIL_REMETENTE=<remetente verificado>
LOCADORA_PUBLIC_URL=https://locadora-fastapi.onrender.com
```

### E-mail no Render Free

O Render Free bloqueia SMTP tradicional em portas comuns. Por isso, a aplicação não depende mais de Gmail SMTP ou `smtplib` em produção.

A recuperação de senha usa a **Brevo Transactional Email API via HTTPS**, permitindo que o fluxo funcione normalmente no Render Free.

Esse fluxo já foi validado em produção:

```text
solicitação de recuperação
        ↓
e-mail recebido
        ↓
link de redefinição aberto
        ↓
senha alterada
        ↓
login com a nova senha realizado com sucesso
```

## Produção validada

A versão online foi testada manualmente após o deploy com sucesso para:

- health check;
- login de administrador;
- login de cliente;
- escrita e persistência no PostgreSQL Neon;
- recuperação de senha por e-mail;
- redefinição de senha;
- login após redefinição;
- alteração do nome de usuário de cliente;
- bloqueio do login com o nome antigo;
- login com o novo nome de usuário;
- persistência da alteração no banco.

**Status atual: versão funcional concluída, publicada e validada em produção, com evolução contínua de segurança, testes, observabilidade e arquitetura.**

## Frontend — Etapa 14

A fase de refinamento visual e de experiência foi concluída com uma camada compartilhada de UX. Além do Design System, dashboard e telas operacionais, o frontend agora inclui melhorias de navegação por teclado, retorno de foco em diálogos, estados `aria-busy`, feedback de conectividade, alvos de toque e suporte ampliado a preferências de contraste e movimento.

Essas melhorias permanecem independentes das regras de negócio e do RBAC: autorização e validação continuam sendo responsabilidade do backend.

## Trilha principal — Paginação e consultas server-side

As telas operacionais deixam de depender do carregamento integral das coleções para busca e filtros. A API passa a oferecer consultas paginadas em endpoints dedicados, preservando as rotas legadas de listagem para compatibilidade com consumidores existentes.

Endpoints adicionados:

```text
GET /api/v1/clientes/consulta
GET /api/v1/veiculos/consulta
GET /api/v1/alugueis/consulta
GET /api/v1/alugueis/me/consulta
GET /api/v1/manutencoes/consulta
```

As consultas aceitam `pagina`, `por_pagina`, `busca`, `status`, `ordenar` e `direcao`, respeitando os campos válidos de cada recurso. O PostgreSQL/SQLite executa `WHERE`, `ORDER BY`, `LIMIT` e `OFFSET`; o frontend recebe somente a página atual, os totais e o resumo operacional.

As rotas antigas como `GET /api/v1/veiculos` continuam disponíveis nesta etapa porque ainda são usadas por fluxos que precisam da coleção completa, como seleção de veículo em aluguel ou manutenção. A migração é, portanto, incremental e sem quebra imediata de compatibilidade.

## Trilha principal — Dashboard com métricas melhores

A Etapa 12 evolui o dashboard sem repetir o redesign visual concluído na subtrilha de frontend. O foco passa a ser a qualidade dos dados exibidos: as métricas administrativas são agregadas diretamente no banco com SQLAlchemy e expostas por um endpoint dedicado protegido por `relatorios:ler`.

Endpoint adicionado:

```text
GET /api/v1/relatorios/dashboard
```

O resumo administrativo inclui clientes ativos/inativos, distribuição da frota por status, aluguéis e manutenções ativos/finalizados, taxa da frota atualmente alugada, receita de aluguéis finalizados, custos de manutenção finalizada, resultado bruto e ticket médio dos aluguéis concluídos.

Usuários sem a permissão de relatórios continuam usando o resumo básico já existente. O frontend decide qual fonte consultar a partir das permissões retornadas por `/api/v1/auth/me`; a autorização do endpoint administrativo continua sendo aplicada no backend.

Não há migration nesta etapa.

## Trilha principal — Exportações CSV, Excel e PDF

A Etapa 13 adiciona download do relatório completo de resultado por veículo em três formatos interoperáveis:

```text
GET /api/v1/relatorios/resultado-por-veiculo/exportar/csv
GET /api/v1/relatorios/resultado-por-veiculo/exportar/xlsx
GET /api/v1/relatorios/resultado-por-veiculo/exportar/pdf
```

As exportações reutilizam os dados já produzidos por `RelatorioService.resultado_por_veiculo()`. A nova camada `ExportacaoRelatoriosService` não recalcula regras financeiras: ela recebe o resultado do relatório e apenas o transforma em arquivo. O endpoint continua protegido por `relatorios:ler`.

Características dos formatos:

- **CSV**: UTF-8 com BOM e separador `;`, facilitando abertura no Excel em ambientes pt-BR;
- **Excel (.xlsx)**: planilha com cabeçalho, filtro, congelamento de painel, larguras de coluna e formatação monetária;
- **PDF**: documento A4 paisagem com título, instante de geração e tabela paginável;
- todos usam `Content-Disposition: attachment` e `Cache-Control: no-store`;
- textos iniciados por caracteres de fórmula são neutralizados nas exportações destinadas a planilhas para reduzir risco de CSV/Excel Formula Injection.

O frontend de relatórios oferece botões CSV, Excel e PDF na seção “Resultado por veículo”. O access token continua somente em memória: o download é feito pela camada autenticada de `frontend/js/api.js`, que também consegue renovar a sessão antes de repetir a solicitação.

Novas dependências de runtime:
- `openpyxl` para geração de `.xlsx`;
- `reportlab` para geração de PDF.

Não há migration nesta etapa.

## Trilha principal — Manutenção avançada

A Etapa 14 amplia o módulo de manutenção sem antecipar inspeções, danos, multas,
caução ou combustível. A manutenção passa a registrar contexto operacional além
do motivo e do custo final:

- tipo `preventiva` ou `corretiva`;
- prioridade `baixa`, `media` ou `alta`;
- oficina/fornecedor responsável;
- custo estimado;
- previsão de conclusão;
- observações de acompanhamento;
- indicação derivada de manutenção atrasada.

Manutenções ativas podem ser editadas por usuários com
`manutencoes:editar`. A abertura continua alterando o veículo para o estado
`manutencao`, e a finalização continua registrando o custo real e liberando o
veículo na mesma transação.

Endpoint adicional:

```text
PATCH /api/v1/manutencoes/{id_manutencao}
```

A consulta paginada também aceita filtros por `tipo` e `prioridade`, além de
ordenação por previsão e custo estimado. O resumo operacional inclui quantidade
atrasada e custo estimado ainda em aberto.

A evolução exige a migration `20260928_0004_manutencao_avancada`, preservando
os registros existentes com os padrões `corretiva`, `media` e custo estimado
zero.

## Trilha principal — Reservas futuras de veículos

A Etapa 15 adiciona reservas para períodos futuros sem alterar o estado atual do
veículo. Um veículo pode estar disponível hoje e, ao mesmo tempo, possuir um
período futuro comprometido por uma reserva.

Fluxos principais:

```text
POST /api/v1/reservas
GET  /api/v1/reservas
GET  /api/v1/reservas/consulta
GET  /api/v1/reservas/me
GET  /api/v1/reservas/me/consulta
PATCH /api/v1/reservas/me/{id_reserva}/cancelar
PATCH /api/v1/reservas/{id_reserva}/cancelar
```

A criação exige início posterior à data atual e fim posterior ao início. O
período é tratado como intervalo semiaberto `[inicio, fim)`, permitindo que uma
reserva termine no mesmo dia em que outra começa, mas rejeitando qualquer
sobreposição real para o mesmo veículo.

Antes de registrar a reserva, `ReservaService` verifica conflitos com outras
reservas ativas, aluguéis ativos e manutenção em andamento. Uma manutenção sem
previsão de conclusão impede a reserva; quando existe previsão, o conflito é
avaliado pelo período conhecido.

Reservas possuem estados persistidos `ativa`, `cancelada` e `convertida`. O
estado `expirada` é derivado da data final e não precisa ser armazenado. No dia
de início, o fluxo de aluguel reconhece uma reserva do mesmo cliente e pode
convertê-la em aluguel quando o período solicitado está contido no período
reservado. Reservas de outros clientes impedem o aluguel conflitante.

O frontend oferece uma tela própria com consulta server-side, busca, filtros,
ordenação, paginação, criação pelo cliente e cancelamento conforme RBAC.
Administradores podem consultar toda a agenda e cancelar reservas; clientes
consultam e administram apenas o próprio fluxo.

A etapa usa a migration `20260928_0005_reservas`, com índices por veículo/período
e cliente/status. A checagem de conflitos é feita na camada de aplicação nesta
etapa; proteção contra corrida entre transações concorrentes será tratada na
etapa específica de concorrência e consistência transacional.


## Trilha principal — Vistorias, danos, multas, caução e combustível

A Etapa 16 separa o registro operacional da vistoria do processamento financeiro.
Isso permite registrar o estado real do veículo e as ocorrências relacionadas ao
aluguel antes da Etapa 17, que passa a ser responsável pelos pagamentos
adicionais e pela liquidação financeira.

O módulo usa a seguinte composição:

```text
frontend/vistorias.html
        ↓
api/routers/vistorias.py
        ↓
VistoriaService
        ↓
VistoriaRepository
        ↓
InspecaoAluguelModel / DanoAluguelModel
MultaTransitoModel / CaucaoAluguelModel
        ↓
PostgreSQL / SQLite
```

As inspeções possuem dois momentos: `retirada` e `devolucao`. Cada aluguel aceita
no máximo uma inspeção de cada tipo. A inspeção registra quilometragem do
odômetro, nível de combustível entre 0% e 100% e observações. Quando as duas
inspeções existem, o sistema calcula a diferença de combustível devolvida abaixo
do nível inicial sem transformar essa diferença automaticamente em cobrança.

Danos e multas de trânsito ficam ligados ao aluguel e podem ser cancelados sem
apagar o histórico. Os valores ativos compõem um resumo de pendências estimadas.
A multa de trânsito é independente da multa por atraso já existente em
`Aluguel`.

A caução é um registro único por aluguel. O sistema armazena o valor total e o
valor já liberado e deriva o estado como `retida`, `parcial` ou `liberada`.
Nenhum desses valores é liquidado automaticamente nesta etapa.

Principais rotas:

```text
GET   /api/v1/vistorias/alugueis/{id_aluguel}
POST  /api/v1/vistorias/alugueis/{id_aluguel}/inspecoes
POST  /api/v1/vistorias/alugueis/{id_aluguel}/danos
PATCH /api/v1/vistorias/danos/{id_dano}/cancelar
POST  /api/v1/vistorias/alugueis/{id_aluguel}/multas
PATCH /api/v1/vistorias/multas/{id_multa}/cancelar
PUT   /api/v1/vistorias/alugueis/{id_aluguel}/caucao
```

A autorização administrativa usa `vistorias:ler`, `vistorias:registrar`,
`danos:gerenciar`, `multas:gerenciar` e `caucoes:gerenciar`. Escritas sensíveis
também entram na trilha de auditoria.

A migration `20260928_0006_vistorias_ocorrencias` cria as tabelas `inspecoes`,
`danos`, `multas_transito` e `caucoes`, com foreign keys para `alugueis`,
constraints de domínio e índices para as consultas operacionais. A migration
também tolera o cenário em que `Base.metadata.create_all()` já criou as tabelas.

A Etapa 16 deliberadamente não soma danos, multas de trânsito, combustível ou
caução ao pagamento existente da devolução. Esses registros são a fonte
operacional consumida pela Etapa 17 para montar a liquidação financeira sem
duplicar regras de vistoria.


## Trilha principal — Pagamentos e financeiro

A Etapa 17 introduz uma camada financeira própria sem apagar o histórico do
fluxo de devolução existente. Aluguéis finalizados antes dessa etapa já possuem
o valor e a forma de pagamento registrados no próprio aluguel; esse valor entra
como **liquidação legada** para que a aplicação não cobre o contrato duas vezes.

O módulo segue a composição:

```text
frontend/pagamentos.html
        ↓
api/routers/pagamentos.py
        ↓
PagamentoService
        ↓
PagamentoRepository + VistoriaService
        ↓
PagamentoFinanceiroModel
DanoAluguelModel / MultaTransitoModel / CaucaoAluguelModel
        ↓
PostgreSQL / SQLite
```

O resumo financeiro de cada aluguel finalizado considera:

```text
total_devido =
    valor registrado na devolução
    + danos ativos
    + multas de trânsito ativas

total_pago =
    liquidação legada da devolução
    + pagamentos financeiros confirmados

saldo_pendente =
    max(total_devido - total_pago, 0)
```

A multa por atraso continua sendo exibida de forma informativa porque já integra
o valor registrado pela devolução. A caução retida também aparece no resumo como
valor disponível, mas não reduz o saldo automaticamente: a Etapa 17 não altera a
semântica operacional da caução nem presume que todo valor retido foi convertido
em cobrança.

Pagamentos adicionais aceitam dinheiro, Pix, débito, crédito, boleto e
transferência. Parcelamento é permitido apenas no crédito, de uma a doze
parcelas. O sistema impede pagamentos acima do saldo pendente. Um pagamento
confirmado pode ser estornado sem ser apagado, preservando o histórico.

Os estados financeiros são derivados:

```text
pendente   -> existe saldo e nenhum pagamento adicional confirmado
parcial    -> existe saldo e já houve pagamento adicional confirmado
liquidado  -> saldo zerado
credito    -> alterações operacionais posteriores deixaram total pago acima do devido
```

Principais rotas:

```text
GET   /api/v1/pagamentos/consulta
GET   /api/v1/pagamentos/alugueis/{id_aluguel}
POST  /api/v1/pagamentos/alugueis/{id_aluguel}
PATCH /api/v1/pagamentos/{id_pagamento}/estornar
```

A autorização administrativa usa `financeiro:ler`, `financeiro:receber` e
`financeiro:estornar`. Registro e estorno de pagamentos entram na auditoria.

A migration `20260928_0007_pagamentos_financeiro` cria a tabela
`pagamentos_financeiros`, ligada a `alugueis`, com constraints para valor,
forma, parcelas e status. O histórico legado permanece no aluguel e não é
duplicado na nova tabela.

## Trilha principal — Notificações automáticas

A Etapa 18 adiciona uma central persistente de notificações sem antecipar a
infraestrutura de filas/background jobs prevista para a Etapa 19. Os lembretes
são sincronizados de forma idempotente quando o usuário acessa o painel ou a
central de notificações; a etapa seguinte poderá reutilizar o mesmo service em
execuções agendadas.

O módulo segue a composição:

```text
frontend/notificacoes.html
        ↓
api/routers/notificacoes.py
        ↓
NotificacaoService
        ↓
NotificacaoRepository
        ↓
NotificacaoModel
        ↓
PostgreSQL / SQLite
```

Clientes recebem lembretes de reserva próxima, devolução próxima/atrasada e
pendência financeira. Administradores recebem lembretes de manutenção prevista
ou atrasada. A chave de deduplicação persistida impede que atualizar a página
crie o mesmo aviso ou envie o mesmo e-mail repetidamente.

Quando Brevo está configurado, lembretes destinados a clientes também são
enviados por e-mail. Falhas no provedor não impedem a criação da notificação
interna: o resultado do canal de e-mail fica registrado como `enviado`,
`falhou`, `nao_configurado` ou `nao_aplicavel`.

Principais rotas:

```text
POST  /api/v1/notificacoes/sincronizar
GET   /api/v1/notificacoes/consulta
PATCH /api/v1/notificacoes/ler-todas
PATCH /api/v1/notificacoes/{id_notificacao}/ler
```

A permissão `notificacoes:ler` é atribuída a administradores e clientes. A
migration `20260928_0008_notificacoes` cria a tabela `notificacoes` e o índice
por usuário, estado de leitura e data de criação.

A Etapa 19 passou a chamar `NotificacaoService.processar_usuario()` fora do ciclo
de requisição por meio da fila persistente, sem duplicar regras de domínio.

## Trilha principal — Background jobs e fila persistente

A Etapa 19 adiciona uma fila persistente em banco para executar trabalho fora do
ciclo HTTP sem introduzir Redis antes da Etapa 20. O primeiro job automatizado
reaproveita `NotificacaoService.processar_usuario()` para gerar os lembretes
diários de todos os usuários ativos.

```text
Scheduler do worker
        ↓
BackgroundJobService
        ↓
tarefas_background
        ↓
worker reserva uma tarefa
        ↓
NotificacaoService
```

A chave de deduplicação da tarefa inclui data e usuário. Por isso vários ciclos
do worker podem tentar agendar o mesmo dia sem duplicar trabalho. A fila persiste
status, número de tentativas, horário de disponibilidade, bloqueio, erro e término.
Falhas são reagendadas com backoff exponencial e bloqueios abandonados por um
processo interrompido voltam para a fila após o timeout configurado.

Por padrão, desenvolvimento local mantém o worker embutido desativado. O Render
ativa `LOCADORA_BACKGROUND_JOBS_ENABLED=true` no mesmo Web Service, evitando criar
um serviço adicional nesta etapa. Como o Web Service atual usa o plano gratuito,
o worker é **best effort**: ele roda enquanto a instância está acordada e retoma a
fila persistida quando a aplicação desperta novamente. Para garantia rígida de
horário, use no futuro um worker/cron dedicado. Em um deploy com worker dedicado,
o mesmo processador também pode ser iniciado com:

```bash
python -m modulos.background_worker
```

Para executar somente um ciclo, útil em cron, diagnóstico ou CI:

```bash
python -m modulos.background_worker --once
```

Variáveis disponíveis:

```text
LOCADORA_BACKGROUND_JOBS_ENABLED
LOCADORA_BACKGROUND_JOBS_INTERVALO_SEGUNDOS
LOCADORA_BACKGROUND_JOBS_LOTE
LOCADORA_BACKGROUND_JOBS_TIMEOUT_BLOQUEIO_SEGUNDOS
```

A migration `20260930_0009_background_jobs` cria `tarefas_background` e o índice
`idx_tarefas_background_status_disponivel`. O PostgreSQL usa `FOR UPDATE SKIP
LOCKED` para reservar trabalho com segurança quando houver mais de um worker.

A sincronização manual de notificações continua disponível como fallback e não
cria duplicatas, porque a deduplicação final permanece em `NotificacaoService`.

## Trilha principal — Redis e cache compartilhado

A Etapa 20 adiciona Redis/Valkey como infraestrutura **opcional** para cache e
rate limiting distribuído. O PostgreSQL continua sendo a fonte de verdade e a
fila persistente da Etapa 19 permanece no banco relacional.

```text
FastAPI
  ├── autenticação
  │     ↓
  │  RateLimiter
  │     ↓
  │  Redis / Valkey
  │     └── fallback local em memória se indisponível
  │
  └── RelatorioService
        ↓
     CacheService
        ↓
     Redis / Valkey
        └── cache miss → consulta PostgreSQL
```

O dashboard administrativo usa o padrão cache-aside na chave
`relatorios:dashboard:v1`, com TTL curto configurável. A primeira leitura calcula
as métricas no banco e grava o JSON no cache; as próximas leituras reutilizam o
valor até o TTL. O botão **Atualizar dados** envia `?atualizar=true`, ignora o
cache, recalcula no PostgreSQL e substitui a entrada armazenada.

O rate limiter dos fluxos de login, recuperação e redefinição de senha passa a
usar contadores compartilhados quando `LOCADORA_REDIS_URL` está configurada.
Assim, duas instâncias da API enxergam o mesmo limite. Se Redis/Valkey ficar
indisponível, a aplicação degrada para o limiter em memória por processo em vez
de impedir autenticação.

Variáveis disponíveis:

```text
LOCADORA_REDIS_URL
LOCADORA_REDIS_PREFIXO
LOCADORA_REDIS_TIMEOUT_MS
LOCADORA_CACHE_DASHBOARD_TTL_SEGUNDOS
```

No Docker Compose local existe um serviço `cache` baseado em Redis 8. Em
produção, a aplicação aceita qualquer endpoint compatível com `redis://` ou
`rediss://`. A URL não deve ser versionada: configure-a no ambiente do serviço.
Sem `LOCADORA_REDIS_URL`, cache distribuído fica desativado e o sistema continua
funcional.

A fila de background jobs **não foi migrada para Redis** nesta etapa. Essa decisão
preserva a durabilidade já existente no PostgreSQL e evita transformar cache em
fonte de verdade de tarefas.

## Trilha principal — Backup e recuperação

A Etapa 21 adiciona um procedimento operacional de backup, verificação e restore
sem usar o filesystem efêmero do Render como armazenamento definitivo.

O comando principal é:

```bash
python -m modulos.backup_cli criar
```

Em PostgreSQL/Neon ele usa `pg_dump` em formato custom; em SQLite usa a API de
backup nativa. Para Neon, `LOCADORA_BACKUP_DATABASE_URL` pode guardar uma URL
direta separada da conexão pooled usada pela aplicação. Cada arquivo recebe
metadata sem credenciais, SHA-256 e a revisão
Alembic quando identificável. O restore exige uma URL de destino explícita e a
flag `--confirmar`, reduzindo o risco de sobrescrever produção por engano.

Comandos disponíveis:

```bash
python -m modulos.backup_cli criar
python -m modulos.backup_cli listar
python -m modulos.backup_cli verificar backups/ARQUIVO
python -m modulos.backup_cli restaurar backups/ARQUIVO --destino-url URL --confirmar
python -m modulos.backup_cli limpar --manter 7 --confirmar
```

Backups locais ficam em `backups/`, que é ignorado pelo Git e pelo Docker. Redis
não é copiado porque contém apenas cache/rate limit reconstruíveis. A fila da
Etapa 19 continua protegida porque está no PostgreSQL.

O runbook completo, incluindo recovery drill e cuidados específicos com
Neon/Render, está em `docs/backup-recuperacao.md`. Não há migration nova nesta
etapa; posteriormente a Etapa 25 avança o Alembic head para `20261006_0010_consistencia_concorrencia`.


## Ambientes dev / staging / prod

A configuração de ambiente é centralizada por `LOCADORA_AMBIENTE`, com os valores `development`, `test`, `staging` e `production`. Staging e produção recusam fallback SQLite, exigem PostgreSQL explícito e `LOCADORA_PUBLIC_URL` em HTTPS.

Modelos seguros estão em `.env.development.example`, `.env.staging.example` e `.env.production.example`. O fluxo e as regras de isolamento estão documentados em [`docs/ambientes.md`](docs/ambientes.md). O blueprint `render.staging.yaml` serve como referência para um serviço de homologação separado do serviço de produção.

## Trilha principal — testes de carga e otimização

A Etapa 24 adiciona uma baseline reproduzível de desempenho sem transformar
benchmark em teste unitário. O runner assíncrono em
`scripts/performance/load_test.py` mede taxa de sucesso, throughput e latências
média/p50/p95/p99, com cenários para health check, paginação de veículos e
dashboard com e sem reaproveitamento de cache.

Por segurança, o alvo padrão é local e destinos remotos exigem opt-in explícito.
Credenciais de carga são lidas de variáveis de ambiente e não entram nos
resultados. O procedimento completo está em `docs/testes-carga-otimizacao.md`.
A regra desta etapa é medir antes de otimizar e comparar a mesma carga antes e
depois de cada mudança.


## Trilha principal — concorrência e consistência transacional

A Etapa 25 protege as principais mutações contra race conditions sem elevar
globalmente o isolamento do banco. Reservas, aluguéis, manutenção, devoluções e
pagamentos revalidam o estado dentro da própria transação depois de adquirir
locks de linha com `SELECT ... FOR UPDATE` no PostgreSQL.

A linha de `veiculos` é usada como ponto comum de serialização para operações
que disputam o mesmo veículo. Pagamentos serializam pela linha do aluguel. Uma
segunda operação que chega com estado desatualizado recebe
`ConflitoConcorrencia`, exposto pela API como HTTP `409 Conflict`.

A migration `20261006_0010_consistencia_concorrencia` adiciona também o índice
parcial único `idx_aluguel_ativo_veiculo`, impedindo no próprio banco mais de um
aluguel ativo por veículo. O runbook e a estratégia de testes PostgreSQL estão
documentados em
[`docs/concorrencia-consistencia.md`](docs/concorrencia-consistencia.md).
