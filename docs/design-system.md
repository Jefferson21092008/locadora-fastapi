# Design System da Locadora

A Etapa 11 consolida a base visual do frontend sem alterar as regras de negócio ou a API.

## Objetivos

- manter uma identidade visual consistente entre autenticação, dashboard e telas operacionais;
- reduzir CSS improvisado por tela por meio de tokens compartilhados;
- preservar contraste, foco visível e navegação por teclado;
- manter a interface utilizável em desktop, tablet e celular;
- evitar dependências externas de fonte, ícones ou frameworks.

## Tokens

Os tokens vivem em `frontend/css/styles.css`, dentro de `:root`.

### Cores

A interface usa uma base azul-marinho para navegação, teal como cor de ação/estado positivo e âmbar como destaque. Cores semânticas continuam disponíveis para sucesso e erro.

Principais aliases:

```css
--surface
--surface-subtle
--background
--border
--border-strong
--accent
--accent-strong
--accent-soft
--danger
--success
```

### Espaçamento

A escala compartilhada é:

```css
--space-1
--space-2
--space-3
--space-4
--space-5
--space-6
--space-8
--space-10
--space-12
```

### Bordas, sombras e movimento

Componentes reutilizam `--radius-*`, `--shadow-*`, `--transition-fast` e `--transition-base`. A intenção é manter elevação e movimento discretos, sem transformar hover em uma mudança brusca de layout.

## Componentes base

Os componentes já existentes foram padronizados em vez de substituídos:

- `primary-button`, `secondary-button` e `card-button`;
- `field`, `search-field` e `select-field`;
- `metric-card`, `vehicle-card`, `client-card` e demais cards operacionais;
- `fleet-content` e `fleet-overview`;
- `modal`;
- `sidebar` e `nav-item`;
- estados de carregamento, vazio, sucesso e erro.

Essa abordagem mantém os IDs e classes consumidos pelo JavaScript e reduz o risco de regressão funcional.

## Layout responsivo

Em desktop, a navegação continua lateral. Abaixo de 860 px, ela passa a ocupar o topo, permanece visível durante a rolagem e oferece navegação horizontal. Em telas menores, grids, ações e formulários reduzem para uma coluna quando necessário.

## Acessibilidade

Todas as páginas recebem um link “Ir para o conteúdo principal”, visível ao receber foco, apontando para `#main-content`.

O frontend mantém:

- `:focus-visible` perceptível;
- suporte a `prefers-reduced-motion`;
- landmarks semânticos;
- labels já associados aos campos;
- mensagens de estado com `aria-live` onde a aplicação já as utiliza.

## Evolução

Esta etapa é a fundação visual. Dashboard e telas de domínio podem evoluir nas próximas etapas reaproveitando os mesmos tokens e componentes, evitando redesenhar a base em cada página.

## Dashboard operacional — Etapa 12

O dashboard passa a ser a primeira superfície operacional da aplicação, e não apenas uma coleção de contadores.

A composição reutiliza os tokens da Etapa 11 e organiza a tela em três níveis:

1. identificação da conta e contexto da sessão;
2. indicadores principais da locadora;
3. atalhos de navegação e estado de sincronização com a API.

### Indicadores

Os quatro indicadores mantêm os mesmos dados fornecidos por `/api/v1/status`, sem criar métricas derivadas ou regras novas no frontend. Durante a atualização, os cards usam estado visual de carregamento e `aria-busy`.

### Acesso rápido

Os atalhos para Veículos e Aluguéis ficam disponíveis conforme a navegação já existente. Clientes, Manutenções e Relatórios continuam respeitando o RBAC do backend e a mesma matriz de permissões usada para esconder links administrativos na navegação.

O frontend apenas adapta a interface. A autorização efetiva permanece nas rotas da API.

### Estado da operação

O painel de sistema informa quando os dados estão sendo sincronizados, quando a última atualização foi concluída e quando houve falha de comunicação. O horário exibido corresponde à atualização concluída no navegador do usuário.

### Responsividade

Em telas largas, atalhos e estado da operação ocupam colunas distintas. Em larguras intermediárias eles passam a uma coluna e, em telas pequenas, os indicadores e atalhos também são empilhados.

As animações de carregamento respeitam `prefers-reduced-motion`.
