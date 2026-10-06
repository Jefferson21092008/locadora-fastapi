# Concorrência e consistência transacional

A Etapa 25 reforça operações críticas da Locadora para que duas requisições
concorrentes não consigam persistir estados incompatíveis. O foco é manter o
PostgreSQL como fonte de verdade e usar garantias do próprio banco, em vez de
criar locks apenas em memória dentro da API.

## Problemas tratados

Os cenários mais sensíveis são:

- duas reservas sobrepostas para o mesmo veículo;
- dois aluguéis simultâneos do mesmo veículo;
- aluguel e manutenção disputando o mesmo veículo;
- reserva criada enquanto uma manutenção é aberta ou reprogramada;
- duas devoluções ou finalizações da mesma operação;
- dois pagamentos simultâneos consumindo o mesmo saldo pendente;
- dois estornos concorrentes do mesmo pagamento.

Antes desta etapa, vários services validavam o estado e depois chamavam o
repository em outra transação. Entre a leitura e a gravação, outra requisição
podia alterar o banco. Esse intervalo é uma race condition clássica do tipo
"check-then-act".

## Estratégia

### 1. Lock pessimista por linha

Os repositories críticos usam `SELECT ... FOR UPDATE` no PostgreSQL antes de
revalidar e alterar o estado persistido. A linha de `veiculos` funciona como
ponto de serialização das operações ligadas ao mesmo veículo.

A ordem adotada é previsível:

```text
veículo
  ↓
entidade dependente, quando necessário
  ↓
revalidação
  ↓
escritas
  ↓
commit único do repository
```

Manter a mesma ordem reduz o risco de deadlocks quando mais de uma linha precisa
ser bloqueada.

O helper `modulos.concorrencia.buscar_por_id_para_atualizacao()` centraliza a
consulta e força `populate_existing`, evitando que um objeto antigo do identity
map seja usado depois da aquisição do lock.

### 2. Revalidação dentro da transação

O lock sozinho não substitui a regra de negócio. Depois de adquirir o lock, o
repository consulta novamente o estado que realmente será persistido.

Exemplos:

- `ReservaRepository.registrar()` volta a verificar reservas, aluguel ativo e
  manutenção ativa antes do `INSERT`;
- `AluguelRepository.registrar()` volta a verificar disponibilidade, aluguel
  ativo e reserva concorrente;
- `ManutencaoRepository.registrar()` e `atualizar()` voltam a verificar reservas
  futuras depois de bloquear o veículo;
- devolução e finalização rejeitam uma segunda operação se o registro já tiver
  mudado de estado;
- `PagamentoRepository.registrar()` bloqueia o aluguel, soma pagamentos
  confirmados novamente e só então aceita o novo valor.

### 3. Invariante também no banco

A migration `20261006_0010_consistencia_concorrencia` cria o índice parcial
único:

```text
idx_aluguel_ativo_veiculo
```

Ele permite no máximo um aluguel com `status = 'ativo'` para cada `veiculo_id`.
Assim, mesmo um caminho de código futuro que esqueça a revalidação não consegue
persistir dois aluguéis ativos do mesmo veículo.

A migration faz uma verificação antes de criar o índice. Se encontrar dados
históricos inconsistentes, ela interrompe com uma mensagem explícita em vez de
ocultar ou excluir registros.

### 4. Conflito HTTP explícito

Foi adicionada `ConflitoConcorrencia`, que herda de `RegraDeNegocio`. Quando uma
requisição perdeu a corrida porque o estado mudou enquanto ela era processada,
a API responde HTTP `409 Conflict`.

Isso diferencia:

```text
400 -> entrada/regra inválida independentemente de concorrência
409 -> a operação era plausível, mas o estado mudou antes do commit
```

O cliente pode atualizar os dados e tentar novamente quando fizer sentido.

## Pagamentos concorrentes

O service calcula o limite total de pagamentos adicionais permitido para o
aluguel e o repository volta a verificar esse limite depois de bloquear a linha
do aluguel.

Exemplo:

```text
saldo adicional permitido: R$ 100
requisição A: R$ 70
requisição B: R$ 70
```

Sem serialização, as duas poderiam ler saldo de R$ 100 e confirmar R$ 140. Com o
lock, uma confirma primeiro; a outra enxerga os R$ 70 já persistidos e recebe
conflito.

Estornos seguem a mesma ideia: aluguel e pagamento são revalidados antes da
mudança, impedindo que duas requisições concluam o mesmo estorno como se fossem a
primeira.

## SQLite x PostgreSQL

O SQLAlchemy omite `FOR UPDATE` em SQLite. Isso é aceitável para o uso local e
para a maioria dos testes unitários, mas não equivale ao lock pessimista do
PostgreSQL.

Por esse motivo, os testes realmente concorrentes da etapa são executados contra
`LOCADORA_TEST_DATABASE_URL`, no banco descartável `locadora_test`, usando duas
threads e duas sessões independentes. O PostgreSQL é a referência para o
comportamento de produção.

## Testes PostgreSQL da etapa

A suíte de integração valida:

- índice único de aluguel ativo;
- duas reservas sobrepostas iniciadas ao mesmo tempo;
- dois aluguéis concorrentes do mesmo veículo;
- dois pagamentos concorrentes que juntos excederiam o limite.

Nos cenários concorrentes, o resultado esperado é:

```text
1 operação confirmada
1 operação rejeitada com ConflitoConcorrencia
estado final válido no banco
```

## Limites desta etapa

Esta etapa protege as principais mutações atuais, mas não transforma toda leitura
da aplicação em operação serializável. Consultas de relatório, dashboard e
listagens continuam usando o isolamento normal do PostgreSQL, porque bloquear
leituras analíticas reduziria concorrência sem ganho de consistência para o
caso de uso.

Também não foi elevado globalmente o nível de isolamento para `SERIALIZABLE`.
Locks pontuais e invariantes de banco são mais previsíveis para os fluxos atuais
e evitam retries desnecessários em toda a aplicação.

Mudanças futuras que criem novos caminhos de escrita para veículo, reserva,
manutenção, aluguel ou pagamentos devem reutilizar a mesma ordem de lock e
revalidar o estado dentro da transação.
