---
id: DEM-91
status: pendente
data_ativacao: 2026-10-10 10:32:59
modulo: API
---

# 🚀 Histórico de Execução: Instancia expirando dentro do período de trial

## 📌 Resumo do Problema
Mesmo com dias restantes de trial, clientes estão recebendo erro de token expirado ao realiza chamadas à API

Referente ao ticket: https://painel.uzapi.com.br/admin/support/f9ea1970-a3f1-45d7-bc4c-ef7461c65b2e

## 🛠️ Solução Adotada

> **Estado (10/10/2026):** análise por leitura de código. **Causa não identificada; nenhum código alterado.** Faltam dados do ticket. Prioridade P1 (Cliente + Urgente).

### Onde o bloqueio nasce (`api-service`, `main` `6931e5e` / `v1.57.6`)
- `src/database/instances.service.ts` `validateInstance` (linhas 499–511): se `instances.expiresIn` passou do fim do dia → `401 A instância '<id>' expirou em dd/MM/yyyy. Por favor, renove sua instância.` Resultado positivo fica em cache por 1 h (`instance.interceptor.ts:105`).
- `validateUser` (linhas 432–455): bloqueia `NONE`, `CANCELLED` e `user_billing.expires_in` vencido → `403`.
- O token JWT da instância **não** expira (`token.guard.ts:82`, `ignoreExpiration: true`); "token expirado" no relato deve ser uma das mensagens acima.

### De onde vem o vencimento no trial
- `user_billing.expires_in` = `user.createdAt` + `trialDays` (`api-service` `subscription.service.ts:53` e `manager-service` `subscription.ts:115`). O trial conta a partir do **cadastro**, não da criação da instância.
- A instância nova herda esse valor (`k8s.service.ts:137`, `resolveNewInstanceExpiresIn`). Sem `expires_in` na assinatura e sem ser admin, a instância nasce vencendo **no próprio dia**.

### Hipóteses (nenhuma confirmada)
1. Instância criada quando a linha de `user_billing` não tinha `expires_in` → vence no dia da criação.
2. Cliente em trial que gerou cobrança e ela foi excluída no Asaas: status `CANCELLED` → `validateUser` bloqueia mesmo com dias de trial (mesma família da DEM-43; a mensagem seria "assinatura cancelada", não "expirou").
3. Divergência entre a data exibida e a gravada: `manager-service` `src/app/api/instances/route.ts:59` e a lista de assinaturas do admin subtraem a carência também de quem está em trial (itens 59, 80 e 82 do backlog). Isso explica data **exibida** menor, não bloqueio.
4. A versão `v1.57.6` do `api-service` (DEM-67) pode não estar em produção — não verificado.

### Atualização 10/10/2026 — retorno do QA
> "Aconteceu isoladamente com 2 clientes: a instância estava expirada, porém o trial estava dentro do prazo."

**Defeito confirmado por leitura (exibição):** `manager-service/src/app/api/instances/route.ts:59` devolve `expiresIn = subDays(row.expiresIn, gracePeriodDays)` para **todas** as instâncias do usuário. O vencimento do trial não embute carência (`billing-cycle.ts:58`: `isTrial ? rawExpiresAt : rawExpiresAt − carência`), então a instância de um cliente em trial aparece com a expiração adiantada em `gracePeriodDays` dias — com trial de 7 dias e carência de 7, aparece vencendo no dia do cadastro, enquanto o cartão da assinatura mostra o trial dentro do prazo. A rota do admin (`src/app/api/admin/instances/route.ts:42`) já tem essa exceção (`subscriptionStatus !== "TRIAL"`); a do usuário não. É o mesmo sintoma do item 80 do backlog.

**Ainda não explicado:** o bloqueio real na API (erro retornado ao cliente). No banco, a instância criada no trial herda a mesma data da assinatura; pelo código não encontrei caminho que grave uma data menor na instância durante o trial. Sem os dados dos 2 clientes não é possível confirmar se houve bloqueio real ou apenas a data exibida.

**Proposta parcial (aguardando aprovação):** aplicar na rota do usuário a mesma exceção de trial da rota do admin (1 arquivo no `manager-service`).

### Para avançar
Texto exato do erro retornado, `username` e `phone_number_id` do ticket, e autorização para consulta **somente leitura** em `user_billing` e `instances` desse usuário.

### Correção de exibição aplicada (11/10/2026) — autorizada pelo desenvolvedor, commit `13b63c0`
Repositório `manager-service`, branch `fix/dem-91-trial-instance-expires` criada a partir da `origin/dev` (`d57ba07`).

`src/app/api/instances/route.ts` (`GET`): passou a consultar `user_billing.subscription_status` do usuário da sessão e só desconta `gracePeriodDays` de `instances.expires_in` quando o status **não** é `TRIAL` — mesma regra de `src/app/api/admin/instances/route.ts` e de `getBillingCycleContextSync`. Antes, `subDays(row.expiresIn, gracePeriodDays)` era aplicado a toda instância, e a de um cliente em trial aparecia vencendo `grace` dias antes do fim real do trial.

Validação: `pnpm exec tsc --noEmit` e `eslint --max-warnings=0` no arquivo, sem erros. Não validado no painel.

Roteiro para o QA (dev): criar conta nova (trial), criar a instância e conferir que a data de expiração da instância na lista é igual à do cartão da assinatura.

**Limites:** isto corrige só a data exibida. O bloqueio real na API relatado no ticket continua sem causa identificada; depende do `username` dos 2 clientes, do texto exato do erro e de consulta somente de leitura autorizada. A demanda segue `pendente`. Status `TRIAL_EXPIRED` mantém o desconto de carência (paridade com as outras telas; itens 59/82 do backlog).

## 📂 Arquivos Modificados
- `manager-service/src/app/api/instances/route.ts`

### Merge na `dev` (11/10/2026)
MR mergeado na `dev`, conforme informado pelo desenvolvedor (não conferido por fetch). Aguardando reteste do QA no ambiente dev.
