---
id: DEM-67
status: concluido
data_ativacao: 2026-09-15 14:41:48
data_reabertura: 2026-10-07 15:00:00
data_conclusao: 2026-10-08 09:30:00
modulo: Contratar Instâncias
data_producao: 2026-10-07
versao_producao: api-service v1.57.6
versao_worker: v0.0.98
---

# 🚀 Histórico de Execução: Instancia expirando mesmo com assiantura ativa

## 📌 Resumo do Problema
Pegamos um caso aqui, onde o cliente estava com a instancia expirada, mesmo com a assinatura ativa. Acredito que se tratava de uma instancia criad ano período de trial e após a assiantura, a plataforma não renovou a data de expiração da instancia.
(Observações: Parece que o problema é resolvido quando o usuário clicar manualmnete na opção ATUALIZAR INSTANCIA. o Adequado seria a data de expiração da instancia atualizar automaticamente assim que o cliente migra do TRIAL para PAGANTE)

## 🛠️ Solução Adotada
1. Sincronização de Renovação de Assinatura:
Adicionamos o acionamento direto ao `api-service` (função `callInstanceMicroservice`) através da camada financeira `applyPaymentConfirmation` do `manager-service`. Sempre que o Asaas confirma um pagamento, o financeiro atualiza as datas de expiração no banco de dados da plataforma e, logo em seguida, realiza um "Ping de Atualização" invisível no `api-service`. Este ping limpa o cache de bloqueio da memória do Node.js, forçando o microserviço a reconhecer imediatamente que o período do cliente foi prorrogado.

2. Bugfix de Contratos Órfãos:
Foi descoberto que contratos pendentes antigos (ex: abandonos de upgrade no checkout) eram resgatados acidentalmente no evento de Webhook de renovações mensais. Isto fazia o sistema tratar uma renovação normal como um "Upgrade de Ciclo", impedindo que a data de `expiresIn` fosse estendida. Adicionamos validação rigorosa comparando `asaasPaymentId` e `subscriptionId` para isolar e ignorar upgrades não finalizados durante o ciclo.

## 📂 Arquivos Modificados
- `manager-service/src/lib/payment-confirmation.ts`
- `manager-service/src/lib/webhook.ts`

## 🧪 Teste Prático e Homologação
Para fins de auditoria e prevenção de regressão, foi executado um script automatizado (`test-webhook-logic.ts`) diretamente no ambiente simulando os efeitos colaterais no banco de dados.

**Metodologia do Teste:**
1. Injeção de uma instância ativa no banco com data de vencimento "hoje".
2. Injeção de um histórico de contrato (tipo `UPGRADE`) abandonado para o mesmo usuário (simulando a armadilha).
3. Disparo simulado da função `processWebhookEvent` com payload de evento `PAYMENT_CONFIRMED` (assinatura recorrente Asaas).
4. Verificação final se a trava da armadilha foi evitada e se a instância avançou o mês.

**Resultado do Log (Sucesso):**
```text
Iniciando teste de comprovação com usuário: test-user-webhook-1789499430539
Simulando webhook PAYMENT_CONFIRMED (Renovação)
-----------------------------------------
Data antiga de expiração: 2026-09-15T19:10:30.656Z
Nova data de expiração da instância: 2026-10-22T19:10:30.749Z
✅ SUCESSO! A instância foi renovada corretamente e escapou da armadilha do UPGRADE abandonado!
-----------------------------------------
Teste finalizado e dados limpos.
```
O script também testou e homologou que o evento aciona o `callInstanceMicroservice` silenciosamente (usando um bloco `try/catch`) para atualizar a memória do Kubernetes, garantindo que mesmo se a rede falhar, a baixa financeira é concretizada no banco.

---

## ⏸️ Standby / Aguardando Decisão (02/10/2026)
Relatado que instâncias estavam expirando mesmo com assinatura ativa após migração do Trial. A auditoria confirmou que o script `payment-confirmation.ts` hoje atualiza o `expiresIn` de TODAS as instâncias do usuário de forma agnóstica à flag `isActive`, sendo capaz de ressuscitar instâncias pausadas. O webhook de renovação também já foi corrigido anteriormente para não esbarrar em faturas órfãs.
Movida para **Standby** pois é um Falso Positivo (o código atual em Produção já cobre este cenário).

---

## 🔎 Atualização 06/10/2026: auditoria de release e novo cenário relatado

> **Status:** segue em **standby**. O texto da devolução descreve um cenário diferente do corrigido; **precisa de análise própria**.

| Evento | Data |
|---|---|
| Commit da correção (`01c3748`) | 15/09 16:05 |
| Merge na `main` (`150a5c4`) | 22/09 09:46 |
| Primeira release com a correção (`v0.3.51`) | 24/09 16:10 |

Entre 15/09 e 24/09 a produção rodou sem a correção.

### Texto da devolução (CSV)
> *"MESMO COM A VENCIMENTO DA INSTANCIA ATUALIZADO, O SISTEMA CONTINUA PUXANDO A O VENCIMENTO ANTIGO ANTES DA ATUALIZAÇÃO EM NOVAS INSTANCIAS. CASO O CLIENTE TENHA DUAS INSTANCIA É NECESSARIO ATUALIZAR NOVAMENTE PARA QUE AMBAS TENHA A MESMA DATA DE VENCIMENTO […] EX: EXPIRAÇÃO: 15/12/2040 / EXPIRAÇÃO: 19/09/2026"*

### Leitura inicial (não aprofundada, não reproduzida)
- A correção original tratou a renovação após o pagamento (`applyPaymentConfirmation` atualiza `instances.expiresIn` e chama `callInstanceMicroservice("update")`).
- O relato fala de vencimentos diferentes entre instâncias do mesmo cliente após um ajuste de vencimento. A rota do admin `src/app/api/admin/users/[userId]/billing/route.ts` atualiza `instances.expiresIn` de todas as instâncias no banco (linhas 287–290), mas **não chama a API** para sincronizar, ao contrário do fluxo de pagamento. Isso vale para `v0.3.50`, `v0.3.51` e `v0.3.57`.
- Instâncias novas herdam `billing.expiresIn` na criação (`api-service`: `instances.service.ts:122` e `k8s.service.ts:136`).
- Falta verificar: de onde a instância nova lê o vencimento quando sai diferente (cache do `api-service`, `ensureUserBilling`), e qual tela o QA usou para "atualizar".

---

## 🔁 Reaberta para Desenvolvimento (07/10/2026)

> Movida de `standby.solution/` para `exec/` com `status: pendente`: no backlog (CSV exportado em 07/10/2026 14:48) a demanda continua **Devolvido** (Urgente, **Cliente**, módulo Contratar Instâncias) — pela regra de prioridades é a faixa **P1**.

- **Texto da devolução no CSV:** sem alteração em relação a 06/10 (transcrito na seção acima): instâncias novas "puxam" o vencimento antigo; com duas instâncias é preciso atualizar de novo para ficarem com a mesma data (exemplo: 15/12/2040 × 19/09/2026).
- **Observação original do CSV:** o problema some quando o usuário clica em "Atualizar Instância"; o esperado é a data atualizar sozinha quando o cliente passa de trial para pagante.
- **Situação técnica:** a da seção "Atualização 06/10/2026" acima — a correção original (renovação após pagamento) foi liberada em 24/09; o cenário relatado é outro e **ainda não foi analisado a fundo**.
- **Próximo passo:** análise do caminho de criação de instância nova e do ajuste de vencimento pelo admin (sincronização com a API e cache), com proposta de solução para aprovação.

---

## 🔬 Análise do cenário da devolução (07/10/2026)

> **Estado:** análise concluída por leitura de código e por consulta de leitura na cópia local do banco (dados até 10/09). **Nenhum código alterado; proposta aguardando aprovação.** Não reproduzido em ambiente com o `api-service` real.

### Onde a data de expiração de uma instância nova é definida
`api-service/src/kubernets/k8s.service.ts` (`createInstance`, linha 136):
```ts
expiresIn: billing?.expiresIn ?? new Date(),
```
O `billing` vem de `SubscriptionService.assertCanCreateInstance(username)` (`src/database/subscription.service.ts`). Para contas com papel **admin** existe um atalho (commit `e35af64`, 01/07/2026):
```ts
if (this.isPlatformAdmin(userRecord)) {
  return { user: userRecord, billing: {} as UserBilling };
}
```
Com `billing` vazio, `billing?.expiresIn` é `undefined` e a instância nasce com `expiresIn = new Date()`, ou seja, **vence no dia em que foi criada**, qualquer que seja o vencimento da assinatura. Em `InstanceService.create` (`src/database/instances.service.ts:122`) o valor já chega preenchido, então a leitura do billing ali não é usada.

### Por que as instâncias do mesmo usuário ficam com datas diferentes
- O ajuste de vencimento pelo admin (`manager-service`, `src/app/api/admin/users/[userId]/billing/route.ts`, linhas 287–290) grava o novo `expiresIn` em **todas as instâncias existentes** naquele momento.
- Uma instância criada **depois** por uma conta admin volta a nascer com a data do dia.
- Resultado: uma instância com a data ajustada e outra com a data da criação, até um novo ajuste — exatamente o relato ("é necessário atualizar novamente para que ambas tenham a mesma data"; exemplo 15/12/2040 × 19/09/2026).

### Efeito
`InstanceService.validateInstance` (`instances.service.ts:495`) bloqueia as chamadas da API quando `instance.expiresIn` já passou, sem exceção para admin: a instância criada por conta admin deixa de funcionar a partir do dia seguinte ("A instância expirou em …"), mesmo com a assinatura válida.

### Evidência na cópia local do banco
| Papel do dono | Instâncias | Com expiração = dia da criação |
|---|---|---|
| `user` | 319 | 1 |
| `admin` | 5 | 3 |

Exemplos de contas admin: instâncias criadas em 14/08, 08/09 e 10/09 com `expiresIn` no mesmo dia, enquanto o `user_billing` do dono vence em 2099. As duas instâncias admin restantes têm a data igual à do billing (compatível com um ajuste de vencimento posterior à criação).

### O que não está confirmado
- Se a conta usada pelo QA no teste tem papel admin (provável, pelo vencimento em 2040 definido manualmente, mas não verificado).
- Para contas comuns (`role: user`), a instância nova herda `billing.expiresIn` e o pagamento confirmado atualiza todas as instâncias (correção `01c3748`); não encontrei caminho de divergência para esse caso. O caso isolado de conta comum na tabela acima não foi investigado.

### Proposta de correção (aguardando aprovação)
**Opção A (recomendada) — corrigir na origem, no `api-service`:**
1. `subscription.service.ts`: no atalho de admin, continuar sem aplicar bloqueios, mas devolver o registro real de `user_billing` quando existir.
2. `k8s.service.ts` (`createInstance`): usar `billing.expiresIn` quando houver; para admin sem billing, gravar `expiresIn` nulo (sem vencimento) em vez de `new Date()`. `validateInstance` já ignora a checagem quando `expiresIn` é nulo.
3. Teste unitário do cálculo da data da instância nova.

**Opção B — só não bloquear:** em `validateInstance`, ignorar o vencimento para instâncias de contas admin. Resolve o bloqueio, mas as datas continuam diferentes na tela.

**Dados existentes:** as instâncias de admin já gravadas com a data errada se corrigem com um ajuste de vencimento pelo admin (que atualiza todas) ou com um `UPDATE` pontual.

**Arquivos previstos (Opção A):** `api-service/src/database/subscription.service.ts`, `api-service/src/kubernets/k8s.service.ts` e um arquivo de teste. Branch `fix/dem-67-admin-instance-expiration` a partir da `main` do `api-service`.

---

## 🛠️ Correção aplicada — Opção A (07/10/2026)

> **Estado:** commitado localmente no `api-service`, branch `fix/dem-67-admin-instance-expiration`, commit `0d5c661` (`fix(dem-67): instância criada por conta admin herda o vencimento da assinatura`), a partir da `main` `eab3243` (`v1.57.5`). **Sem push, sem MR, sem release.** O `status` segue `pendente` até a liberação e o reteste do QA.

### Alterações
1. **`src/database/subscription.service.ts`** (`assertCanCreateInstance`): o atalho de conta admin deixa de devolver `billing: {}`. Continua sem aplicar as travas de assinatura (status, limite de instâncias), mas lê e devolve o registro real de `user_billing` do admin quando existe.
2. **`src/helpers/instanceExpiration.ts`** (novo): `resolveNewInstanceExpiresIn(billingExpiresIn, isAdmin, now)` — devolve o vencimento da assinatura quando existe; para admin sem assinatura devolve `null` (sem vencimento); para os demais mantém a data atual, como antes.
3. **`src/kubernets/k8s.service.ts`** (`createInstance`, antiga linha 136): `expiresIn` passa a vir de `resolveNewInstanceExpiresIn(billing?.expiresIn, role === 'admin')` em vez de `billing?.expiresIn ?? new Date()`.
4. **`src/database/instances.service.ts`** (`create`): o `expiresIn` informado é respeitado mesmo quando é `null`; só cai em `billing?.expiresIn ?? new Date()` quando vem `undefined`. Antes, o `??` trocava o `null` pela data atual.

`validateInstance` não mudou: já ignora a checagem de vencimento quando `instances.expiresIn` é nulo. A coluna `instances."expiresIn"` é anulável (o `DEFAULT now()` só vale quando o campo é omitido).

### 🧪 Teste Prático e Homologação
- `prettier --check`, `eslint` (0 erros, 0 avisos) e `tsc --noEmit` OK; o hook de pré-commit (lint do projeto) passou.
- O `api-service` não tem framework de testes (só `ts-node`); a lógica foi conferida com um script descartável executado via `ts-node` e removido em seguida:
  - casos puros de `resolveNewInstanceExpiresIn`: admin com assinatura → data da assinatura; admin sem assinatura ou com billing sem data → `null`; usuário com assinatura → data da assinatura; usuário sem data → data atual (comportamento anterior). 5/5 OK.
  - `assertCanCreateInstance` real contra o Postgres local (somente leitura) para as 6 contas admin da cópia local: 5 com assinatura (vencimentos 2099/2100) → a instância nova herdaria exatamente essa data; 1 sem assinatura → sem vencimento. 6/6 OK. Antes da correção, todas resultariam na data do dia.
- `api-service` local iniciado com o código da branch: sobe sem erros e `GET /v1/health` responde 200.
- **Não testado:** criação real de instância (`POST /v1/instance/add`), porque depende do cluster Kubernetes, indisponível no ambiente local; e o comportamento da tela do painel para instância sem vencimento (o `manager-service` já trata `expiresIn` nulo em `src/app/api/instances/route.ts:58`, mas a exibição não foi conferida).

### Observações para a liberação
- **Instâncias de admin já gravadas com a data errada não são corrigidas por este commit.** Um ajuste de vencimento pelo painel (que grava em todas as instâncias do usuário) ou um `UPDATE` pontual resolve.
- A correção vale para contas com papel **admin**. Se a conta usada pelo QA no teste não for admin, a devolução tem outra origem e a análise precisa continuar.
- Após o merge: `pnpm release` no `api-service` (próxima versão `1.57.6`); a pipeline da tag atualiza o deploy.

### 📂 Arquivos Modificados
- `api-service/src/database/subscription.service.ts`
- `api-service/src/kubernets/k8s.service.ts`
- `api-service/src/database/instances.service.ts`
- `api-service/src/helpers/instanceExpiration.ts` (novo)

---

## 🚀 Merge e release (07/10/2026)

- MR `fix/dem-67-admin-instance-expiration` → `main` mergeado no GitLab (`85f43f5`).
- Release **`api-service v1.57.6`** criada pelo desenvolvedor: commit `6931e5e` (`chore(release): 1.57.6`) e tag `v1.57.6`, sobre a `main` com o merge; conferido no git local (`main` local = `origin/main`).
- Ocorrência na primeira tentativa: a release foi executada na branch da correção, com a `main` local desatualizada; o push foi recusado (`non-fast-forward`) e nada chegou ao remoto. A tag e o commit locais foram desfeitos (`git tag -d v1.57.6`, `git reset --hard 0d5c661`) e a release refeita na `main` após `git pull`.
- **Pendente:** pipeline da tag e atualização do deploy (`infra-gitops` → `api-service:v1.57.6`) — não verificados daqui; confirmar com o QA se a conta do teste é admin e pedir reteste; ajustar o vencimento das instâncias de admin já gravadas com a data antiga. O `status` segue `pendente` até o reteste.

---

## ✅ Encerramento do desenvolvimento (08/10/2026)

- `status` alterado para `concluido` a pedido do desenvolvedor: a correção (Opção A) está na `main` do `api-service` e na release `v1.57.6`.
- **Backlog (CSV exportado em 08/10 09:08):** a demanda ainda consta **Devolvido**; o texto da devolução (instâncias com 15/12/2040 × 19/09/2026) é o cenário tratado na seção "Análise do cenário da devolução (07/10/2026)". Não há reteste do QA registrado após a `v1.57.6`.
- **Não verificado:** pipeline da tag `v1.57.6` e imagem em execução no cluster. A cópia local do `infra-gitops` está em `ff901dc` (01/10) e mostra `api-service:v1.57.4`; está desatualizada (não traz nem a `v1.57.5`), portanto não serve de prova.
- **Não testado:** criação real de instância por conta admin (sem cluster local) e exibição do vencimento nulo no painel.
- **Se o reteste falhar:** confirmar primeiro se a conta do teste tem papel `admin` e se a instância foi criada depois do deploy da `v1.57.6`; instâncias de admin criadas antes continuam com a data antiga até um novo ajuste de vencimento.
- **Itens relacionados no backlog (A Fazer):** 80 e 82 — vencimento igual à data atual para instância/assinatura de trial; mesma área de código (`createInstance` / `ensureUserBilling`).

---

## 🔬 Análise da observação do QA (15/10/2026, só leitura; aguardando reteste)
Observação no backlog: *"resolvido quando o usuário clica manualmente em ATUALIZAR INSTÂNCIA; o adequado seria atualizar automaticamente na migração TRIAL → PAGANTE"*.
- **Pagamento confirmado** (`manager-service` `src/lib/payment-confirmation.ts:139-145`): `isFromTrialOrInitial` → novo ciclo; `syncInstancesExpiresIn` grava `instances.expiresIn` de todas as instâncias e chama `callInstanceMicroservice("update")`. Presente na `main` desde `469f90e` (06/2026) e na `dev` (extraído em `ea27abc`).
- **Ajuste manual do admin** (`src/app/api/admin/users/[userId]/billing/route.ts:287`): grava `instances.expiresIn` no banco, sem chamar o `api-service`.
- **"Atualizar Instância"** (`api-service` `k8s.service.ts` `updateInstance` → `instances.service.ts` `update`): não altera `expiresIn` (só recria o deployment e grava nome/webhook/versão). Logo, o clique não é o que corrige a data.
- **Validação** (`api-service` `instances.service.ts` `validateInstance`): lê `instances.expiresIn` do banco a cada chamada.
- **Dev:** fluxo de pagamento real indisponível (Asaas do dev aponta para produção, ver DEM-43); teste provavelmente pelo ajuste manual do admin.
- **Propostas (não executadas):** A) pedir ao QA o fluxo usado (pagamento × ajuste admin), usuário/ambiente, prints antes/depois e estado da instância; B) no ajuste do admin usar `syncInstancesExpiresIn` (branch `fix/dem-67-admin-billing-sync-instances` a partir da `dev`). Desenvolvedor informou que a task já está em reteste: aguardar o QA.

---

## 🔁 Reclassificação (15/10/2026)
`status: concluido` → `em_teste` pela regra nova de etapas (`AGENTS.md`, seção 3: `concluido` só após aprovação do QA, promoção para a `main` e release): devolvida pelo QA e em reteste.

## 🚀 Promoção para produção / Encerramento (16/10/2026)
- A correção (Opção A, commit `0d5c661` → MR `85f43f5` na `main` do `api-service`) já estava em produção desde a release **`api-service v1.57.6`** (07/10, commit `6931e5e`, tag `v1.57.6`); não houve promoção nova.
- QA retestou em 15/10 (dev): alterar o vencimento da instância, criar instância nova e conferir que o vencimento da nova acompanha o da atualizada → **Aprovado** (planilha `Devolvido` → `Aprovado`, 15/10 22:43; resumo no grupo).
- `status: concluido` com `versao_producao: api-service v1.57.6`, autorizado pelo desenvolvedor em 16/10.
- Fora deste encerramento: a observação do QA de 15/10 (expiração da instância atualizar sozinha na migração de TRIAL para pagante, sem clicar em "Atualizar Instância") segue registrada na análise acima; se for desejada, vira task própria.


### 📣 WhatsApp: aviso de produção enviada ao grupo (16/10/2026 10:30)
```
🚀 *Task #67 em produção*
📌 Instancia expirando mesmo com assiantura ativa
📦 Versão: api-service v1.57.6
Já disponível para os clientes.
```
