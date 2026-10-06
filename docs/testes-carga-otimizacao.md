# Testes de carga e otimização

A Etapa 24 mede desempenho antes de otimizar. O objetivo não é descobrir um
"número mágico" de usuários, mas criar uma baseline reproduzível e usar os
dados para decidir onde vale otimizar.

## Regras de segurança

- O alvo padrão é `http://127.0.0.1:8000`.
- Destinos remotos são bloqueados por padrão.
- `--allow-remote` deve ser usado somente em staging controlado.
- Não execute carga contra produção sem autorização e janela planejada.
- Senhas não entram na linha de comando nem no arquivo de resultados.
- Resultados locais ficam em `performance-results/`, ignorado pelo Git.

## Métricas

O runner registra:

- total de requisições;
- taxa de sucesso;
- throughput em requisições por segundo;
- média, mediana, p95, p99 e máximo de latência;
- distribuição de status HTTP.

P95 é uma das métricas principais: 95% das requisições terminaram em tempo
menor ou igual ao valor informado.

## Cenários

`health`
: valida API + round-trip simples ao banco, porque `/health` testa conexão.

`veiculos`
: consulta pública paginada de veículos.

`dashboard-cache`
: consulta autenticada do dashboard usando o fluxo normal de cache-aside.

`dashboard-db`
: consulta autenticada com `?atualizar=true`, forçando recálculo no banco.

`misto`
: alterna health, consulta paginada e dashboard para representar tráfego menos
artificial.

## Baseline local recomendada

Suba o Docker Compose da Locadora e confirme `api`, `db` e `cache` saudáveis.
Comece pequeno para não transformar a máquina de desenvolvimento no gargalo.

```cmd
python -m scripts.performance.load_test --cenario health --usuarios 5 --requisicoes-por-usuario 20 --output performance-results\health-baseline.json
```

Depois:

```cmd
python -m scripts.performance.load_test --cenario veiculos --usuarios 5 --requisicoes-por-usuario 20 --output performance-results\veiculos-baseline.json
```

Para cenários autenticados, informe credenciais somente na sessão do terminal:

```cmd
set LOCADORA_LOAD_USUARIO=admin
set LOCADORA_LOAD_SENHA=SUA_SENHA_LOCAL
```

Então compare cache e banco:

```cmd
python -m scripts.performance.load_test --cenario dashboard-cache --usuarios 5 --requisicoes-por-usuario 20 --output performance-results\dashboard-cache-baseline.json
python -m scripts.performance.load_test --cenario dashboard-db --usuarios 5 --requisicoes-por-usuario 20 --output performance-results\dashboard-db-baseline.json
```

Ao terminar:

```cmd
set LOCADORA_LOAD_USUARIO=
set LOCADORA_LOAD_SENHA=
```

## Escada de carga

Não comece com centenas de usuários em um notebook pequeno. Use uma escada:

1. 5 usuários × 20 requisições;
2. 10 usuários × 20 requisições;
3. 20 usuários × 20 requisições;
4. aumente somente se a máquina cliente e o servidor ainda estiverem estáveis.

Aumentar concorrência até o notebook ficar sem RAM não mede a capacidade da API;
mede a limitação da máquina que está gerando a carga.

## Critério de regressão

Depois de obter uma baseline confiável, o runner pode virar um gate manual:

```cmd
python -m scripts.performance.load_test --cenario health --usuarios 10 --requisicoes-por-usuario 20 --min-success-rate 99 --max-p95-ms 500
```

Se a taxa de sucesso ou o p95 violarem o limite, o comando termina com código
diferente de zero.

## Processo de otimização

1. medir baseline;
2. identificar o endpoint/gargalo;
3. formular uma hipótese;
4. fazer uma alteração pequena;
5. repetir exatamente a mesma carga;
6. comparar p95, throughput e erros;
7. manter a mudança somente se houver ganho ou justificativa operacional.

Não é recomendado criar índice, aumentar pool, adicionar cache ou paralelismo sem
uma evidência mensurável. A Etapa 24 deve evitar otimização prematura.

## Diagnóstico e decisão da Etapa 24

A baseline local de 10 usuários × 30 requisições manteve 100% de sucesso em
todos os cenários medidos. O `dashboard-db` foi o cenário mais lento, enquanto
a consulta paginada de veículos também apresentou degradação relevante com o
aumento de concorrência. Durante o `dashboard-db`, `docker stats` mostrou carga
principalmente na API e no PostgreSQL, sem pressão relevante de memória.

Foram experimentadas duas otimizações pequenas e isoladas:

- agregações condicionais no dashboard para reduzir subconsultas repetidas;
- `COUNT(*) OVER()` na paginação de veículos para eliminar um round-trip de
  `COUNT` em páginas com resultados.

As medições posteriores mostraram variação alta entre execuções idênticas no
ambiente local. O próprio `/health`, sem alteração de código, apresentou
variações relevantes de throughput e percentis. Em veículos, execuções com o
mesmo código oscilaram fortemente; no dashboard, a mediana de três execuções
otimizadas melhorou throughput e latência média apenas alguns pontos
percentuais, enquanto p95/p99 não melhoraram de forma consistente.

Por isso, a decisão da Etapa 24 é **não manter as duas otimizações de produção
que não demonstraram ganho estável**. O código funcional anterior é preservado,
e permanecem no projeto a infraestrutura de carga, os cenários reproduzíveis,
a gravação de resultados e o comparador baseline × candidato. Isso evita
otimização prematura e deixa uma base objetiva para futuras mudanças de
performance em hardware e ambientes mais controlados.

Resultados JSON de execução continuam locais em `performance-results/` e não
devem ser versionados.

Para comparar duas execuções compatíveis:

```cmd
python -m scripts.performance.compare_results performance-results\BASELINE.json performance-results\CANDIDATO.json
```

O comparador recusa arquivos com cenário, usuários, requisições por usuário ou
aquecimento diferentes para reduzir comparações enganosas.
