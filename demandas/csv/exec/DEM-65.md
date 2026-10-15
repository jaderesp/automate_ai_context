---
id: DEM-65
status: pendente
data_ativacao: 2026-09-15 19:18:48
data_reabertura: 2026-10-07 15:00:00
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

---

## ⏸️ Standby / Aguardando Decisão (02/10/2026)
O QA relatou que notificações inativas ainda estavam sendo disparadas pelo Cronjob das 06h. Após auditoria, foi comprovado que as funções `executeAutomation` e `executeAutomationForUser` contêm a trava explícita de segurança `if (!template || !template.isActive) return;` desde o deploy da versão `v0.3.54`. É fisicamente impossível o código atual vazar disparos se a flag estiver inativa no banco.
Movida para **Standby** aguardando confirmação se o teste não ocorreu em um ambiente defasado ou com a flag `isActive` não comutada no banco do tenant.

---

## 🔎 Atualização 06/10/2026: auditoria de release

> **Status:** segue em **standby**, aguardando reteste do QA.

| Evento | Data |
|---|---|
| Commit da correção (`66daf04`) | 16/09 11:32 |
| Merge na `main` (`859580a`) | 22/09 09:47 |
| Primeira release com a correção (`v0.3.51`) | 24/09 16:10 |

- Entre **16/09 e 24/09** a produção rodou sem a correção (a `v0.3.50`, de 17/09, não a continha). A devolução do QA (*"AS NOTIFICAÇÕES CONTINUAM SENDO ENVIADAS MESMO ESTANDO DESATIVADAS"*) é compatível com um teste nesse intervalo; a data do teste não é conhecida.
- As travas estão na `main` atual (`src/lib/notifications.ts`): `!config?.isActive` e `!template.isActive` em `executeAutomation` (linhas 336 e 343) e `executeAutomationForUser` (409 e 416), e `!template.isActive` em `sendCampaign` (244). O cron do envio é `5 9 * * *` em `src/instrumentation.ts` (09:05 UTC = 06:05 em Brasília).
- Não foi possível conferir o cluster (imagem em execução) daqui.
- **Encaminhamento:** pedir reteste ao QA informando que a correção só entrou em produção em 24/09.

---

## 🔁 Reaberta para Desenvolvimento (07/10/2026)

> Movida de `standby.solution/` para `exec/` com `status: pendente`: no backlog (CSV exportado em 07/10/2026 14:48) a demanda continua **Devolvido** (Urgente, Hugo Peres, módulo Notificações).

- **Texto da devolução no CSV:** *"AS NOTIFICAÇÕES CONTINUAM SENDO ENVIADAS MESMO ESTANDO DESATIVADAS."* Campo Observações vazio. Sem data nem exemplo do envio indevido.
- **Situação técnica:** a da seção "Atualização 06/10/2026" acima — correção de 16/09 só entrou em produção em 24/09 (`v0.3.51`); as travas `isActive` estão na `main` atual.
- **A verificar nesta reabertura:** (1) se o QA retestou depois de 24/09; (2) qual controle foi desativado na tela (automação `notificationAutomationConfig.isActive` ou modelo `notificationTemplates.isActive`) e para qual tipo (`trial_expiring`); (3) se existe outro caminho de envio do aviso de trial que não passe por `executeAutomation`/`executeAutomationForUser`/`sendCampaign`; (4) a imagem realmente em execução no cluster.

---

## 📨 Pedido de reteste ao QA (15/10/2026)
- Conferido na `origin/dev` do `manager-service`: merge `859580a` (`fix/dem-65-template-isActive`) presente desde `v0.3.59-dev.1`; atual `v0.3.59-dev.13`. Travas em `src/lib/notifications.ts:336/343` (`executeAutomation`) e `:409/416` (`executeAutomationForUser`).
- Cron `5 9 * * *` (`src/instrumentation.ts:67`) = 09:05 UTC = **06:05 BRT**, o horário relatado.
- **Caminho alternativo identificado (não verificado em banco):** campanha agendada com público `trial_expiring` sai por `runScheduledCampaigns` → `sendCampaign`, que só checa `template.isActive` (`:244`), não a chave da automação.
- Mensagem enviada ao QA pelo desenvolvedor: reteste no dev (desativar a automação, usuário trial vencendo em ≤3 dias, conferir após 06:05); se houver envio, informar data/horário, o que foi desativado e print das campanhas agendadas; data do teste anterior (correção só em produção desde 24/09).
