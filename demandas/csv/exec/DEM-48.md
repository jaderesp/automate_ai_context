---
id: DEM-48
status: pendente
data_ativacao: 2026-09-10 19:55:27
modulo: Instâncias
---

# 🚀 Histórico de Execução: Botão Criar Instancia Ativo para Assinaturas Vencidas

## 📌 Resumo do Problema
O botão "Nova Instância" continua clicável e ativo mesmo quando a assinatura do usuário expirou (data atual ultrapassou o `expiresIn`), pois o status no banco de dados (`subscriptionStatus`) pode demorar para ser atualizado (via webhook ou cron) para `OVERDUE` ou `TRIAL_EXPIRED`. Enquanto o status permanecer como `ACTIVE` ou `TRIAL`, o backend permite a criação.

## 🛠️ Solução Adotada
(IA preencherá este campo após autorização)

## 📂 Arquivos Modificados
- (A preencher)
