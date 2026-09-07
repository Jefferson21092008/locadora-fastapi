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

Além das funcionalidades de negócio, a versão atual também possui cobertura mínima obrigatória no CI, documentação da arquitetura, rate limiting em endpoints sensíveis de autenticação e testes E2E de frontend executados em Chromium com Playwright.

A documentação detalhada da arquitetura está disponível em [`docs/arquitetura.md`](docs/arquitetura.md).

## Funcionalidades

- cadastro, consulta, ativação e desativação de clientes;
- cadastro, busca, edição e controle de veículos;
- criação e finalização de aluguéis;
- cálculo de devolução, quilometragem, multa e pagamento;
- abertura e finalização de manutenções;
- relatórios administrativos e financeiros;
- autenticação JWT com perfis de administrador e cliente;
- recuperação de senha por e-mail via Brevo API;
- tokens temporários, de uso único e armazenados por hash;
- alteração do nome de usuário pelo próprio cliente, com confirmação da senha atual;
- prevenção de nomes de usuário duplicados;
- atualização transacional do nome de usuário nas tabelas relacionadas;
- CLI e API REST usando a mesma camada de negócio;
- frontend responsivo com login JWT e painel conectado à API;
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
│   ├── dependencias.py
│   ├── erros.py
│   ├── main.py
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
│   │   ├── auth.js
│   │   ├── cadastro.js
│   │   ├── clientes.js
│   │   ├── dashboard.js
│   │   ├── esqueci-senha.js
│   │   ├── manutencoes.js
│   │   ├── redefinir-senha.js
│   │   ├── relatorios.js
│   │   └── veiculos.js
│   ├── alugueis.html
│   ├── cadastro.html
│   ├── clientes.html
│   ├── dashboard.html
│   ├── esqueci-senha.html
│   ├── index.html
│   ├── manutencoes.html
│   ├── redefinir-senha.html
│   ├── relatorios.html
│   └── veiculos.html
├── docs/
│   └── arquitetura.md
├── migrations/
│   ├── versions/
│   │   └── 20260903_0001_schema_inicial.py
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── modulos/
│   ├── cli/
│   ├── models/
│   ├── repositories/
│   ├── servicos/
│   ├── alugueis.py
│   ├── clientes.py
│   ├── config.py
│   ├── container.py
│   ├── database.py
│   ├── excecoes.py
│   ├── interface.py
│   ├── locadora.py
│   ├── manutencoes.py
│   ├── pagamentos.py
│   ├── seguranca.py
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

Os arquivos de domínio em `modulos/` representam clientes, veículos, aluguéis, manutenções, usuários e pagamentos. Eles concentram regras próprias do domínio e não executam SQL.

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
- status: `http://127.0.0.1:8000/status`;
- health check: `http://127.0.0.1:8000/health`.

Para encerrar preservando os dados:

```bat
docker compose --env-file .env.docker down
```

Para apagar também o volume e reiniciar o banco do zero:

```bat
docker compose --env-file .env.docker down --volumes
```

A API é executada no container por um usuário Linux sem privilégios administrativos e não utiliza `--reload` em produção.

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
10. configuração Docker Compose.

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
- integração com `POST /auth/login`;
- armazenamento do JWT em `sessionStorage`;
- validação da sessão com `GET /auth/me`;
- redirecionamento de usuários sem autenticação;
- encerramento da sessão;
- painel com quantidades carregadas de `GET /status`;
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

## Autenticação

O login é realizado por:

```text
POST /auth/login
```

Em caso de sucesso, a API retorna um JWT:

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
GET /auth/me
```

Alterar o nome de usuário de uma conta de cliente:

```text
PATCH /auth/me/usuario
```

A alteração exige a senha atual, rejeita nomes já utilizados e atualiza os registros relacionados de forma transacional.

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

Estado atualmente validado:

```text
449 passed
Coverage total: 89,86%
Coverage mínima obrigatória: 85%
```

Os testes convencionais cobrem:

- entidades de domínio;
- Services;
- Repositories SQLAlchemy;
- transações e rollback;
- Container;
- autenticação JWT;
- recuperação de senha;
- rate limiting;
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
- armazenamento do JWT no `sessionStorage`;
- redirecionamento para o dashboard;
- carregamento dos dados do usuário e das métricas;
- tratamento de credenciais inválidas;
- permanência na tela de login após falha;
- ausência de token após login inválido.

Nesta etapa, as respostas da API são interceptadas pelo Playwright. Assim, os testes validam o frontend em um navegador real sem depender do banco de produção. Testes E2E full-stack, usando API e banco de testes reais, podem ser adicionados em uma evolução futura.

No CI, os testes convencionais e os testes E2E são executados em jobs separados. Considerando as duas suítes, a validação atual executa **451 testes automatizados**: 449 convencionais e 2 E2E.

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
- tokens de recuperação expiram, são de uso único e invalidam solicitações anteriores;
- respostas de login e recuperação evitam revelar se uma conta existe;
- permissões são verificadas por perfil;
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
- login, sessão JWT e painel: **concluídos**;
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
- logs estruturados: **próxima etapa**;
- monitoramento de erros: **planejado**;
- audit logs: **planejados**.

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

O `Dockerfile` inicia o container executando primeiro:

```text
python -m alembic upgrade head
```

e depois inicia o Uvicorn em `0.0.0.0` usando a porta fornecida pela variável `PORT` do Render.

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
