---
id: DEM-47
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

---

## 🔢 Correção de numeração (15/10/2026)
Este arquivo se chamava `DEM-48.md` (`id: DEM-48`), mas o conteúdo corresponde à **DEM-47** da planilha ("Botão Criar Instancia Ativo para Assinaturas Vencidas", Hugo Peres, Alta, `A Fazer`). A DEM-48 da planilha é outra task ("Checkout abrindo em uma nova aba", Normal, `A Fazer`), ainda não trabalhada. Renomeado para `DEM-47.md` com autorização do desenvolvedor. Os registros antigos (branch `fix/dem-48-block-expired`, merge `aedd4ac` em 28/09, release `manager-service v0.3.55`, e as entradas "DEM-48" do `HANDOVER.md` de 23/09) referem-se a esta task. Situação: correção em produção desde `v0.3.55`; falta o teste do QA (por isso `em_teste`).

## 📋 Backlog (planilha, 15/10/2026, autorizado)
Linha 48: Status `A Fazer` → `Concluído`, Versão `0.095` → `0.097` (worker de produção; correção já em produção), Observações (havia "Nenhuma", mantido) + resumo e roteiro de teste.
