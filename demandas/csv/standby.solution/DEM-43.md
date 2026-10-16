---
id: DEM-43
status: standby
data_ativacao: 2026-09-16 11:00:13
data_reabertura: 2026-10-07 15:00:00
data_conclusao: 2026-09-25 11:20:00
modulo: Contratar Instâncias
data_standby: 2026-10-14
aguardando: Eduardo
pendencia: corrigir URL e chave do Asaas no dev (hoje chama api.asaas.com e recebe 401) e trocar a chave exposta no log; depois o QA retesta as tasks #43 e #82
---

# 🚀 Histórico de Execução: Divergência entre data de vencimento das assinaturas no Asaas e na UzAPI

## 📌 Resumo do Problema
Quando o usuário contrata instância pela primeira vez é criada uma assinatura no Asaas com a Data Atual + Dias de Corte. Isso faz com que a data de vencimento na UzAPI fique divergente, pois nela é salva apenas a data atual em que o usuário fez a assinatura.

**OBS:** A DATA DE CORTE NÃO DEVE SER USADA NO CÁLCULO DE DATA DE VENCIMENTO. BASICAMENTE, ELA TEM QUE ATUAR COMO UM CRON QUE IRÁ SE BASEAR NA DATA DE VENCIMENTO DA ASSINATURA DO CLIENTE (QUE INCLUSIVE TEM QUE SER IDÊNTICAS ENTRE O ASAAS E A UZAPI). OU SEJA, QUANDO CHEGAR NA DATA DE VENCIMENTO, O CLIENTE JÁ É ALERTADO SOBRE A RENOVAÇÃO. MAS QUANDO CHEGAR X DIAS DEPOIS DO VENCIMENTO DELE, A ASSINATURA É PAUSADA. ESSE BUG TEM RELAÇÃO COM O BUG DE ID 16.

---

## 🔄 Reabertura e Feedback de Homologação do Cliente (25/09/2026)

### Relato de Devolução (CSV):
> *"O BUG PERSISTE: ASSINATURA NA UZAPI FICA COM A DATA CORRETA (DATA ATUAL). JÁ NO ASAAS, A ASSINATURA FICA ERRADA (DATA ATUAL + X DIAS RESTANTES DO TRIAL)"*

### Diagnóstico Aprofundado da Causa Raiz:
1. **No arquivo `create-instance-payment.ts`:**
   A lógica anterior utilizava `cycle.visibleExpiresAt && cycle.visibleExpiresAt > new Date() ? cycle.visibleExpiresAt : new Date()`.
   Quando um cliente em período de teste contratava um plano pago, `cycle.visibleExpiresAt` continha a data futura do fim do Trial (ex: 3 a 5 dias à frente). O código empurrava o primeiro vencimento (`nextDueDate`) no Asaas para o fim do Trial, enquanto na UzAPI a assinatura era ativada imediatamente na Data Atual.
2. **No arquivo `payment-confirmation.ts`:**
   Ao compensar a fatura de um cliente vindo de Trial (`INITIAL`), a checagem `isAfter(billingBefore.expiresIn, now)` considerava o Trial ainda válido e chamava `extendCycleExpiresIn()`, somando 30 dias em cima do prazo residual de teste em vez de iniciar um ciclo limpo a partir de `now`.
3. **No arquivo `asaas-subscription-sync.ts`:**
   Na criação da assinatura recorrente (`applyRecurrentSubscriptionFromContract`), o parâmetro `nextDueDate` utilizava `billing.expiresIn` bruto, que embute os dias de tolerância/carência do corte (`gracePeriodDays`), empurrando a cobrança 7 dias para além do vencimento oficial.

---

## 🛠️ Solução Adotada (Correção Definitiva)

1. **`manager-service/src/lib/create-instance-payment.ts`:**
   - Adicionada a trava `isNewOrTrial` cobrindo `isTrialUser`, `contractType === "INITIAL"` e status `TRIAL`/`TRIAL_EXPIRED`.
   - Para qualquer cliente vindo de Trial ou primeira contratação, o `nextDueDate` no Asaas é fixado estritamente em **`new Date()` (Hoje)**, eliminando a defasagem dos dias residuais de teste.
   - Para renovações de clientes já pagantes ativos, preserva-se o vencimento do plano oficial (`cycle.visibleExpiresAt`).

2. **`manager-service/src/lib/payment-confirmation.ts`:**
   - Adicionada a condicional `isFromTrialOrInitial`. Quando o contrato é `INITIAL` ou o usuário era `TRIAL`/`TRIAL_EXPIRED`, o ciclo de 30 dias na UzAPI é sempre inicializado a partir de agora (`computeRenewalExpiresIn(now, gracePeriod)`), sem estender sobre dias de teste anteriores.
   - O método `extendCycleExpiresIn()` fica restrito exclusivamente a renovações legítimas (`RENEWAL`).

3. **`manager-service/src/lib/asaas-subscription-sync.ts`:**
   - Refatorada a função `applyRecurrentSubscriptionFromContract` para extrair a data oficial via `getBillingCycleContextSync(billing, gracePeriodDays).visibleExpiresAt`.
   - Os dias de tolerância/corte (`gracePeriodDays`) são totalmente isolados e nunca mais são somados à fatura do cliente no Asaas.

---

## 🧪 Testes Automatizados e Homologação

1. **Testes Unitários de Ciclo e Contratos (`npm run test:unit`):**
   - Suíte `contract-calculator.test.ts` atualizada com novo teste garantindo que o Trial não subtrai carência nem altera o vencimento visível e que a primeira contratação (0 instâncias) define tipo `INITIAL` e `isUpgrade: false`:
   - **Resultado:** 8 testes executados com 100% de aprovação (`pass: 8, fail: 0`).
2. **Compilador Estrito (`npx tsc --noEmit`):**
   - Compilação do TypeScript concluída com código de saída 0 (sem erros de tipagem).
3. **Linter do Projeto (`npx eslint`):**
   - Análise estática aprovada com 0 erros e 0 warnings.
4. **Gitflow, Releases e Produção:**
   - **Etapa 1:** Branch `fix/dem-43-asaas-duedate` (commit `8903fb6`) mesclada na `main`, gerando tag de release `v0.3.53`.
   - **Etapa 2 (Ajuste Fino de Fatura Avulsa):** Branch `fix/dem-43-invoice-initial-duedate` (commit `2dae680`) mesclada na `main`, gerando tag de release `v0.3.54`.
   - **Deploy em Produção:** Imagem `manager-service:v0.3.54` aplicada via `infra-gitops` (commit `6745847`) e em execução em `https://painel.uzapi.com.br`.

---

## 📂 Arquivos Modificados
- `manager-service/src/lib/create-instance-payment.ts`: Força `nextDueDate = new Date()` (hoje) para transições de trial e fixa `dueDate = new Date()` para faturas avulsas de contratações iniciais.
- `manager-service/src/lib/payment-confirmation.ts`: Ciclo de 30 dias limpo em transições de trial (`isFromTrialOrInitial`).
- `manager-service/src/lib/asaas-subscription-sync.ts`: Assinatura recorrente usa `visibleExpiresAt` oficial sem carência.
- `manager-service/src/lib/contract-calculator.ts`: Travada a condição de upgrade (`effectivePreviousInstances > 0`), impedindo que 0 → 1 seja tratado como upgrade proporcional.
- `manager-service/src/lib/contract-calculator.test.ts`: Testes unitários para ciclo de trial e contratação inicial.

---

## ⏸️ Standby / Aguardando Decisão (02/10/2026)
Esta tarefa foi devolvida pelo QA apontando que a assinatura no Asaas ficava com "Data Atual + X Dias". Após auditoria no código da branch `main` (`v0.3.54` e superiores), foi constatado matematicamente que o código envia estritamente `new Date()` (Data Atual) para o Asaas quando o cliente vem de TRIAL ou contrata do zero (`isNewOrTrial = true`). A única forma do sistema manter a data antiga é num **Upgrade Proporcional (Prorated)** de um cliente já ativo (o que é o comportamento financeiro correto).
A tarefa foi movida para **Standby** aguardando alinhamento com os testadores, pois trata-se de um Falso Positivo provocado por testes em versão desatualizada ou má interpretação da regra de upgrade.

---

## 🔎 Atualização 05–06/10/2026: reanálise da devolução e auditoria de release

> **Status:** segue em **standby**, aguardando retorno do QA. Nenhum código alterado nesta reanálise.

### Relato mais recente do QA (CSV)
> *"ESTÁ SENDO GERADO A PRIMEIRA COBRANÇA COM A DATA CORRETA (DATA ATUAL), PORÉM A ASSINATURA CONTINUA COM O VENCIMENTO ERRADO (DATA ATUAL + X DIAS RESTANTES DO TRIAL)"*

### O que o código da `main` (`v0.3.57`) faz — trial que contrata com pagamento recorrente
| Etapa | Onde | Data |
|---|---|---|
| Cobrança avulsa | `create-instance-payment.ts:222` (`isNewOrTrial` → `dueDate = new Date()`) | hoje |
| Confirmação do pagamento | `payment-confirmation.ts:112` (`contractType === "INITIAL"` → `computeRenewalExpiresIn(now, gracePeriod)`) | `expiresIn` = hoje + 30 + carência |
| Criação da assinatura no Asaas | `asaas-subscription-sync.ts:119` (`cycle.visibleExpiresAt` do billing já `ACTIVE`) | `nextDueDate` = hoje + 30 |

Pelo código atual, UzAPI (vencimento visível) e Asaas ficam iguais. O sintoma relatado corresponde ao código de **`≤ v0.3.52`**: `payment-confirmation.ts` tratava `INITIAL` como `RENEWAL` (`extendCycleExpiresIn` sobre o fim do trial) e `asaas-subscription-sync.ts` usava `billing.expiresIn` bruto → assinatura em hoje + 30 + dias restantes do trial. Exemplo citado no handover (assinatura de 3 instâncias com vencimento 01/11/2026) = compra em 25/09 + 30 + 7 dias de carência, pelo código antigo.

### Auditoria de release (pedido do programador chefe)
`8903fb6` → tag `v0.3.53` (25/09 14:49) e `2dae680` → tag `v0.3.54` (25/09 15:43); o GitLab CI atualizou o `infra-gitops` minutos depois de cada tag. **A correção foi liberada**; não foi possível conferir o cluster.

### Hipótese principal para a devolução
A correção não ajusta assinaturas já criadas no Asaas. Uma assinatura anterior a 25/09 mantém a data antiga e só é substituída quando um novo pagamento é confirmado (`replaceRecurrentSubscription` roda em `applyPaymentConfirmation`). Se o QA gerou uma cobrança nova e conferiu a assinatura sem pagar, ou reusou um usuário de teste antigo, verá "cobrança certa, assinatura errada". **Não confirmado** — a cópia local do banco vai até 10/09 e não há chave do Asaas no ambiente de desenvolvimento.

### Defeitos reais encontrados na mesma área (não corrigidos)
1. **Assinaturas anteriores à correção não foram ajustadas** (sem backfill do `nextDueDate` no Asaas).
2. **Confirmação sem trava de repetição:** `webhook.ts` chama `applyPaymentConfirmation` para `PAYMENT_CONFIRMED` e `PAYMENT_RECEIVED`. No segundo evento do mesmo pagamento o contrato já tem `paymentId`, `contract` vira `null`, `contractType` cai em `"INITIAL"` e o ciclo é reiniciado a partir desse dia (`computeRenewalExpiresIn(now)`), enquanto a assinatura no Asaas não muda. Leitura de código; não reproduzido.
3. **Datas em UTC:** `toISOString().split("T")[0]` em `asaas.ts` (`createInvoice`) e `asaas-subscription-sync.ts` → compra após 21h (Brasília) sai com vencimento no dia seguinte.
4. **Trial com custo zero** (cupom de 100%): `create-instance-payment.ts:141` não altera `expiresIn` (fica o fim do trial) e a assinatura no Asaas começa hoje.
5. Ponto frágil: em `payment-confirmation.ts` a checagem `billingBefore.subscriptionStatus === "TRIAL"` nunca é verdadeira para cobranças pagas, porque o status foi trocado para `PENDING` ao gerar a cobrança; funciona apenas pelo `contractType === "INITIAL"`.

### Encaminhamento
- Mensagem enviada ao QA (05/10) pedindo: usuário do teste (novo ou reaproveitado), data de criação da assinatura no painel do Asaas e se a cobrança foi paga antes da conferência; e um novo teste do zero.
- Proposto e **não autorizado ainda**: teste automatizado do fluxo com o Asaas simulado (Postgres local) e correção dos itens 1 a 4 em branch `fix/dem-43-...`.

---

## 🔁 Reaberta para Desenvolvimento (07/10/2026)

> Movida de `standby.solution/` para `exec/` com `status: pendente`: no backlog (CSV exportado em 07/10/2026 14:48) a demanda continua **Devolvido** (Urgente, Hugo Peres, módulo Contratar Instâncias).

- **Texto da devolução no CSV:** sem alteração em relação a 05/10 — último relato: *"ESTÁ SENDO GERADO A PRIMEIRA COBRANÇA COM A DATA CORRETA (DATA ATUAL), PORÉM A ASSIANTURA CONTINUA COM O VENCIMENTO ERRADO (DATA ATUAL + X DIAS RESTANTES DO TRIAL)"*. Campo Observações: "Nenhuma".
- **Retorno do QA à mensagem de alinhamento de 05/10:** não registrado até aqui.
- **Situação técnica:** a da seção "Atualização 05–06/10/2026" acima — correção liberada em 25/09 (`v0.3.53`/`v0.3.54`); pelo código atual as datas ficam iguais; hipótese principal de assinatura criada antes da correção; quatro defeitos reais listados e ainda não corrigidos.
- **Próximo passo proposto (aguardando autorização):** branch `fix/dem-43-...` no `manager-service` com (1) teste automatizado do fluxo com o Asaas simulado, (2) trava contra reprocessamento do mesmo pagamento, (3) datas no fuso de Brasília, (4) caso de custo zero e (5) script para alinhar as assinaturas antigas.

### 🧭 Histórico consolidado e correção de leitura (07/10/2026)

| Rodada | Código | Release | O que mudou |
|---|---|---|---|
| 1 | `a0a5811` (16/09), merge `68d00bd` (22/09) | `v0.3.51` (24/09) | Assinatura criada no checkout sem pagamento passa a usar `cycle.visibleExpiresAt` em vez de `billing.expiresIn` bruto |
| 2 | `8903fb6` (25/09 11:18), merge `c613265` | `v0.3.53` (25/09 14:49) | Trial/primeira contratação inicia ciclo de 30 dias a partir do pagamento; assinatura pós-pagamento usa `visibleExpiresAt` |
| 3 | `2dae680` (25/09 15:35), merge `3622a53` | `v0.3.54` (25/09 15:43) | Cobrança avulsa de trial/primeira contratação com `dueDate` = hoje (até a `v0.3.53` era hoje + 3 dias); 0 → 1 instância deixa de ser "upgrade" |

**Correção da leitura feita em 05/10:** o último relato do QA reconhece que a primeira cobrança sai com a data atual. Isso só passou a acontecer na `v0.3.54` (até a `v0.3.53` a cobrança avulsa saía com hoje + 3 dias). Portanto esse teste foi feito **depois** das três rodadas, e não em versão antiga. A hipótese de "teste em versão anterior à correção" fica descartada para este relato; seguem possíveis: assinatura já existente no Asaas e ainda não substituída (a troca só ocorre na confirmação do pagamento), ou um caminho ainda não identificado. O sintoma continua sem reprodução.

---

## 🧪 Reprodução com Asaas simulado (09/10/2026)

> **Estado:** branch `fix/dem-43-asaas-due-date` criada no `manager-service` a partir da `dev` (`549c4b5`, `v0.3.59-dev.6`). **Nenhum código da aplicação alterado.** Correção proposta, aguardando aprovação. `status` segue `pendente`.

### Método
Teste fora do repositório (não versionado, por decisão do desenvolvedor): Postgres em memória (`pglite`, schema gerado por `drizzle-kit export`) e Asaas simulado por um adaptador do `axios` (clientes, cobranças, assinaturas; a assinatura gera a 1ª cobrança no `nextDueDate` enviado). O teste chama o código real: `executeCreateInstancePayment` e `processWebhookEvent`. Carência = 7 dias, preço = R$ 50 por instância, execução em 09/10/2026.

### Resultado
| Cenário | Cobrança avulsa | Vencimento UzAPI | Assinatura Asaas | Situação |
|---|---|---|---|---|
| A. Trial (5 dias restantes) contrata 1 e paga | 09/10 | 08/11 | 08/11 | correto |
| B. Igual, com `PAYMENT_CONFIRMED` + `PAYMENT_RECEIVED` | 09/10 | 08/11 | 08/11 | correto |
| C. `TRIAL_EXPIRED` contrata 3 e paga | 09/10 | 08/11 | 08/11 | correto |
| G. Trial gera cobrança, ela vence e o cliente paga a mesma | 09/10 | 08/11 | 08/11 | correto |
| F1. Trial (3 dias) gera cobrança, não paga, **contrata de novo** 1 | 09/10 | 04/11 | 04/11 | **errado**: ciclo = fim do trial − carência + 30 |
| F2. Idem, contrata 2 | nenhuma | 05/10 (já vencido) | 09/10 | **errado**: 2 instâncias ativas sem pagamento; datas divergentes |
| F3. Trial (10 dias), contrata de novo 1 | nenhuma | — | — | **errado**: "Nenhuma alteração necessária"; conta fica `OVERDUE`/`CANCELLED` |
| F4. Trial (10 dias), contrata de novo 2 | R$ 30 em 09/10 | 12/10 | 12/10 | **errado**: cobra pro-rata de R$ 30 em vez de R$ 100; ciclo de 3 dias |
| E. Trial com cupom de 100% (recorrente) | nenhuma | fim do trial | 09/10 | **errado**: datas divergentes |

Os cenários F valem tanto para cobrança vencida (`PAYMENT_OVERDUE` → `OVERDUE`) quanto excluída (`PAYMENT_DELETED` → `CANCELLED`).

### Causa
`contract-quote.ts:115` reconhece o cliente de trial só pelo status (`TRIAL`/`TRIAL_EXPIRED`). `create-instance-payment.ts:116` troca o status para `PENDING` ao gerar a cobrança, e o webhook troca para `OVERDUE` (cobrança vencida) ou `CANCELLED` (cobrança excluída). A partir daí `isTrialUser` é falso, `effectivePreviousInstances` vira 1 (a instância do trial) e a nova contratação é tratada como **renovação ou upgrade de cliente pagante**, usando o fim do trial (`expiresIn`) como se fosse um ciclo pago:
- mesma quantidade → `RENEWAL` → `payment-confirmation.ts` chama `extendCycleExpiresIn(expiresIn do trial)` (F1) ou `NONE` (F3);
- quantidade maior → `UPGRADE` pro-rata sobre o "ciclo" do trial (F2, F4); em `isMidCycleChange` o `expiresIn` do trial é mantido e a assinatura sai em `visibleExpiresAt` = fim do trial − carência.

Isso é compatível com o relato do QA ("primeira cobrança com a data atual, assinatura com data derivada dos dias restantes do trial"), que não aparece no caminho direto (A, B, C, G). **Não confirmado** que foi este o caminho usado pelo QA.

### Proposta (aguardando aprovação)
1. Reconhecer a origem de trial sem depender do status: cliente que nunca teve ciclo pago (`firstPaymentDate` nulo e `pricePerInstance` = 0) continua sendo tratado como trial em `PENDING`/`OVERDUE`/`CANCELLED` → contratação `INITIAL`, cobrança cheia, ciclo de 30 dias a partir do pagamento.
2. Caso de custo zero (E): iniciar o ciclo na data da contratação em vez de manter o fim do trial.
3. Itens já listados em 05/10 e ainda abertos: trava contra reprocessamento do mesmo pagamento, datas no fuso de Brasília, script para assinaturas antigas.

---

## 🛠️ Correção aplicada na branch (09/10/2026) — itens 1 e 2

> **Estado:** commit `ea27abc` na branch `fix/dem-43-asaas-due-date` do `manager-service` (base `dev` `549c4b5`). Sem push, sem MR. `status` segue `pendente` até o merge na `dev` e o reteste do QA.

### O que mudou
1. **`src/lib/subscription-status.ts`** — nova função pura `isTrialOrigin(billing)`: verdadeiro para `TRIAL`/`TRIAL_EXPIRED` e também para `PENDING`/`OVERDUE`/`CANCELLED` quando `user_billing.first_payment_date` é nulo e `price_per_instance` = 0 (linha criada pelo trial em `subscription.ts:119`, que nunca teve ciclo pago). `ACTIVE` nunca é origem de trial.
2. **`src/lib/contract-quote.ts`** — `isTrialUser = isTrialOrigin(billingRow)` no lugar da comparação direta de status. Com isso `effectivePreviousInstances` = 0, o contrato sai `INITIAL`, a cobrança é cheia com vencimento hoje e `payment-confirmation.ts` inicia o ciclo em `computeRenewalExpiresIn(now, carência)`; a assinatura no Asaas sai em `visibleExpiresAt` (hoje + 30).
3. **`src/lib/create-instance-payment.ts`** — trial contratando sem custo (cupom de 100%): `expiresIn` passa a ser `computeRenewalExpiresIn(now, carência)` (antes mantinha o fim do trial), `lastContractUpdate` = agora, as instâncias recebem o novo vencimento e a assinatura recorrente sai em hoje + 30 (antes: hoje).
4. **`src/lib/payment-confirmation.ts`** — o trecho que grava `instances.expires_in` e avisa o `api-service` foi extraído, sem mudança de comportamento, para `syncInstancesExpiresIn(userId, expiresIn)`, reutilizado no item 3.

### Validação
| Verificação | Resultado |
|---|---|
| Teste com Asaas simulado + Postgres em memória (8 cenários; 14 combinações) | 8 de 8 aprovados |
| Cenários F1–F4 (cobrança vencida ou excluída, nova contratação de 1 ou 2) | cobrança cheia (R$ 50 / R$ 100) em 09/10; UzAPI 08/11; Asaas 08/11 |
| Cenário E (cupom de 100%) | UzAPI 08/11; Asaas 08/11 |
| Regressão: cliente pagante em `OVERDUE` renovando | continua `RENEWAL`, R$ 100 |
| `pnpm test:unit` e `subscription-status.test.ts` | aprovados |
| `npx tsc --noEmit` e `eslint` nos 4 arquivos | sem erros |

**Não testado:** Asaas real (sem chaves no ambiente de desenvolvimento), interface do painel e sincronização com o `api-service` (`PUBLIC_API_URL` desligada no teste). O simulador aceita assinatura de valor zero; o Asaas real pode recusar (caso do cupom de 100%).

**Não incluído nesta entrega:** trava contra reprocessamento do mesmo pagamento, datas no fuso de Brasília, ajuste de assinaturas antigas. Cliente de trial que paga a cobrança **antiga** depois de gerar uma nova fica ativo sem assinatura recorrente (o contrato pendente mais recente não corresponde ao pagamento) — observado na leitura, não corrigido.

### Roteiro para o QA (ambiente dev, após o merge)
1. Usuário novo em trial → contratar 1 instância (recorrente) → **não pagar**.
2. No Asaas, excluir a cobrança (ou aguardar vencer).
3. Contratar de novo (1 e, em outro usuário, 2 instâncias) → pagar.
4. Conferir: cobrança com o valor cheio e vencimento no dia; vencimento na UzAPI = dia do pagamento + 30; assinatura no Asaas com a mesma data.

## 📂 Arquivos Modificados (09/10/2026)
- `manager-service/src/lib/subscription-status.ts`
- `manager-service/src/lib/contract-quote.ts`
- `manager-service/src/lib/create-instance-payment.ts`
- `manager-service/src/lib/payment-confirmation.ts`


---

## 🔀 Merge na `dev` (confirmado em 10/10/2026)

- Merge `d57ba07` (`Merge branch 'fix/dem-43-asaas-due-date' into 'dev'`, 09/10 18:03) em `origin/dev` do `manager-service`, contendo o commit `ea27abc`. Versão gerada pela pipeline: **`v0.3.59-dev.9`**. Conferido no git local após `git fetch` do desenvolvedor.
- **Pendente:** reteste do QA no ambiente de desenvolvimento (roteiro acima) e, após aprovação, MR para a `main`. `status` segue `pendente`.

---

## ⏸️ Standby — Reteste no ambiente dev bloqueado por configuração do Asaas (14/10/2026)

> **Status:** `standby`, aguardando o programador chefe (Eduardo). Nenhum código alterado. A correção da DEM-43 (`ea27abc`, `manager-service v0.3.59-dev.9`) segue só na `dev`; **não promover para a `main`** antes do reteste aprovado.

### Relato do QA (14/10, ambiente dev implantado, `painel.dev.uzapi.com.br`)
1. Criar conta nova: OK.
2. Contratar instância (recorrente): mensagem vermelha ao gerar a fatura; a página não avançou nem abriu o checkout.
3. Nova tentativa: aviso de pagamento pendente; nenhuma cobrança no Asaas e nenhuma tela de pagamento.

(Um primeiro relato citava "Error 404"; o detalhamento do QA mostrou que o erro foi na fatura, não na criação de instância.)

### Evidência — log do `manager-service` de dev (colado pelo desenvolvedor)
Requisição `POST https://api.asaas.com/v3/payments` (**API de produção**), corpo:
```json
{"customer":"cus_000206731927","billingType":"UNDEFINED","dueDate":"2026-10-14","value":97,
 "description":"Uzapi-API: Contratação de 1 instância(s)",
 "split":[{"walletId":"ac53fecd-…","percentualValue":33}],
 "callback":{"successUrl":"https://painel.dev.uzapi.com.br/payment-success"}}
```
Resposta `400`:
```json
{"errors":[{"code":"invalid_object","description":"É necessário enviar uma URL que use o mesmo domínio cadastrado nas suas Minha Conta na aba Informações."}]}
```

### Causa 1 — falha da fatura (configuração do ambiente, não código da DEM-43)
- `createInvoice` (`src/lib/asaas.ts`) envia `callback.successUrl` montado a partir de `ASAAS_CALLBACK_URL`. No dev o valor aponta para `painel.dev.uzapi.com.br`, domínio diferente do cadastrado na conta Asaas → o Asaas recusa a cobrança inteira.
- **O ambiente dev está configurado com o Asaas de produção:** `buildClient()` (`src/lib/asaas.ts:41`) usa `ASAAS_ENVIRONMENT` (padrão `sandbox`); a requisição foi para `api.asaas.com`, logo no dev a variável está `production`. Consequências: cada teste do QA cria cliente e cobrança **reais**, com split para a carteira real. O cliente `cus_000206731927` (conta de teste do QA) já existe no Asaas de produção.
- **Vazamento de credencial:** a biblioteca `asaas` (`node_modules/asaas/dist/client/Payments.js`, `handleError(error, 'Erro ao criar a cobrança:')`) imprime o erro Axios completo, incluindo o cabeçalho `access_token`. A chave de produção ficou no log do pod de dev (e foi colada na sessão do agente). **Recomendado: gerar nova chave no Asaas e revogar a atual.** A chave não é reproduzida neste documento.

### Causa 2 — conta travada após a falha (bug antigo, fora do escopo da DEM-43)
Em `executeCreateInstancePayment` (`src/lib/create-instance-payment.ts`), a ordem é:
1. `billingWrite` grava `user_billing.subscription_status = 'PENDING'` (`insert … onConflictDoUpdate`), junto com o `contract_history`;
2. só depois chama `createInvoice` no Asaas.

Se o passo 2 lança erro, nada reverte o passo 1: a conta fica `PENDING` sem cobrança, e toda nova tentativa é barrada no início da função por `billingRow?.subscriptionStatus === "PENDING"` → `"Há uma contratação aguardando pagamento…"`. Fica também um registro órfão em `contract_history` sem `asaas_payment_id`. Presente na `main` desde `469f90e` (Eduardo, 07/06/2026); **também ocorre em produção** sempre que o Asaas recusar uma cobrança. Não foi introduzido pela DEM-43.

Correção proposta (demanda nova, a ser gerada pelo Kanban; não implementada): envolver `createInvoice`/`upsertLocalAsaasPayment` em `try/catch` e, na falha, restaurar `subscription_status` e `pending_coupon_code` anteriores (e remover ou marcar o `contract_history` do ciclo) antes de relançar o erro.

### Indício parcial a favor da DEM-43
A cobrança montada para a conta nova em trial saiu com `dueDate` = data do dia (`2026-10-14`) e valor cheio (R$ 97), o comportamento esperado após `ea27abc`. Falta validar a assinatura recorrente no Asaas e o vencimento na UzAPI (passos 3 e 4 do roteiro).

### Outros itens do log (sem relação com a falha)
- `ECONNREFUSED 10.152.183.192:5432` no `seedAutomationConfig` e no `health:ready`: na subida do pod, antes de o banco responder; as requisições seguintes funcionaram.
- `Failed to find Server Action "x"`: navegador com build anterior aberto após deploy; recarregar resolve.

### Decisões pedidas ao Eduardo (mensagem entregue ao desenvolvedor em 14/10)
| Opção | Ação | Prós | Contras |
|---|---|---|---|
| **A (recomendada)** | Dev no sandbox: `ASAAS_ENVIRONMENT=sandbox`, `ASAAS_SANDBOX_TOKEN`, `ASAAS_SPLITS` com carteira do sandbox, domínio do dev cadastrado na conta sandbox | Testes sem cobrança real; isola produção | Configurar conta/carteira sandbox |
| B | Manter produção e cadastrar o domínio do dev | Nenhuma configuração nova | Todo teste gera cobrança real com split; dados de teste no Asaas real |

Além disso: rotacionar a chave de produção; destravar a conta de teste do QA no banco do dev (`user_billing.subscription_status` `PENDING` → status anterior) e excluir no Asaas de produção o cliente `cus_000206731927`, se não for usado; decidir se a Causa 2 vira demanda.

### Para retomar
1. Eduardo confirma a configuração do Asaas no dev (A ou B), a rotação da chave e destrava a conta do QA.
2. QA repete o roteiro com **conta nova**, do zero.
3. Aprovado → promoção pela regra do programador chefe: branch nova da `main` atualizada + cherry-pick de `ea27abc` → MR para `main`; então mover este arquivo de volta a `exec/` com `status: concluido`.

### Retorno do Eduardo (14/10/2026, repassado pelo desenvolvedor)
> "Tem que mudar a URL do asaas, foi uma coisa que passou batido na hora de subir o ambiente de dev."

- Confirma que é configuração do ambiente dev, sem mudança de código. Não ficou explícito se a mudança é só do domínio de callback (`ASAAS_CALLBACK_URL`) ou do ambiente Asaas (`ASAAS_ENVIRONMENT=sandbox` + chave e carteira do sandbox); o recomendado é o sandbox.
- Ainda sem resposta: rotação da chave de produção exposta no log, desbloqueio da conta de teste do QA e se o bug do `PENDING` vira demanda.
- Próximo passo: após o ajuste no dev, QA repete o roteiro com conta nova.

## 🔎 Evidência no log do `manager-service` (16/10/2026, só leitura)
- Trecho de log colado pelo desenvolvedor: em **15/10/2026 19:29:17 (-03:00)** o `manager-service` fez uma chamada HTTP (axios) para **`api.asaas.com`** (host do Asaas de **produção**) e recebeu **`status: 401`** com `data: { errors: [...] }`.
- **Correlação com o reteste:** às 19:40 do mesmo dia o QA reprovou a DEM-43 no dev ("Contratar uma instância no plano recorrente sem efetuar o pagamento: Erro"), e a DEM-82 ficou bloqueada pelo mesmo erro. Se o log é do ambiente dev, confirma o diagnóstico já alinhado com o Eduardo: **o dev aponta para a URL de produção do Asaas com uma chave que não vale lá** (provavelmente a do sandbox) → toda criação de cliente/cobrança falha com 401.
- **Risco de segurança:** o erro do axios é despejado inteiro no log (`console.error(err)`), e o objeto inclui `config.headers` com o **`access_token` do Asaas**. A chave fica gravada no log do pod. Reforça a pendência de **rotacionar a chave** e sugere ajuste no código: logar só `status` e `response.data.errors` (task à parte, se aprovada).
- Nenhum dado sensível foi copiado para este arquivo.
- **Para o Eduardo:** corrigir `ASAAS` URL/chave do dev (sandbox `api-sandbox.asaas.com` + chave do sandbox, ou URL e chave de produção, conforme a decisão); depois o QA retesta a DEM-43 e a DEM-82.
