---
id: DEM-43
status: concluido
data_ativacao: 2026-09-16 11:00:13
modulo: Contratar Instâncias
---

# 🚀 Histórico de Execução: Divergência entre data de vencimento das assianturas no Asaas e na Uzapi

## 📌 Resumo do Problema
Quando o usuário contrata instancia pela primeira vez é criado uma assiantura no Assas com a Data Atual + Dias de Cortes.Isso faz com que a data de vencimento na Uzapi fique divergente, pois nela é salvo apenas a data atual, em que o usuário fez a assiantura.

OBS: A DATA DE CORTE NÃO DEVE SER USADA NO CÁLCULO DE DATA DE VENCIMENTO. BASICAMNETE, ELA TEM QUE ATUAR COMO UM CRON QUE IRÁ SE BASEAR NA DATA DE VENCIMENTO DA ASSIANTURA DO CLIENTE (QUE INCLUSIVE TEM QUE SER IDÊNTICAS ENTRE O ASAAS E A UZAPI). OU SEJA, QUANDO CHEGAR NA DATA DE VENCIMENTO, O CLIENTE JÁ É ALERTADO SOBRE A RENOVAÇÃO. MAS QUANDO CHEGAR X DIAS DEPOIS DO VENCIMENTO DELE, A ASSIANTURA É PAUSADA. ESSE BUG TEM RELAÇÃO COM O BUG DE ID 16

## 🛠️ Solução Adotada
**Diagnóstico:** A lógica de criação de assinaturas recorrentes no Asaas estava dessincronizada com o fluxo da UzAPI. Novos clientes tinham o vencimento empurrado 3 dias artificiais à frente. Além disso, a arquitetura da UzAPI já embutia os "dias de carência" no `expiresIn` bruto do banco de dados, o que fazia as renovações da fatura caírem exatamente no dia do bloqueio, gerando faturas defasadas e atrasadas em relação ao ciclo visível.

**Correção Implementada (Arquitetura Inteligente):** 
O arquivo `manager-service/src/lib/create-instance-payment.ts` foi reestruturado para integrar-se ao motor do `billing-cycle`. 
Em vez de subtrair dias manualmente, utilizamos a propriedade `cycle.visibleExpiresAt` que já calcula nativamente a diferença entre Trial, Vencidos e Ativos.
A regra para o Asaas ficou:
- Se a **Data Visível** do cliente (ex: Fim do Trial ou próxima Mensalidade real) for no futuro, a cobrança no Asaas é agendada perfeitamente para essa data (sem carência embutida).
- Caso o usuário não tenha plano ou já esteja vencido/inadimplente, a primeira mensalidade será cobrada Hoje (`new Date()`).

### 🧪 Teste Prático e Homologação
Simulação de isolamento efetuada via script local (removido após os testes) avaliando os 4 cenários vitais para `gracePeriodDays: 7`:
1. **Cliente Novo (Checkout Inicial):** Retornou `Hoje`. Correto (Asaas cobra a primeira fatura e ativa os 30 dias).
2. **Cliente em Trial (Assinando Cartão):** Retornou exatamente a `Data do fim do Trial`. Correto (Trial não sofre interferência da carência).
3. **Cliente Pagante Renovando:** Retornou a `Data exata do Vencimento (-7 dias da data do bloqueio)`. Correto!
4. **Cliente Inadimplente (Trocando cartão hoje):** Retornou `Hoje`. Correto (Tira o cliente da inadimplência imediatamente).

### 🛡️ Validação de Integridade e Tipagem (TypeScript/Linter)
Além dos testes matemáticos, o código foi submetido à compilação estrita do projeto (`npx tsc --noEmit`).
- A nova arquitetura do `billing-cycle` passou sem nenhum erro de tipagem.
- Foram identificados e corrigidos 2 pequenos erros residuais de tipagem (`Type null is not assignable`) no `webhook.ts` e `payment-confirmation.ts` (herdados de intervenções anteriores).
- O Linter (`eslint --fix`) foi aplicado garantindo que as modificações respeitam os padrões de qualidade do repositório.

## 📂 Arquivos Modificados
- `manager-service/src/lib/create-instance-payment.ts`


### 📌 Homologação de Regra de Negócio (Alinhamento Cliente)
O motor matemático final satisfaz integralmente as duas regras contratuais validadas com a diretoria:
- **Cenário 1 (Pagamento dentro da carência):** Se o vencimento é dia 16 (corte 23) e o cliente paga dia 20, o sistema usa \`extendCycleExpiresIn()\`. Como a API não foi interrompida, o calendário é preservado e o vencimento do mês seguinte continua sendo dia 16.
- **Cenário 2 (Regularização pós-corte):** Se o cliente é cortado dia 23 e paga apenas dia 28, o sistema usa \`computeRenewalExpiresIn()\`. O calendário antigo é resetado e a nova assinatura no Asaas/UzAPI fixa o vencimento para todo dia 28, garantindo que o cliente não pague pelos dias em que a API esteve desligada.
