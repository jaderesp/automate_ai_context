---
id: DEM-80
status: concluido
data_ativacao: 2026-10-16 10:26:26
modulo: Instâncias
data_producao: 2026-10-16
versao_producao: manager-service v0.3.61
versao_worker: v0.0.98
---

# 🚀 Histórico de Execução: Instancia de usuário trial com data de expiração errada.

## 📌 Resumo do Problema
Ao criar um instancia no período trial, a mesma está vindo com a data de expiração igual a data atual. O certo seria data atual + X dias de trial.

## 🛠️ Solução Adotada
**Causa (arquitetura):** a expiração da instância (`instances.expires_in`) é gravada com a data da assinatura, que para o TRIAL já é *cadastro + dias de trial* e **não embute a carência** (a carência, `platform_settings` → `getGracePeriodDays()`, só é somada ao vencimento das assinaturas pagas, em `billing-cycle`). As telas, porém, sempre subtraíam a carência na exibição (`subDays(row.expiresIn, gracePeriodDays)`), então, com carência de 7 dias e trial de 7 dias, a instância aparecia vencendo **no dia do cadastro**.

Duas rotas tinham o defeito:
1. **Admin** (`src/app/api/admin/instances/route.ts`, `admin/billing`): corrigida no commit `b91ea05` (28/09, DEM-36/37), em produção desde o `manager-service v0.3.56`.
2. **Lista de instâncias do próprio usuário** (`GET /api/instances`, `src/app/api/instances/route.ts`): corrigida no commit `13b63c0` (11/10, registrado como DEM-91), entregue no dev em `v0.3.59-dev.12`. A rota passa a ler `user_billing.subscription_status` do usuário (Drizzle: `db.select({ subscriptionStatus: userBilling.subscriptionStatus }).from(userBilling).where(eq(userBilling.userId, session.user.id)).limit(1)`) e só desconta a carência quando `gracePeriodDays > 0` **e** o status não é `TRIAL` (`shouldDiscountGrace`); para TRIAL devolve o `expiresIn` como está gravado.

Nada muda no banco: nenhuma coluna, migração ou FK; só a regra de exibição.

## ✅ Teste do QA
- 15/10 (dev, `0.095-dev06`): "Verificar a data de vencimento do novo usuário: Concluído" → **Aprovado** (planilha e grupo).

## 🚀 Promoção para produção
- Branch `promote/dem-80-90-prod` a partir da `main` `b9d70ba` (`v0.3.60`), junto com a DEM-90: `git cherry-pick -x 13b63c0` → `03ee865` (o merge de 3 vias resolveu sozinho o import; só `userBilling` foi acrescentado, nada da escolha de versão do worker nem do Mobile da `dev`).
- `tsc --noEmit` e `eslint` OK.
- MR !31 mergeado na `main` (pais `b9d70ba` + `03ee865`), tag **`v0.3.61`** (16/10/2026, informado pelo desenvolvedor).

## 📂 Arquivos Modificados
- `manager-service/src/app/api/instances/route.ts` (`03ee865`, produção `v0.3.61`)
- `manager-service/src/app/api/admin/instances/route.ts` e rotas de billing do admin (`b91ea05`, produção `v0.3.56`)


### 📣 WhatsApp: aviso de produção enviada ao grupo (16/10/2026 10:28)
```
🚀 *Task #80 em produção*
📌 Instancia de usuário trial com data de expiração errada.
📦 Versão: manager-service v0.3.61
Já disponível para os clientes.
```
