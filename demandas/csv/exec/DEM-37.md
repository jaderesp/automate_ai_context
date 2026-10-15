---
id: DEM-37
status: concluido
data_ativacao: 2026-09-24 09:31:55
modulo: Assinaturas
---

# 🚀 Histórico de Execução: Assinantes indevidamente com status Ativo

## 📌 Resumo do Problema
Nos casos em que estendemos o prazo Trial do Usuário, faz com que ele fique com o status da assinatura igual Ativo mesmo passando da data de vencimento.

OBS: "Pelo que notei, o backend está restringindo o uso da instância. Porém seria interessante que esse tratamento também tivesse a nível de frontend, onde as instâncias ficassem com o status Pausada e sem permitir uma nova autenticação, o usuário não conseguiria criar novas instâncias, e o status da assinatura fosse para VENCIDO."

## 🛠️ Solução Adotada (Fase 1 — implementada em 23/09/2026)

### Causa raiz
1. **A extensão de prazo pelo admin gravava `ACTIVE`:** a única ação administrativa ("Ativar / Ajustar Manualmente") convertia qualquer status para `ACTIVE` (`admin/users/[userId]/billing/route.ts:228,248`), mesmo quando a intenção era apenas prolongar teste/cortesia.
2. **Não existia transição `ACTIVE → vencido` por tempo:** `OVERDUE` só nascia do webhook `PAYMENT_OVERDUE` do Asaas (`webhook.ts:340`). Ativações manuais não têm assinatura no Asaas → o status ficava `ACTIVE` indefinidamente após o vencimento.
3. **Backend bloqueava de forma inconsistente:** `validateUser` usava `lastContractUpdate + 30` (ignorando `expiresIn`/status) e a data de referência ficava **congelada no boot do pod** (`instances.service.ts:30`), liberando/bloqueando na hora errada.
4. **Sem bloqueio de reautenticação/restart/resume** por billing (rotas excluídas dos interceptors).

### Alterações (manager-service — branch `fix/dem-36-37-subscription-status`)
- **Ação "Estender Teste" (`mode: "extend_trial"`) em `admin/users/[userId]/billing/route.ts`:** preserva/define `TRIAL` e atualiza apenas `expiresIn` (sem somar grace, pois trial não embute tolerância); auditoria `admin_trial|email|justificativa` em `contract_history` (`type: ADMIN_OVERRIDE`). O modo padrão `activate` mantém o comportamento anterior.
- **Transição lazy + cron** (`src/lib/subscription.ts`, `src/lib/subscription-expiration.ts`, `src/instrumentation.ts`): `ACTIVE` vencido (vencimento visível = `expiresIn - grace`) → **`OVERDUE`** (exibido como "Vencido" no admin e "Em atraso" no dashboard) e `TRIAL` vencido → `TRIAL_EXPIRED`. Cron de hora em hora + checagem nas telas.
- **Admin:** datas visíveis coerentes (sem desconto de grace em TRIAL) em `admin/billing`, `admin/instances` e GET da billing do usuário.
- **Frontend:** instância exibida como **"Pausada"** quando bloqueada; "Autenticar"/"Reiniciar"/"Atualizar" desabilitados; banner "Assinatura vencida" (ACTIVE com 0 dias); aviso em Contratar Instâncias.

### Alterações (api-service — branch `fix/dem-36-37-subscription-status`)
- **`database/instances.service.ts`:** `validateUser` usa `billing.expiresIn` (vencimento oficial) + bloqueia `CANCELLED`; **removida a data congelada** (`currentDate`) — `new Date()` a cada chamada em `validateUser`/`validateInstance`.
- **`database/subscription.service.ts`:** `ensureUserBilling` faz a transição lazy `ACTIVE → OVERDUE` com grace (paridade com o manager), garantindo bloqueio de criação/uso coerente.
- **Interceptors:** `restart`, `resume` e `update` agora são validados por billing (saíram das listas de exclusão); `logout`/`delete` seguem liberados.

### Fase 2 (não implementada)
Pausa real do deployment por vencimento + `resume` automático ao regularizar (a Fase 1 entrega o comportamento visual "Pausada" e os bloqueios).

## 🧪 Testes e Validação
- **Unitários (manager):** `src/lib/subscription-status.test.ts` (7 subtestes) — `npm run test:unit` → **15/15 PASS**.
- **TypeScript/lint:** manager `tsc` 0 / `lint` 0; api-service `build` 0 / `lint` 0.
- **Homologação E2E:** ⏳ pendente (cenário-chave: admin usa "Estender Teste" → status permanece TRIAL; ao vencer, vira TRIAL_EXPIRED automaticamente; ACTIVE vencido vira OVERDUE e bloqueia).

## 📂 Arquivos Modificados
**manager-service** (commit `b91ea05`, branch `fix/dem-36-37-subscription-status`):
- `src/app/api/admin/users/[userId]/billing/route.ts` (modo estender teste + datas TRIAL), `src/app/api/admin/billing/route.ts`, `src/app/api/admin/instances/route.ts`
- `src/lib/subscription-status.ts` (novo), `src/lib/subscription-status.test.ts` (novo), `src/lib/subscription-expiration.ts` (novo), `src/lib/subscription.ts`, `src/instrumentation.ts`
- `src/app/instances/page.tsx`, `src/app/instances/components/actions-menu.tsx`, `src/app/instances/components/status-badge.tsx`, `src/app/api/instances/check-limit/route.ts`
- `src/components/layout/subscription-status-banner.tsx`, `src/app/contract-instances/page.tsx`, `package.json`

**api-service** (commit `905b706`, branch `fix/dem-36-37-subscription-status`):
- `src/database/instances.service.ts`, `src/database/subscription.service.ts`, `src/common/interceptors/username.interceptor.ts`, `src/common/interceptors/instance.interceptor.ts`

### Dependências
- **DEM-48** (MR aberto) é a base do bloqueio de criação; a branch do manager parte dela.
- Release do manager-service (ex.: `v0.3.55`) levará DEM-48 + DEM-36/37.

### Teste Prático e Homologação
Aprovado visualmente pelo usuário no ambiente de produção. Status atualizado para Aprovado via planilha CSV (10/09/2026).
