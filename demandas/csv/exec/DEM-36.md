---
id: DEM-36
status: concluido
data_ativacao: 2026-09-24 09:31:40
modulo: Assinaturas
---

# 🚀 Histórico de Execução: Assinantes indevidamente com status Trial

## 📌 Resumo do Problema
Mesmo após a data de vencimento, alguns assinantes continuam com a assinatura no status Trial.

OBS: "Pelo que notei, o backend está restringindo o uso da instância. Porém seria interessante que esse tratamento também tivesse a nível de frontend, onde as instâncias ficassem com o status Pausada e sem permitir uma nova autenticação, o usuário não conseguiria criar novas instâncias, e o status da assinatura fosse para TRIAL-EXPIRADO."

## 🛠️ Solução Adotada (Fase 1 — implementada em 23/09/2026)

### Causa raiz
1. **Sem rotina agendada:** a transição `TRIAL → TRIAL_EXPIRED` era 100% *lazy* (`manager-service/src/lib/subscription.ts:144-158`), só executando quando o usuário acessava rotas que passam por `getSubscriptionDetails`. Sem acesso, o status ficava preso em `TRIAL` no banco (listagens admin leem o valor bruto).
2. **Datas divergentes no admin:** rotas admin subtraíam `gracePeriodDays` mesmo em TRIAL, mas trial não embute grace (`billing-cycle.ts:58-61`) → admin via "vencido" até 7 dias antes da hora.
3. **Bloqueio de criação incompleto:** o fix da DEM-48 (`daysRemaining <= 0`) nunca havia sido mergeado (branch `fix/dem-48-block-expired`).
4. **Sem bloqueio de reautenticação:** rotas `restart/resume/update` estavam nas listas de exclusão dos interceptors do api-service; "Pausada" só nascia de timeout de autenticação.

### Alterações (manager-service — branch `fix/dem-36-37-subscription-status`, baseada na DEM-48)
- **`src/lib/subscription-status.ts` (novo):** regra pura `getExpiredTransition(status, visibleExpiresAt, now)` → `TRIAL → TRIAL_EXPIRED` e `ACTIVE → OVERDUE`; demais status inalterados.
- **`src/lib/subscription.ts`:** transição lazy agora cobre também `ACTIVE` vencido (`OVERDUE`), usando `billing-cycle` (grace-aware); `canCreateInstance` passou a retornar `isBlocked`/`blockReason`.
- **`src/lib/subscription-expiration.ts` (novo) + `src/instrumentation.ts`:** **cron de hora em hora** (`0 * * * *`) conciliando em lote:
  - `TRIAL` com `expiresIn < now` → `TRIAL_EXPIRED`;
  - `ACTIVE` com `expiresIn < now + grace` (vencimento visível) → `OVERDUE`.
- **Admin (`admin/billing`, `admin/instances`, GET `users/[userId]/billing`):** não desconto de grace quando `TRIAL` (datas visíveis coerentes com o dashboard).
- **Frontend:**
  - `instances/page.tsx` + `actions-menu.tsx`: "Autenticar", "Reiniciar" e "Atualizar" desabilitados para assinatura bloqueada (com tooltip do motivo); `openAuth` bloqueado com toast.
  - `status-badge.tsx`: instância exibida como **"Pausada"** quando a assinatura está bloqueada.
  - `subscription-status-banner.tsx`: novo banner "Assinatura vencida" para `ACTIVE` com `daysRemaining <= 0`.
  - `contract-instances/page.tsx`: aviso de assinatura bloqueada (`isBlocked`/`blockReason`).

### Alterações (api-service — branch `fix/dem-36-37-subscription-status`)
- **`database/instances.service.ts`:**
  - `validateUser` passou a usar `billing.expiresIn` (vencimento oficial com tolerância) em vez de `lastContractUpdate + 30`, com bloqueio explícito de `CANCELLED`;
  - **corrigido bug da data congelada no boot** (`private currentDate` removido; `new Date()` por chamada em `validateUser`/`validateInstance`).
- **`database/subscription.service.ts`:** transição lazy de `ACTIVE → OVERDUE` com grace (paridade com o manager) em `ensureUserBilling`.
- **Interceptors (`username`/`instance`):** `restart`, `resume` e `update` saíram das listas de exclusão → agora validam billing; `logout`/`delete` permanecem liberados (cliente pode desconectar/excluir).

### Fase 2 (não implementada)
Pausa real do deployment por vencimento (acionar `pauseInstance` do api-service + `resume` automático ao regularizar) — a ser avaliada após homologação da Fase 1.

## 🧪 Testes e Validação
- **Unitários (manager):** novo `src/lib/subscription-status.test.ts` (7 subtestes: TRIAL/ACTIVE vencidos, dentro do prazo, status sem transição, borda do instante exato, sem data). `npm run test:unit` → **15/15 PASS** (aumentei o glob do script para incluir todos os `src/lib/*.test.ts`).
- **TypeScript/lint:** `npx tsc --noEmit` exit 0 e `npm run lint` exit 0 (manager); `npm run build` exit 0 e `npm run lint` exit 0 (api-service).
- **Homologação E2E:** ⏳ pendente (cenários: trial vencido, trial estendido, ACTIVE vencido — conferir status, botões, criação e reautenticação).

## 📂 Arquivos Modificados
**manager-service** (commit `b91ea05`, branch `fix/dem-36-37-subscription-status`, baseada na `fix/dem-48-block-expired`):
- `src/lib/subscription-status.ts` (novo), `src/lib/subscription-status.test.ts` (novo), `src/lib/subscription-expiration.ts` (novo)
- `src/lib/subscription.ts`, `src/instrumentation.ts`, `package.json`
- `src/app/api/admin/billing/route.ts`, `src/app/api/admin/instances/route.ts`, `src/app/api/admin/users/[userId]/billing/route.ts`
- `src/app/api/instances/check-limit/route.ts`
- `src/app/instances/page.tsx`, `src/app/instances/components/actions-menu.tsx`, `src/app/instances/components/status-badge.tsx`
- `src/components/layout/subscription-status-banner.tsx`, `src/app/contract-instances/page.tsx`

**api-service** (commit `905b706`, branch `fix/dem-36-37-subscription-status`):
- `src/database/instances.service.ts`, `src/database/subscription.service.ts`
- `src/common/interceptors/username.interceptor.ts`, `src/common/interceptors/instance.interceptor.ts`

### Dependências
- **DEM-48** (bloqueio de criação com `daysRemaining <= 0`): MR aberto — base da branch do manager. Mergear antes/junto.
- Release do manager-service (ex.: `v0.3.55`) levará DEM-48 + DEM-36/37.

### Teste Prático e Homologação
Aprovado visualmente pelo usuário no ambiente de produção. Status atualizado para Aprovado via planilha CSV (10/09/2026).
