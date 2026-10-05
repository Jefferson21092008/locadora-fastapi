# Ambientes: development, test, staging e production

A Locadora usa `LOCADORA_AMBIENTE` como fonte de verdade para distinguir a execução local, testes, homologação e produção. Os valores canônicos são `development`, `test`, `staging` e `production`.

## Matriz

| Ambiente | Uso | Banco | URL pública | Jobs |
|---|---|---|---|---|
| development | desenvolvimento local | SQLite ou PostgreSQL local | HTTP local permitido | normalmente desligados |
| test | pytest, CI e E2E | bancos descartáveis | não pública | desligados salvo teste explícito |
| staging | homologação antes de produção | PostgreSQL separado | HTTPS obrigatório | desligados por padrão |
| production | usuários reais | PostgreSQL de produção | HTTPS obrigatório | conforme operação |

## Regras de segurança

- `staging` e `production` exigem `LOCADORA_DATABASE_URL` explícita; o fallback SQLite local é recusado.
- `staging` e `production` exigem PostgreSQL e `LOCADORA_PUBLIC_URL` em HTTPS.
- Bancos, Redis e segredos de staging e produção não devem ser compartilhados.
- O prefixo Redis deve identificar o ambiente (`locadora:staging`, `locadora:production`).
- Arquivos `.env`, `.env.staging`, `.env.production` e equivalentes são locais e não entram no Git. Somente arquivos `*.example` podem ser versionados.
- Staging deve usar dados sintéticos/anônimos; não copie dados pessoais de produção para homologação.

## Arquivos de exemplo

- `.env.development.example`: desenvolvimento local.
- `.env.staging.example`: referência para homologação.
- `.env.production.example`: referência para produção.
- `.env.docker.example`: desenvolvimento local via Docker Compose.

Os exemplos não contêm segredos reais. Em Render, Neon, Sentry, Brevo e Redis/Valkey, configure credenciais no painel do provedor.

## Staging no Render

`render.staging.yaml` documenta um serviço de homologação separado. Antes de criá-lo, disponibilize um PostgreSQL exclusivo de staging e, se usar cache/rate limit distribuído, um Redis/Valkey separado ou ao menos um namespace exclusivo.

O staging mantém `LOCADORA_BACKGROUND_JOBS_ENABLED=false` por padrão para evitar notificações automáticas durante homologação. Ative somente quando o comportamento estiver sendo testado conscientemente com destinatários seguros.

## Fluxo recomendado

```text
development -> testes/CI -> staging -> production
```

Uma mudança deve passar pela suíte automatizada antes de staging. Staging é usado para smoke tests e validação integrada com configuração próxima da produção. Somente depois a mudança segue para produção.
