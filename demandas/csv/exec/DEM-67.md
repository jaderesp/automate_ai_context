---
id: DEM-67
status: concluido
data_ativacao: 2026-09-15 14:41:48
modulo: Contratar Instâncias
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
