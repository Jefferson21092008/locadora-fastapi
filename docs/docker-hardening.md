# Docker hardening

## Objetivo

A Etapa 23 reduz a superfície de ataque da imagem e limita o impacto de uma eventual falha dentro do container. Ela não altera regras de negócio nem substitui controles da aplicação.

## Imagem de produção

O `Dockerfile` usa build multi-stage. Dependências são instaladas em um virtualenv no estágio `builder`; o estágio `runtime` recebe somente o virtualenv e os arquivos necessários para executar API, frontend estático e migrations. Testes, documentação, arquivos de ambiente e artefatos locais não são copiados para a imagem final.

O processo roda como `app` com UID/GID 10001, sem diretório home e com shell de login bloqueado. O container não inicia como root.

A imagem final possui `HEALTHCHECK` nativo em `/health`, `STOPSIGNAL SIGTERM` e inicia por `python -m modulos.container_entrypoint`, sem `sh -c`. O entrypoint valida a porta, executa Alembic quando habilitado e substitui o PID pelo Uvicorn com `os.execv`. O header `Server` do Uvicorn é desabilitado.

## Dependências

`requirements.txt` contém apenas dependências necessárias em runtime. `pytest` fica em `requirements-dev.txt`; `httpx2`, que não é utilizado pela aplicação, foi removido. Isso reduz pacotes disponíveis dentro da imagem de produção.

## Docker Compose

Os serviços `api` e `migrate` recebem controles adicionais:

- filesystem raiz somente leitura;
- `/tmp` temporário com `noexec` e `nosuid`;
- remoção de Linux capabilities com `cap_drop: ALL`;
- `no-new-privileges`;
- limite de PIDs;
- usuário não root definido na própria imagem.

No Compose, migrations rodam no serviço dedicado `migrate`; por isso a API recebe `LOCADORA_EXECUTAR_MIGRATIONS=false`. A porta interna fica explicitamente em `8000`. No Render, o entrypoint mantém migrations habilitadas por padrão e usa a variável `PORT` fornecida pela plataforma.

## Build context

`.dockerignore` exclui testes, documentação, arquivos `.env`, exemplos de ambiente, coverage, backups, banco local e arquivos apenas de desenvolvimento. Além de reduzir o contexto enviado ao daemon, isso diminui o risco de conteúdo desnecessário entrar em camadas futuras por engano.

## CI

Além de construir a imagem, o job Docker verifica que:

1. `Config.User` é `app:app`;
2. há `HEALTHCHECK`;
3. o UID efetivo é 10001;
4. `pytest` não existe na imagem de produção.

## Limitações

Containers não são uma fronteira de segurança absoluta. Secrets continuam fora da imagem, o host/serviço de execução precisa ser atualizado, e dependências continuam sendo auditadas. Em produção no Render, controles de runtime equivalentes a `cap_drop` e `read_only` dependem do que a plataforma gerenciada expõe; as proteções que pertencem à imagem continuam válidas independentemente do Compose local.
