---
id: DEM-48
status: em_teste
data_ativacao: 2026-09-10 19:55:27
modulo: Instâncias
---

# 🚀 Histórico de Execução: Botão Criar Instancia Ativo para Assinaturas Vencidas

## 📌 Resumo do Problema
O botão "Nova Instância" continua clicável e ativo mesmo quando a assinatura do usuário expirou (data atual ultrapassou o `expiresIn`), pois o status no banco de dados (`subscriptionStatus`) pode demorar para ser atualizado (via webhook ou cron) para `OVERDUE` ou `TRIAL_EXPIRED`. Enquanto o status permanecer como `ACTIVE` ou `TRIAL`, o backend permite a criação.

## 🛠️ Solução Adotada
O método `getSubscriptionDetails` em `manager-service/src/lib/subscription.ts` foi refatorado. 
A lógica de validação de `isBlocked` passou a incorporar a propriedade dinâmica `cycle.daysRemaining`. Agora, mesmo que o banco de dados ainda reflita estaticamente os status `ACTIVE` ou `TRIAL`, a validação forçará um bloqueio em tempo real caso `daysRemaining <= 0`, prevenindo que a ausência de conciliação imediata com o gateway financeiro permita criações indevidas.

## 📂 Arquivos Modificados
- `manager-service/src/lib/subscription.ts`

---

## 🔁 Reclassificação (15/10/2026)
`status: concluido` → `em_teste` pela regra nova de etapas (`AGENTS.md`, seção 3: `concluido` só após aprovação do QA, promoção para a `main` e release): correção na `main` (merge `aedd4ac`), mas a planilha está `A Fazer`: falta o teste do QA.
