# 🤖 Diário de Bordo e Handover (Agente IA)

> ⚠️ **REGRA DE TOLERÂNCIA ZERO:** Nenhum agente deve modificar arquivos, fazer commits ou limpar código sem permissão explícita prévia. Todo o trabalho deve ser precedido de uma proposta técnica e pausa para aprovação do desenvolvedor.
# 🤖 Diário de Bordo e Handover (Agente IA)

Este documento serve como o ponto de partida (memória) para a IA assim que iniciar uma nova sessão de trabalho. Ele contém o estado atual, o histórico recente e as pendências imediatas.

---

## 📌 Status Atual do Sistema (Snapshot)
- **Painel Kanban Local (`ai.context/demandas`)**: 100% estabilizado. Agora renderiza arquivos Markdown completos no Modal e possui integração via rota `/api/nova-demanda` para salvar direto no CSV.
- **Worker Go (`worker-go`)**: Rotas de Mídias estabilizadas (Upload/Retrieve isolados em PTT iOS sem conflitos na tabela de mensagens). Novo interceptador adicionado no `factory.go` garantindo que mensagens de *outgoing* sejam refletidas instantaneamente no SQLite local.
- **API Service (`api-service`)**: Bug ESM com `@kubernetes/client-node` resolvido. Gerador de Hash para mensagens (`messageId`) refatorado seguindo as novas restrições de segurança da Meta (SHA-256 com telefone do remetente).

---

## 🚀 O que foi feito nas Últimas Sessões

### Sessão: 11/09/2026 (Hoje)
*ID da Sessão:* `agy --conversation=3ef7433b-d165-4c31-9f41-8206ab38a804`
- **DEM-64 (Playback iOS)**: Concluída. Corrigido encode do `ffmpeg` para arquivos PTT inserindo as flags `-ac 1 -ar 16000` (Mono, 16kHz). Push feito com sucesso para o GitLab.
- **DEM-45 (Retrieve 410 Áudios)**: Concluída.
- **DEM-66 (Falha no Revoke de Mensagens)**: Concluída em sua totalidade (Causa 1 e Causa 2).
  - *Causa 1:* WhatsApp Web agora exige que o ID customizado gerado seja um SHA-256 contendo o timestamp e o `phoneNumber` do remetente, do contrário ele sobrescreve com 32 caracteres. `api-service` foi atualizada para gerar o ID perfeito.
  - *Causa 2:* O Worker-Go não salvava as mensagens disparadas por ele próprio no banco SQLite local. Como a ação de Revoke do frontend exige apenas o `messageId`, o Worker não encontrava a mensagem no SQLite e falhava silenciosamente ao tentar recuperar o JID de destino. `worker-go/factory.go` foi refatorado para salvar automaticamente todas as mensagens disparadas com metadados sintéticos. O teste prático E2E homologou a solução com êxito no smartphone.

---

## Pendências e Próximos Passos
- **Push Manager-Service:** Rodar `git push` nas branches `fix/demanda-1-delete-user` e `fix/dem-48-block-expired` do `manager-service`.
- **Push Worker-Go:** Rodar `git push` no repositório `worker-go` nas branches de correção (inclui a DEM-45 e o `factory.go` da DEM-66).
- **Push API-Service:** O usuário precisará realizar o push local das correções ESM e DEM-66.


## Sessão DEM-67 (2026-09-15)
- **ID da Sessão:** `agy --conversation=3ef7433b-d165-4c31-9f41-8206ab38a804`
- **Demandas Analisadas:** DEM-67 (Instância expirando mesmo com assinatura ativa)
- **Status:** Concluído.
- **Resumo Técnico:**
  - Corrigido o bug onde o Webhook do Asaas resgatava contratos de Upgrade órfãos (checkout abandonado) durante renovações recorrentes, impedindo que a data de vencimento (\`expiresIn\`) avançasse 30 dias.
  - Implementada sincronização com a API (via \`callInstanceMicroservice\`) direto no \`applyPaymentConfirmation\`. Assim que a fatura (ou transição de TRIAL para PAGANTE) é compensada, o manager aciona a API e limpa o cache de bloqueio da instância automaticamente (que antes requeria clique manual no botão Atualizar).
- **Pendências:** O desenvolvedor precisa confirmar os commits para `manager-service` (que farei a seguir).
- **Melhorias de Ferramentas (UX Kanban):** Adicionada funcionalidade de "Snapshot" em HTML (via html2canvas) e injeção automática de descrições detalhadas dentro dos arquivos markdown gerados através do `painel_local.py`.

## Sessão DEM-65 (2026-09-16)
- **ID da Sessão:** `agy --conversation=3ef7433b-d165-4c31-9f41-8206ab38a804`
- **Demandas Analisadas:** DEM-65 (Notificações Trial enviadas mesmo desativadas) + Erro Schema Better-Auth
- **Status:** Concluído.
- **Resumo Técnico:**
  - Corrigido o erro de compilação de banco local inserindo a nova coluna `impersonatedBy` no schema do Drizzle para suportar atualizações do `better-auth`.
  - Descoberto que a ação de "Desativar" no UI mudou a flag `isActive` da tabela `notificationTemplates`, mas o Cronjob (`executeAutomation`) ignorava essa flag na hora de recuperar o texto.
  - Implementada a trava `!template.isActive` em `executeAutomation`, `executeAutomationForUser` e `sendCampaign`.
- **Pendências:** O desenvolvedor precisa confirmar o git commit no `manager-service`.

## Sessão DEM-43 (2026-09-16)
- **ID da Sessão:** `agy --conversation=3ef7433b-d165-4c31-9f41-8206ab38a804`
- **Demandas Analisadas:** DEM-43 (Vencimento divergente Asaas x Uzapi)
- **Status:** Concluído.
- **Resumo Técnico:**
  - A criação de assinaturas recorrentes no `create-instance-payment.ts` estava enviando um `nextDueDate` hardcoded de `Date.now() + 3 dias` (para novos clientes) e `billingRow.expiresIn` puro para renovações (o que incluía os dias de tolerância).
  - Corrigido para: Se cliente novo = `new Date()` (Hoje). Se recorrente = `subDays(expiresIn, gracePeriodDays)`.
  - Isso garante que a data de vencimento no Asaas seja perfeitamente idêntica à data oficial do plano na UzAPI, separando de vez a responsabilidade dos "Dias de Corte" exclusivamente para as rotinas do Cronjob.
- **Pendências:** O desenvolvedor precisa confirmar o git commit no `manager-service`.
- **Nota Adicional DEM-43:** O código foi refinado após alinhamento com o cliente para utilizar o motor interno \`billing-cycle.ts\` e sua propriedade \`visibleExpiresAt\`. Isso cobriu um caso oculto onde clientes "Trial" poderiam ser cobrados em datas no passado caso a carência fosse apenas subtraída cruamente do banco. Testes isolados com 4 cenários garantiram a perfeição da lógica, que agora espelha perfeitamente as regras de Trial, Renovações e Inadimplentes. Os dados de teste foram adicionados à DEM-43.md.
- **Nota Final DEM-43 (Regras Contratuais):** Confirmado com o cliente que o \`billing-cycle\` e o \`payment-confirmation.ts\` já estão cobrindo os cenários de pagamento atrasado de forma inteligente. Pagamentos na carência (antes do corte) preservam o dia do vencimento. Pagamentos pós-corte (instância derrubada) resetam a assinatura para o dia atual do pagamento. A DEM-43 está rigorosamente detalhada e fechada.
- **Validação TypeScript/Linter:** O compilador estrito (`npx tsc`) foi rodado no projeto para certificar as alterações. Além da lógica do `billing-cycle` passar ilesa, 2 erros residuais de tipagem (`null assignable`) no `webhook.ts` foram mapeados e limpos no mesmo commit.
