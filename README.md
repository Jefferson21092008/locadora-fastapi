# Locadora API

Sistema de gerenciamento de locadora de veículos desenvolvido em Python. O
mesmo domínio e as mesmas regras de negócio atendem uma interface de linha de
comando, uma API REST com FastAPI e um frontend em HTML, CSS e JavaScript.

## Estado atual

A migração da persistência antiga foi concluída. O sistema usa exclusivamente:

```text
CLI / FastAPI
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

`BancoDados`, `GerenciadorDados`, coleções em memória e arquivos JSON não
fazem mais parte do fluxo da aplicação. O `BancoSQLAlchemy` centraliza o
Engine e a fábrica de sessões. O Alembic controla a criação e a evolução do
schema.

## Funcionalidades

- cadastro, consulta, ativação e desativação de clientes;
- cadastro, busca, edição e controle de veículos;
- criação e finalização de aluguéis;
- cálculo de devolução, quilometragem, multa e pagamento;
- abertura e finalização de manutenções;
- relatórios administrativos e financeiros;
- autenticação JWT com perfis de administrador e cliente;
- recuperação de senha por e-mail;
- tokens temporários, de uso único e armazenados por hash;
- CLI e API REST usando a mesma camada de negócio;
- frontend responsivo com login JWT e painel conectado à API;
- transações e rollback em operações compostas;
- documentação OpenAPI/Swagger;
- testes unitários e de integração.

## Tecnologias

- Python;
- HTML, CSS e JavaScript;
- FastAPI e Uvicorn;
- SQLAlchemy 2;
- Alembic;
- SQLite e PostgreSQL;
- Psycopg 3;
- Pydantic;
- PyJWT;
- python-dotenv;
- pytest;
- HTTPX para os testes da API;
- SMTP / smtplib.

## Estrutura

```text
Locadora/
├── api/
│   ├── routers/
│   ├── schemas/
│   ├── dependencias.py
│   ├── erros.py
│   ├── main.py
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
├── alembic.ini
├── .env.example
├── .gitignore
├── carros.py
├── README.md
└── requirements.txt
```

O diretório `scripts/legacy/` preserva apenas o histórico da antiga migração
dos arquivos JSON para SQLite. Ele não participa da execução atual da
aplicação e pode ser removido futuramente quando esse histórico não for mais
necessário.

### Entidades

Os arquivos de domínio em `modulos/` representam clientes, veículos,
aluguéis, manutenções, usuários e pagamentos. Eles concentram regras próprias
do domínio e não executam SQL.

### Models

Os Models em `modulos/models/` descrevem as tabelas do banco com o ORM do
SQLAlchemy. Eles ficam separados das entidades para que a regra de negócio não
dependa da persistência.

### Repositories

Os Repositories recebem `BancoSQLAlchemy`, abrem sessões e convertem Models
ORM em entidades de domínio. Eles são a única camada que consulta ou altera o
banco.

### Services

Os Services executam as regras de negócio e dependem apenas dos contratos
oferecidos pelos Repositories. Eles não conhecem SQLite, SQLAlchemy, HTTP ou a
interface de terminal.

### Container

O `Container` monta uma única infraestrutura de banco, aplica as migrations
pendentes, cria os Repositories, injeta-os nos Services e compartilha a mesma
aplicação entre a CLI e a API.

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

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

Copie `.env.example` para `.env` e configure pelo menos:

```env
LOCADORA_ADMIN_USUARIO=admin
LOCADORA_ADMIN_SENHA=coloque_uma_senha_forte_aqui
LOCADORA_JWT_SECRET=coloque_uma_chave_secreta_forte_aqui
LOCADORA_DATABASE_URL=sqlite:///dados/locadora.db
```

Se `LOCADORA_DATABASE_URL` não for informada, a aplicação continua usando o
SQLite local. Isso mantém o projeto simples para estudos e testes rápidos.

As configurações de SMTP são opcionais, mas necessárias para enviar e-mails de
recuperação de senha.

Nunca envie o arquivo `.env` real ao GitHub. Ele já está listado no
`.gitignore`.

A aplicação valida na inicialização se `LOCADORA_ADMIN_SENHA` e
`LOCADORA_JWT_SECRET` foram configuradas.

## PostgreSQL

O mesmo código da aplicação funciona com SQLite e PostgreSQL. Para usar o
PostgreSQL em desenvolvimento, configure no `.env`:

```env
LOCADORA_DATABASE_URL=postgresql+psycopg://locadora_app:SUA_SENHA@localhost:5432/locadora_dev
LOCADORA_TEST_DATABASE_URL=postgresql+psycopg://locadora_app:SUA_SENHA@localhost:5432/locadora_test
```

Use a senha real apenas no `.env`, nunca no `.env.example`, em commits ou em
mensagens. Se a senha contiver caracteres especiais como `@`, `:`, `/`, `#`
ou `%`, eles precisam ser codificados para uso dentro da URL.

O projeto separa os bancos por finalidade:

- `locadora_dev`: dados usados ao executar a aplicação;
- `locadora_test`: banco descartável usado somente nos testes de integração.

Os dois bancos devem pertencer ao usuário limitado `locadora_app`. A aplicação
não deve se conectar como o superusuário `postgres`.

Depois de configurar a URL de desenvolvimento, aplique o schema:

```bat
python -m alembic upgrade head
python -m alembic current
```

Inicie a API normalmente:

```bat
python -m uvicorn api.main:app --reload
```

O Alembic usa `render_as_batch` somente no SQLite. No PostgreSQL são emitidas
as operações nativas do banco. A migration inicial também mantém `NOCASE`
somente no SQLite e cria o índice parcial de manutenção ativa nos dois bancos.

## Migrations com Alembic

A migration inicial funciona em dois cenários:

- cria todas as tabelas quando o banco está vazio;
- reconhece o schema SQLite legado, recria as tabelas no formato dos Models e
  preserva os registros existentes.

O banco incluído nesta versão já está na revisão:

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

Gerar uma nova migration depois de alterar os Models:

```bash
python -m alembic revision --autogenerate -m "descricao da alteracao"
```

Verificar se Models e banco estão sincronizados:

```bash
python -m alembic check
```

O `migrations/env.py` conecta o Alembic ao `Base.metadata`, lê
`LOCADORA_DATABASE_URL` e ativa `render_as_batch` para alterações
compatíveis com SQLite. Toda migration gerada automaticamente deve ser revisada
antes da execução.

## Execução

### CLI

```bash
python carros.py
```

### API

```bash
python -m uvicorn api.main:app --reload
```

Endereços padrão:

- API: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:8000/app/`
- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`

## Frontend

O frontend é servido pela própria FastAPI. Por isso, não abra os arquivos HTML
diretamente pelo explorador: inicie o Uvicorn e acesse `/app/` pelo navegador.

Os módulos implementados possuem:

- tela de login responsiva;
- integração real com `POST /auth/login`;
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
- visão administrativa de todos os contratos e clientes;
- cadastro público de novas contas de cliente;
- busca e filtros de clientes para administradores;
- desativação e reativação de contas de cliente;
- navegação administrativa escondida de contas comuns;
- painel administrativo de manutenções com busca, filtros e indicadores;
- abertura e finalização de manutenções integradas ao estado da frota;
- histórico de serviços, quilometragem e custos por veículo;
- painel administrativo com resumos operacionais e financeiros;
- rankings de veículos e clientes com limite configurável;
- comparação do faturamento por tipo e dos custos de manutenção;
- consulta do resultado bruto individual de cada veículo;
- solicitação pública de recuperação de senha por nome de usuário;
- redefinição com token temporário, confirmação e validação da nova senha;
- respostas de recuperação que não revelam se uma conta existe;
- tratamento de credenciais inválidas e falha de conexão.

Como o frontend e a API usam a mesma origem, essa etapa não precisa liberar
CORS. As telas reutilizam as funções centralizadas em `frontend/js/api.js`.

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

Nas rotas protegidas, envie:

```http
Authorization: Bearer SEU_TOKEN
```

## Testes

Execute toda a suíte:

```bash
python -m pytest
```

Estado verificado desta versão:

```text
403 passed, 4 skipped
```

Esse resultado ocorre sem a URL do banco PostgreSQL de teste. Quando
`LOCADORA_TEST_DATABASE_URL` está configurada, os quatro testes ignorados são
executados e a suíte completa coleta 407 testes.

Os testes cobrem domínio, Services, Repositories SQLAlchemy, transações,
Container, autenticação, recuperação de senha e endpoints FastAPI.

Os testes PostgreSQL são ignorados quando
`LOCADORA_TEST_DATABASE_URL` não está configurada. Com a variável presente,
execute:

```bat
python -m pytest tests\test_postgresql_integracao.py -q
```

Esses testes apagam e recriam o schema `public`. Por segurança, eles recusam
qualquer banco diferente de `locadora_test` e qualquer usuário diferente de
`locadora_app`. Nunca use a URL de `locadora_dev` nessa variável.

## Segurança

- senhas novas usam PBKDF2-HMAC-SHA256 com salt aleatório;
- hashes SHA-256 antigos são aceitos apenas para compatibilidade;
- tokens de recuperação são aleatórios e apenas seu hash é persistido;
- tokens expiram, são de uso único e invalidam solicitações anteriores;
- respostas de login e recuperação evitam revelar se uma conta existe;
- permissões são verificadas por perfil;
- segredos e credenciais ficam em variáveis de ambiente.

## Trilha do projeto

- POO e domínio: concluído;
- arquitetura em camadas: concluído;
- Repository Pattern e injeção de dependência: concluído;
- FastAPI, Pydantic, JWT e OpenAPI: concluído;
- migração completa para SQLAlchemy: concluída;
- testes automatizados: concluído e em evolução;
- Alembic e migrations: concluído;
- frontend com HTML, CSS e JavaScript: concluído;
- login, sessão JWT e painel inicial: concluídos;
- consulta e gerenciamento da frota no frontend: concluídos;
- criação, devolução e acompanhamento de aluguéis no frontend: concluídos;
- cadastro e gerenciamento de clientes no frontend: concluídos;
- abertura, finalização e acompanhamento de manutenções no frontend: concluídos;
- relatórios operacionais, rankings e resultados financeiros no frontend: concluídos;
- recuperação e redefinição de senha no frontend: concluídas;
- revisão final de integração e acabamento do frontend: concluída;
- material completo de revisão do projeto: concluído;
- Git e GitHub: concluídos e em evolução;
- PostgreSQL e Psycopg: concluídos;
- testes de integração com PostgreSQL: concluídos;
- Docker, CI/CD e deploy: planejados.
