---
id: DEM-65
status: concluido
data_ativacao: 2026-09-15 19:18:48
modulo: Notificações
---

# 🚀 Histórico de Execução: Notificações são enviadas mesmo desativadas

## 📌 Resumo do Problema
Desativamos as notificações Trial Expirando (D-3) e mesmo assim ela continuam sendo enviadas às 06:05AM

## 🛠️ Solução Adotada
**Diagnóstico:** Foi identificado que a funcionalidade "Desativar" utilizada em 26/08 desativou o *Template* no banco de dados (`notificationTemplates.isActive = false`), mas a automação do Cronjob (`executeAutomation`) e os gatilhos (`sendCampaign`) não verificavam o estado do template antes de disparar, apenas a configuração global da automação. Com isso, ao bater 06:05 AM (09:05 UTC), o cronjob resgatava o template do banco e efetuava o disparo indevidamente.

**Correção:** Foram adicionadas travas de segurança explícitas (`if (!template || !template.isActive) return;`) no motor principal (`manager-service/src/lib/notifications.ts`). Agora, o sistema bloqueia os disparos na raiz se o template estiver inativo, estancando o vazamento das mensagens.


## 📂 Arquivos Modificados
- `manager-service/src/lib/notifications.ts`

## 🧪 Teste Prático e Homologação
Para fins de auditoria, foi executado o script automatizado `test-dem65.ts` simulando as exatas condições do erro:

**Metodologia do Teste:**
1. A configuração da automação global foi forçada para ATIVA (simulando o estado antes da correção onde o cron disparava).
2. O template da mensagem foi mantido como INATIVO (simulando a ação do painel em 26/08).
3. O cronjob foi invocado manualmente pela rotina.

**Resultado do Log (Sucesso):**
```text
--- INICIANDO TESTE E HOMOLOGAÇÃO DA DEM-65 ---
✔️ Passo 1: Automação 'Trial Expirando' simulada como ATIVA no banco.
✔️ Passo 2: O Cron Job de 06:05AM acordou e chamou executeAutomation...
🔒 TESTE: Template inativo detectado! Abortando disparo da automação.
--- TESTE FINALIZADO ---
```
A rotina foi corretamente abortada, comprovando o funcionamento da trava. O log de teste foi então removido do código final.
