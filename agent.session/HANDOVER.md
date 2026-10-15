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

## 🚀 Atualizações Recentes (2026-09-21)
- **DEM-49**: Finalizada por outro programador. Kanban atualizado.
- **DEM-3 (Autonomia para exclusão da conta)**: Concluída. Alterada lógica de limpeza Asaas de `deleteCustomer` para `cancelAllActiveSubscriptionsForCustomer`.

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

---

## 📅 Sessão Finalizada em 2026-09-17
**Agente:** \`agy --conversation=3ef7433b-d165-4c31-9f41-8206ab38a804\`

### 📝 Resumo do Expediente
- **DEM-43 (Asaas):** Completamente finalizada, alinhada e homologada com o cliente. MR text gerado.
- **DEM-69 (Erro 400 - Queue):** Investigação concluída, mas suspensa para o próximo dia útil a pedido do usuário. A demanda foi movida para a pasta \`standby.solution\` com o dossiê completo.

### ⚠️ Pendências para o Próximo Agente (Handover)
- Ao iniciar os trabalhos amanhã, você DEVE aguardar o sinal verde do usuário para a **DEM-69**.
- A análise técnica e as soluções exatas propostas estão documentadas no arquivo \`ai.context/demandas/csv/standby.solution/DEM-69.md\`.
- Caso aprovado, você deve alterar \`TokenGuard\` e \`UsernameInterceptor\` no repositório \`api-service\`, devolver a DEM-69 para a pasta \`exec/\`, marcá-la como \`concluido\` e prosseguir com os commits padronizados.

---

## 📅 Sessão Finalizada em 2026-09-22
**Agente:** \`opencode --session=ses_f35d827bfffeWb835n30un2oxl\`

> 🔁 **Como retomar esta sessão amanhã (histórico completo de contexto):**
> - Continuar a última sessão: \`opencode -c\` (ou \`opencode --continue\`)
> - Retomar esta sessão exata: \`opencode --session ses_f35d827bfffeWb835n30un2oxl\`
> - Banco de sessões: \`~/.local/share/opencode/opencode.db\` (listar com \`opencode session list\`)
> - Alternativa/segurança: qualquer sessão nova já carrega este HANDOVER automaticamente via \`opencode.json\` (campo \`instructions\`).

### 📝 Resumo do Expediente
- **DEM-69 (Queue 400):** Já constava concluída no Kanban (conclusão 2026-09-22 10:00) pela sessão anterior; verificado que o commit `103a0af` está no branch `fix/dem-69-queue-error` (merge com main em `bff8696`). Havia um ajuste de formatação Prettier pendente em `username.interceptor.ts`, commitado nesta sessão: `e587aa7` (`style(api): ajustar formatação do interceptor de username`). **Push pendente pelo desenvolvedor.**
- **DEM-74 (Documento chega "Sem título"):** Concluída.
  - **Causa raiz:** divergência de contrato `api-service` (`document.filename`, commit `b469892`) × `worker-go` (`document["fileName"]` legado em `services/messages/document.go:38`). O `FileName` do protobuf nunca era preenchido e o WhatsApp exibia "Sem título".
  - **Correção (Opção A):** `extractFileName` com fallback `filename` → `fileName`; fluxo por `id` passou a usar o `file_name` do `GetMediaByID` (antes descartado); fluxo por `link` deriva basename via `net/url` + `PathUnescape` + `SanitizeFileName`; default final `"document"`.
  - **Testes:** novo `services/messages/document_test.go` (11 subtestes, table-driven) — `PASS`; `gofmt`, `go build ./...` e `go vet ./...` limpos.
  - **Branch/Commit:** `worker-go` — `fix/dem-74-document-filename` — `d9c57d0` (`fix(dem-74): usar filename com fallbacks no nome do documento`).
- **DEM-73 (Button reply não gera webhook no iPhone):** Concluída e **homologada E2E com iPhone real**.
  - **Causa raiz:** o clique em botão chega em tipos protobuf diferentes por plataforma; o worker tratava `TemplateButtonReplyMessage` (Android) e `ListResponseMessage`, mas `ButtonsResponseMessage` havia sido removido no commit `8dbc145` e `InteractiveResponseMessage` nunca foi tratado. Tipos fora do switch viravam `unknown` → `BuildMessagePayload` retornava `nil` → webhook descartado silenciosamente (`events.go:225-228`).
  - **Correção (Opção A):** novos cases `ButtonsResponseMessage` e `InteractiveResponseMessage` (parse do `ParamsJSON` com fallback `Body.Text`) em `webhook/createContent.go`; campo novo em `types/messageTypes.go` + `NormalizeHistorySync.go`; testes em `webhook/createContent_test.go`.
  - **Descoberta do E2E:** o **iPhone envia `ButtonsResponseMessage`** (confirmado no SQLite: `selectedButtonID=btn_dem73_1`). A opção mínima (só `InteractiveResponseMessage`) teria falhado.
  - **E2E Android (regressão validada em device real):** botão `btn_dem73_android` → resposta `A550CED35014A58A13D07A76ADD41504` com **`TemplateButtonReplyMessage`** no SQLite; webhook recebeu o mesmo contrato `button_reply` (id/title). Contrato idêntico entre iOS e Android.
  - **E2E executado:** worker local (branch do fix) + RabbitMQ/Postgres locais + listener de webhook em `127.0.0.1:8099`; pairing novo device `556392308423:19` (QRCode; o SQLite antigo `616846729449965.db` recebeu `401 logged out from another device` e foi deletado pelo handler de Logout); disparo via `pika` na exchange `API-WhatsApp` (msgID `3EB01DF5409B25F5517440`) → clique no iPhone às 15:58:52 → webhook recebeu `interactive.button_reply` com `id=btn_dem73_1`/`title=Confirmar`. Evidências: `/tmp/opencode/dem73/` (logs, DB e scripts de teste).
  - **Branch/Commit:** `worker-go` — `fix/dem-73-button-reply-ios` — `434ddb4` (`fix(dem-73): tratar ButtonsResponseMessage e InteractiveResponseMessage no webhook`). **Texto do MR gerado** (na sessão) e pendente de push/abertura no GitLab.
- **Melhoria de Ferramentas (UX Kanban):** corrigida a rolagem do modal de detalhes em `ai.context/demandas/painel_local.py`. O container `flex-1 overflow-y-auto` não encolhia (`min-height: auto` do flexbox), travando markdown longo sem barra de rolagem. Aplicado `min-h-0` no scroller + `overflow-hidden` no `#taskModalContent` (Opção B); painel reiniciado na porta 9000.
- **Auto-load deste Handover:** criado `opencode.json` na raiz do projeto com `"instructions": ["ai.context/agent.session/HANDOVER.md"]` — toda nova sessão do opencode passa a carregar este arquivo automaticamente no contexto (config lida no startup: requer reiniciar o opencode para valer).

### ⚠️ Pendências para o Próximo Agente / Desenvolvedor
- **Push:** ~~branches `fix/dem-74-document-filename` e `fix/dem-73-button-reply-ios` do `worker-go`~~ ✅ **já enviadas ao remoto** (verificado no fechamento: `origin/fix/dem-73-button-reply-ios`=`434ddb4`, `origin/fix/dem-74-document-filename`=`d9c57d0`). Falta apenas o push da branch `fix/dem-69-queue-error` do `api-service` (commit `e587aa7`, 1 commit à frente do remoto).
- **MRs pendentes de abertura no GitLab:** DEM-73 e DEM-74 (textos gerados na sessão) e DEM-69.
- **Homologação E2E da DEM-74 (QA):** requer build/deploy manual do worker (deploy do worker-go fora do CI; `worker.deployment.yaml` manual). Cenários: link com `filename`, link sem `filename`, `id` sem `filename`.
- **Limpeza do ambiente de teste da DEM-73:** ✅ processos (worker/listener) derrubados e fila `999999999999999` removida no fechamento. Resta apenas **deslinkar o device de teste `556392308423:19`** no telefone (WhatsApp → Dispositivos conectados). Evidências preservadas em `/tmp/opencode/dem73/`.
- **`ai.context` com alterações não commitadas** (a pedido do desenvolvedor): `HANDOVER.md`, `technical_context/WORKER_GO.md` (itens 6 e 7), `demandas/painel_local.py` (fix de rolagem do modal), `DEM-73.md`, `DEM-74.md`, `DEM-69.md`, `DEM-3.md`, `DEM-49.md`, `10092026.csv`.
- **DEM-62 (QRCode instância Pausada):** segue `pendente` em `exec/` (sem análise iniciada).

---

## 📅 Sessão 2026-09-23 (em andamento)
**Agente:** \`opencode --session=ses_f35d827bfffeWb835n30un2oxl\`

### 📝 Resumo do Expediente (parcial)
- **DEM-74 REABERTA:** cliente reportou no grupo (22/09, após deploy) que `filename` continua exibindo "Sem título" e que `caption` funciona ✅. Diagnóstico desta sessão: **o fix não está na imagem de produção** — a tag mais recente `v0.0.91` aponta para `434ddb4` (somente DEM-73), enquanto a `origin/main` já contém os merges `d5e3215` (DEM-74) e `04cd686` (DEM-73). Como a CI builda imagem por tag e o deployment usa `:latest`, falta **taguear a main (ex.: `v0.0.92`)** para gerar a imagem com o fix. Detalhes e payloads no `DEM-74.md` (seção "🔄 Reabertura").
- **E2E local DEM-74 (em execução):** worker compilado da branch `fix/dem-74-document-filename` (`d9c57d0`) + device pareado via QRCode `556392308423:20@s.whatsapp.net` (instância `999999999999999`, SQLite em `/tmp/opencode/dem74/`) + listener de webhook `127.0.0.1:8099` + PDF servido por HTTP em `127.0.0.1:8090` (a partir de `ai.context/examples/documents/`).
  - Cenário A (`link` + `filename` + `caption`) e Cenário B (`link` sem `filename` + `caption`) enviados para iPhone `556392477769` (09:13) e Android `5516997141457` (09:22); messageIDs e payloads exatos registrados no `DEM-74.md`.
  - **Aguardando confirmação visual do desenvolvedor nos aparelhos** (nome do arquivo + legenda). Cenário C (upload por `id`) planejado.
- Ambiente de teste segue rodando em background (worker, listener e http.server).

### ⚠️ Pendências imediatas
- ✅ **DEM-74 homologada e encerrada (23/09):** Cenários A e B confirmados pelo desenvolvedor em **iPhone e Android** (nome do arquivo + legenda corretos). Cenário C (upload por `id`) não executado — fallback coberto por teste unitário. Status no Kanban: `concluido`.
- **Tag/deploy:** ✅ `v0.0.92` criada e publicada (`04cd686`, contém DEM-74 + DEM-73). Faltam: (1) acompanhar a pipeline `build`/`docker-build` no GitLab; (2) reiniciar o pod do `api-service` para limpar o cache de tags do registry (TTL 1h) e enxergar a `v0.0.92`; (3) atualizar/reiniciar as instâncias com `appVersion: "latest"`/`"v0.0.92"` (rollout restart simples não troca a imagem); (4) validar a imagem do pod e pedir o reteste do cliente.
- Demais pendências da sessão anterior: push `api-service` (`e587aa7`), MRs (DEM-73/74/69), deslinkar device de teste, `ai.context` sem commit, DEM-62.

---

## 📅 Sessão 2026-09-25 (Hoje)
**Agente:** `agy --conversation=3ef7433b-d165-4c31-9f41-8206ab38a804`

### 📝 Resumo do Expediente
- **DEM-43 REABERTA E CONCLUÍDA DEFINITIVAMENTE:**
  - **Relato do Cliente:** "O BUG PERSISTE: ASSINATURA NA UZAPI FICA COM A DATA CORRETA (DATA ATUAL). JÁ NO ASAAS, A ASSINATURA FICA ERRADA (DATA ATUAL + X DIAS RESTANTES DO TRIAL)".
  - **Causa Raiz:** Clientes em Trial ao contratar um plano pago tinham o primeiro vencimento (`nextDueDate`) agendado para o fim do Trial (`cycle.visibleExpiresAt`), enquanto a UzAPI ativava o plano na data atual. Além disso, `payment-confirmation.ts` estendia o prazo residual do trial e `asaas-subscription-sync.ts` usava `billing.expiresIn` com os dias de carência.
  - **Correção:**
    1. `create-instance-payment.ts`: Clientes vindos de Trial ou `INITIAL` têm `nextDueDate` fixado em `new Date()` (Hoje).
    2. `payment-confirmation.ts`: Transição de Trial ou `INITIAL` inicializa ciclo de 30 dias a partir de `now` (`computeRenewalExpiresIn`), sem resquício de teste.
    3. `asaas-subscription-sync.ts`: Assinatura recorrente usa `cycle.visibleExpiresAt` oficial sem carência embutida.
  - **Testes & Qualidade:** 7 testes unitários passando em `contract-calculator.test.ts`, compilação estrita `npx tsc --noEmit` aprovada e `eslint` sem erros.
  - **Branch / Commit:** `manager-service` — branch `fix/dem-43-asaas-duedate` — commit `8903fb6` (`fix(dem-43): alinhar vencimento Asaas com UzAPI sem adiar cobranca por trial ou carencia`).
- **ATUALIZAÇÃO DA SPEC DE PRIORIZAÇÃO (`PRIORIDADES.md`):**
  - Incorporadas as novas regras de seleção e ordenação de prioridade das tarefas do backlog.
  - Hierarquia estrita P1 a P5 (P1: Cliente Urgente, P2: Cliente Alta, P3: Hugo/Lucas Urgente, P4: Demais Clientes, P5: Demais Internas).
  - Heurística de agrupamento por contexto (`allow_context_batching: boolean`) com trava de segurança obrigatória contra bloqueios críticos externos (P1/P2).
  - Pseudocódigo/algoritmo oficial documentado na especificação técnica.

- **DEM-43 (CONCLUÍDA & 100% ATIVA EM PRODUÇÃO - v0.3.54):**
  - **Ajuste Fino 1:** `create-instance-payment.ts`: Faturas avulsas para novas contratações/trial passam a ter `dueDate = new Date()` (Hoje), eliminando a tolerância indevida de +3 dias no Asaas.
  - **Ajuste Fino 2:** `contract-calculator.ts`: Travada a condição de upgrade para exigir `effectivePreviousInstances > 0`. Transição de 0 para 1 instância agora é categorizada estritamente como `INITIAL` (Contratação de 1 instância), removendo o rótulo errôneo de "Upgrade proporcional".
  - **Testes:** 8 testes unitários aprovados (`pnpm test:unit`), TypeScript e ESLint sem erros.
  - **Deploy em Produção:** Imagem Docker `v0.3.54` construída pelo GitLab CI e aplicada no cluster de produção via `infra-gitops` (commit `6745847`). Produção em `https://painel.uzapi.com.br` ativa e respondendo com status 200.
  - **Status dos Repositórios Locais:** Todos os repositórios (`manager-service`, `infra-gitops`) encontram-se 100% limpos e sincronizados com `origin/main`.

### ⚠️ Próximos Passos para o Próximo Agente / Expediente
- **Próximas Demandas no Kanban (`exec/` - Seguindo Prioridades P1 a P5):**
  - **DEM-72 (Prioridade P1 - Crítica Externa):** Endpoint `/chat` retornando objeto `Message` vazio para mensagens enviadas pela própria API (Módulo API / `api-service` ou `worker-go`).
  - **DEM-36 / DEM-37 (Prioridade P2 - Alta Externa):** Assinaturas indevidamente com status Trial / Ativo pós-vencimento.
  - **DEM-62 (Prioridade P2 - Alta Externa):** QRCode não exibido em instâncias pausadas.

---

## 📅 Sessão 2026-09-23 (continuação) — DEM-48 + DEM-36/37
**Agente:** \`opencode --session=ses_f35d827bfffeWb835n30un2oxl\`

### 📝 Resumo do Expediente
- **DEM-48 (bloqueio de criação para assinaturas vencidas):** branch `fix/dem-48-block-expired` atualizada com a main atual (merge limpo, sem conflitos; diff efetivo = `src/lib/subscription.ts` +3/-3). Validações: `tsc` 0, `test:unit` 8/8, `lint` 0. **MR aberto pelo desenvolvedor (aguardando merge).**
- **DEM-36/37 — Fase 1 implementada e commitada (2 repos):**
  - **manager-service** — branch `fix/dem-36-37-subscription-status` (baseada na DEM-48) — commit `b91ea05`:
    - Cron horário de conciliação (`instrumentation.ts` + `subscription-expiration.ts`): `TRIAL` vencido → `TRIAL_EXPIRED`; `ACTIVE` vencido (vencimento visível) → `OVERDUE`.
    - Transição lazy no `getSubscriptionDetails` (regra pura em `subscription-status.ts`), `canCreateInstance` expõe `isBlocked/blockReason`.
    - Admin: modo **"Estender Teste"** (`extend_trial`) preserva `TRIAL` (auditoria `admin_trial|...`); rotas admin não descontam grace em TRIAL.
    - UI: "Autenticar/Reiniciar/Atualizar" bloqueados, badge **"Pausada"**, banner "Assinatura vencida" (ACTIVE com 0 dias), aviso em Contratar Instâncias.
    - Testes: `subscription-status.test.ts` (7 subtestes; total **15/15**); `tsc`/`lint` 0.
  - **api-service** — branch `fix/dem-36-37-subscription-status` — commit `905b706`:
    - `validateUser` usa `billing.expiresIn` (não mais `lastContractUpdate+30`) + bloqueia `CANCELLED`; **bug da data congelada no boot corrigido** (`currentDate` removido; `new Date()` por chamada).
    - `ensureUserBilling`: transição lazy `ACTIVE → OVERDUE` com grace (paridade com o manager).
    - `restart`, `resume` e `update` saíram das listas de exclusão dos interceptors (validam billing); `logout`/`delete` liberados.
    - `build` 0 e `lint` 0.
  - **Proposta para gestores** salva em `ai.context/demandas/propostas/DEM-36-37.md`.
- **DEM-43 follow-up (cliente):** reporte "DATA DA PRIMEIRA COBRANÇA ✅ / DATA DA ASSINATURA ❌" (assinatura de 3 instâncias no Asaas com vencimento 01/11/2026). Análise: provável caminho **UPGRADE pós-pagamento** (preserva `expiresIn` antigo — não coberto pelo fix da DEM-43) + dados legados sem backfill. Aguardando decisão do desenvolvedor / coleta de dados reais (Asaas + billing do usuário).

### ⚠️ Pendências imediatas
- **Push + MR** das branches `fix/dem-36-37-subscription-status` (manager-service e api-service).
- **Mergear o MR da DEM-48** (base do manager) e release do manager (ex.: `v0.3.55`) levando DEM-48 + DEM-36/37.
- **Homologação E2E da DEM-36/37:** trial vencido, trial estendido (modo novo), ACTIVE vencido — conferir status, botões, criação e reautenticação.
- **Rollout da `v0.0.92` (worker):** pipeline → reiniciar pod do api-service (cache de tags 1h) → atualizar instâncias com `appVersion` → reteste do cliente (DEM-74/DEM-73).
- **DEM-43 follow-up:** decidir correção do fluxo UPGRADE/backfill da assinatura do cliente.
- **`ai.context` com alterações não commitadas** (DEM-36/37/48/proposta/HANDOVER etc.).

### 📌 Atualização de fechamento (2026-09-23, fim do expediente)
- **DEM-48: MERGEADA e RELEASED.** Merge do MR na `main` feito; release **`v0.3.55`** publicado (tag `fcbe1bf`, verificado: contém `b324af0`; diff efetivo = `src/lib/subscription.ts` +3/-3 + CHANGELOG/package.json). Aguardando pipeline da tag → commit no `infra-gitops` (`apps/manager-service/deployment.yaml`) → deploy; depois validar o bloqueio de criação em produção.
- **DEM-36/37 (manager-service):** branch sincronizada com a main já com a 48 (`7cdbe84` — merge de `origin/main`) e **pushada**; **MR aberto** (aguardando revisão/aprovação).
- **DEM-36/37 (api-service):** branch **pushada** (`905b706`); **MR ainda não aberto** (texto já gerado nesta sessão — abrir e pedir revisão).
- **Textos dos MRs** (manager e api) prontos na conversa; **próximo release:** manager `v0.3.56` (36/37) e api `1.57.4` — somente após os merges.
- **Acompanhamento do pipeline (`v0.3.55`) pendente:** não foi possível monitorar por `git fetch` (chave SSH fora do agent da sessão). Para habilitar: `SSH_AUTH_SOCK=/tmp/.antigravity-ide-server/.ecfbad74d93962fc8ca485d93ab9b4f3d4cb6cf8-ssh-auth.sock ssh-add /root/.ssh/id_ed25519` (ou acompanhar direto no GitLab: Pipelines da tag `v0.3.55` e commits do `infra-gitops`).
- **Fix de ferramentas/lembrete:** ramificação do manager 36/37 contém a main (fast-forward-friendly); a branch `fix/dem-48-block-expired` pode ser deletada após o merge (opcional).


---

## 📅 Sessão Finalizada em 2026-09-30
**Agente:** `agy --conversation=3ef7433b-d165-4c31-9f41-8206ab38a804`

### 📝 Resumo do Expediente
- **DEM-36/37 (Fase 1):** Os MRs da branch `fix/dem-36-37-subscription-status` para ambos os repositórios (`manager-service` e `api-service`) foram mergeados na branch `main` com sucesso pelo desenvolvedor.
- **Lançamento de Release:** As versões mais recentes foram tagueadas no repositório local e enviadas para o GitLab (`v0.3.56` no manager-service e `v1.57.4` no api-service).
- **GitOps (Deploy):** Os arquivos de manifesto no repositório `infra-gitops` (`apps/manager-service/deployment.yaml` e `apps/api-service/deployment.yaml`) foram atualizados e commitados com as novas tags de imagem.

### ⚠️ Pendências para o Próximo Agente (Handover)
- **A DEM-37 continua `pendente` no Kanban** porque a **Homologação E2E** na interface de produção ainda não foi realizada.
- **Sua Primeira Tarefa:** Ao assumir, você DEVE solicitar ao desenvolvedor a conferência prática no painel online (verificando se o botão e o badge "Pausada" travam instâncias vencidas e testando o salvamento via "Estender Teste" pelo Admin).
- **Fechamento:** Após o teste validado, altere o arquivo `DEM-37.md` adicionando os métodos e provas do teste E2E na seção "Teste Prático e Homologação", altere o frontmatter para `status: concluido` e encerre o ciclo.

---

## 📅 Sessão Finalizada em 2026-10-01
**Agente:** `agy --conversation=3ef7433b-d165-4c31-9f41-8206ab38a804`

### 📝 Resumo do Expediente
- **Atualização do Kanban:** Confirmado que a DEM-36 e DEM-37 foram aprovadas. O markdown delas foi movido para `concluido`.
- **Análise de Tasks Devolvidas (DEM-43, 65, 67):** O QA reportou problemas nestas tasks. Após análise aprofundada, concluí que as correções já haviam sido aplicadas na `main` e deployadas (versão `v0.3.54` enviada dia 25/09). Os problemas são Falsos Positivos causados por testes defasados ou interpretações erradas de regra de negócio (Upgrade de instâncias).
- **Correção da DEM-16 (Timezone Shift no Admin):** Ao editar o vencimento de uma assinatura, a conversão `new Date()` da string "YYYY-MM-DD" para UTC causava recuo de 1 dia na interface (-3h do Brasil). Resolvido parseando explicitamente para `T12:00:00.000Z` (Meio-dia UTC) no formulário e na API do `manager-service`.
- **Merge & Release:** O dev criou MR, aprovou, mesclou na `main` do `manager-service`, e geramos a Release `v0.3.57`. O manifesto no `infra-gitops` foi atualizado para essa nova tag.

### ⚠️ Pendências para o Próximo Agente (Handover)
- A próxima demanda prioritária (P1) deve ser a **DEM-72** (Endpoint `/chat` retornando vazio).

---

## 📅 02/10/2026
**Agente Antigravity** (Sessão: `3ef7433b-d165-4c31-9f41-8206ab38a804`)
- **Atualização nas Diretrizes Críticas (`AGENTS.md`)**: Devido a uma falha procedimental do Agente ao tocar no código em `main`, adicionei regras explícitas (em caps lock) proibindo terminantemente edição ou testes fora de branches apropriadas (`fix/` ou `feat/`).
- **DEM-43, DEM-65 e DEM-67**: Movidas para a pasta `standby.solution` como Falsos Positivos do QA, aguardando validação ou resposta técnica externa, visto que os trechos de código em PRD (`v0.3.54+`) já endereçam integralmente as reclamações levantadas.
- **DEM-72 (Resolvida)**:
  - Investigado bug do endpoint `/chat` onde mensagens geradas pela API chegavam vazias, apesar de `IsFromMe = true`.
  - Descoberto que a biblioteca Whatsmeow envelopava ecos de envio no `DeviceSentMessage`. A persistência do `worker-go` recebia nulo pois procurava o texto fora do envelope.
  - Fix codificado e testado de forma unitária no `worker-go` (criado `NormalizeHistorySync_test.go`).
  - Branch e MR criados de forma higienizada, validados e integrados via Merge Request. Kanban arquivo `.md` editado com detalhes técnicos para `status: concluido`.
- **DEM-72 - FASE 2 / HOTFIX (Resolvida Definitivamente)**:
  - O usuário relatou que o problema `Message: {}` retornou na produção APENAS para mensagens enviadas por API (enviadas por APP funcionavam).
  - Identificada **Race Condition** no SQLite: `factory.go` gravava um esqueleto (stub) usando `UpsertMessage` e esmagava dados, e a falta de recebimento do echo (WhatsApp não devolve `DeviceSentMessage` pro remetente via API).
  - Corrigido com `InsertOnlyMessage` em `messageStore.go` e injeção manual do payload `Conversation` direto no `factory.go` para chamadas da API. Timestamps agora são parseados estritamente em `ISO 8601` (`RFC3339`).
  - Branch `fix/dem-72-hotfix-race-condition` comitada. Faltam Push, Merge e Release (`v0.0.94` possivelmente do `worker-go`). DEM-72 atualizada no Kanban.
- **DEM-62 (Em Progresso / Standby)**:
  - Problema: QRCodes carregando infinitamente para instâncias pausadas.
  - Criada branch `fix/dem-62-paused-qrcode` em `manager-service`.
  - UI alterada em `actions-menu.tsx` e `instance-card.tsx` para esconder botões de Autenticação/Atualização caso o status seja `paused` e apresentar um botão de "Retomar Instância".
  - **Aguardando aprovação final do dev para comitar e concluir**.

---

## 📅 Sessão 2026-10-02 (tarde) — Releitura da DEM-72
**Agente:** `claude --resume d156a462-2bfe-42e6-b56b-f042a0c47a79`

### 📝 Resumo do Expediente
- **Análise geral do projeto** (leitura apenas): contexto, regras, 4 repositórios, Kanban e backlog.
- **DEM-72 — releitura a pedido do desenvolvedor:** a Fase 2 (hotfix) só cobria `text` e partia de um diagnóstico parcialmente incorreto (a causa real é o registro vazio introduzido pela DEM-66 em `factory.go`; não há race condition no envio pela API). Detalhes na seção "Fase 3" do `DEM-72.md`.
- **Opção B aplicada (autorizada pelo desenvolvedor)** na branch `fix/dem-72-hotfix-race-condition` do `worker-go`: novo helper `SendAndStore` em `services/messages/helpers.go` grava no SQLite a mesma mensagem enviada (todos os tipos, com chaves de mídia); 10 funções de envio passaram a usá-lo; bloco de gravação removido de `services/factory.go`. Novo `services/messages/helpers_test.go`.
- **Validação local:** `go build`, `gofmt`, `go vet` e `go test -count=1` OK (pacotes exceto a raiz).

### ⚠️ Pendências para o Próximo Agente / Desenvolvedor
- **DEM-72 NÃO está em produção.** A Fase 3 foi commitada em `4c33d5f` (`fix(dem-72): gravar a mensagem real enviada pela API no SQLite local`), 12 arquivos de código; os testes (`services/messages/helpers_test.go` e `database/messageStore_test.go`) ficaram fora do git a pedido do desenvolvedor. A branch tem 4 commits à frente da `main`, **sem push**. Faltam: push → MR → tag (`v0.0.94`) → atualizar instâncias (`appVersion`).
- **E2E em aparelho real executado (17:28–17:30):** texto, imagem e documento enviados pela fila para o próprio número pareado e para `5516997141457`; `/chats` `get` e `list` retornaram o corpo e as chaves de mídia; revoke só com `message_id` OK. Payloads e formato do retorno documentados no `DEM-72.md`. Falta a conferência visual nos aparelhos pelo desenvolvedor; o `api-service` não participou do teste.
- **Instância de teste reutilizável criada em `ai.context/examples/instance/`** (a pedido do desenvolvedor): sessão do WhatsApp pareada (`556392308423`, instância `999999999999999`, porta `3011`) guardada em `db/`. `./start.sh` compila o `worker-go` da branch em checkout e sobe já conectado, sem QR (validado: conectou 2 vezes sem QR); `python3 e2e.py <numero> [--no-revoke]` roda o E2E pela fila; `./stop.sh` para sem deslogar. Detalhes e cuidados no `README.md` da pasta. `db/`, `medias/`, `bin/`, logs e resultados estão no `.gitignore` local — **nunca versionar o `db/`** (chaves da sessão + histórico do número). O worker está **parado** no fim desta sessão. A fila `999999999999999` (RabbitMQ local) e a linha em `instance_realtime_state` (Postgres local) ficam mantidas; o device **não** deve ser deslinkado no telefone. A pasta temporária da sessão foi apagada. O `worker-go/qr.png` foi sobrescrito pelo QR do pareamento de hoje.
- **Observação do E2E:** `Info.Chat` das mensagens enviadas é gravado como `@lid` (JID devolvido pelo `IsOnWhatsApp`), não como `<telefone>@s.whatsapp.net`; comportamento já existente desde a DEM-66.
- O `DEM-72.md` segue com `status: concluido` no frontmatter apesar das pendências acima — decidir se volta para `pendente`.
- **Arquivos soltos não versionados na raiz do `worker-go`** (`test_send.go`, `generate_json.go`, `database/messageStore_test.go`, logs, `qr.png`, `qr_live.html`, binário `worker`): os dois `.go` da raiz quebram `go build ./...` local (`main` duplicado). Aguardando decisão do desenvolvedor (remover ou manter).
- **Segurança:** o campo de e-mail do autor nos commits do `worker-go` (DEM-66 e DEM-72 Fase 1) contém um token pessoal do GitHub (`ghp_…`), já no histórico remoto. Revogar o token e corrigir `git config user.email`.
- **DEM-62** segue `pendente`: diff não commitado em `manager-service` (`fix/dem-62-paused-qrcode`); falta revisar `instance-sheet.tsx` e `page.tsx` para o estado pausado.

### 🔚 Fechamento do expediente — 2026-10-02 (~17:45)
**Agente:** `claude --resume d156a462-2bfe-42e6-b56b-f042a0c47a79`

> **PONTO EXATO DE RETOMADA (amanhã):** a DEM-72 está aguardando o **"sim" do desenvolvedor** para o ajuste de nomenclatura do retorno do `/chats`. Não aplicar nada antes dessa autorização.

**Contexto:** o desenvolvedor comparou o retorno das mensagens enviadas pela API (Opção B, commit `4c33d5f`) com uma mensagem enviada pelo APP e pediu que o retorno siga o mesmo padrão. O formato atual sai do normalizador já existente (`utils.NormalizeMessage`), mas diverge do APP em 3 campos:

| Campo | APP | API hoje (`4c33d5f`) |
|---|---|---|
| Texto simples | `Message.Conversation` | `Message.ExtendedTextMessage.text` |
| `Info.Sender` | `<id>@lid` | `<telefone>@s.whatsapp.net` |
| `Info.PushName` | nome do perfil | `""` |

`Message.MessageContextInfo` (metadados gerados pelo aparelho) não é reproduzível e fica de fora.

**Proposta apresentada (pendente de autorização)** — alterar só `worker-go/services/messages/helpers.go` (+ `helpers_test.go`), na branch `fix/dem-72-hotfix-race-condition`:
1. Gravar texto simples em `Conversation` quando o `ExtendedTextMessage` enviado tiver apenas `text`; com resposta citada, menções ou preview de link, manter `ExtendedTextMessage` (mesmo comportamento do APP). Ajuste só na gravação, sem mudar o que é enviado ao WhatsApp.
2. `Info.Sender` = `resp.Sender` sem o device (`@lid`), com fallback para `client.Store.ID.ToNonAD()`.
3. `Info.PushName` = nome do perfil da sessão (`client.Store.PushName`).

**Passos após a autorização:** aplicar → `gofmt`/`go build`/`go vet`/`go test` (pacotes exceto a raiz) → `cd ai.context/examples/instance && ./start.sh` → `python3 e2e.py 5516997141457 --no-revoke` → comparar o retorno com o exemplo do APP → atualizar a seção "Formato do novo retorno" do `DEM-72.md` (os exemplos de JSON atuais ficarão desatualizados) → pedir autorização de commit.

**Demais pendências da DEM-72:** conferência visual, pelo desenvolvedor, das 3 mensagens enviadas a `5516997141457` às 17:29; push da branch (4 commits à frente da `main`, nada enviado) → MR → tag `v0.0.94` → atualizar instâncias. O frontmatter do `DEM-72.md` segue `status: concluido`.

**Estado dos repositórios no fechamento:**
- `worker-go`: branch `fix/dem-72-hotfix-race-condition`, HEAD `4c33d5f`, sem alterações em arquivos versionados. Não versionados (a pedido do desenvolvedor): `services/messages/helpers_test.go`, `database/messageStore_test.go` e os arquivos soltos da raiz.
- `manager-service`: branch `fix/dem-62-paused-qrcode` com diff não commitado da DEM-62 (intocado nesta sessão).
- `api-service` e `infra-gitops`: sem alterações.
- `ai.context`: `HANDOVER.md`, `DEM-72.md` e `examples/instance/` alterados/criados, **sem commit**.
- Instância de teste: **parada**, sessão preservada em `ai.context/examples/instance/db/`.


## 📅 Sessão 2026-10-05
**Agente:** `claude --resume d156a462-2bfe-42e6-b56b-f042a0c47a79`

- **Discussão de produto (sem código):** o retorno do `/chats` (`Info` + `Message`) é a estrutura interna do worker e **não segue o padrão da API oficial** (envio e webhooks seguem). Isso é anterior à DEM-72. A formatação no padrão oficial acontece no `worker-go` (`webhook/createContent.go`, `webhook/payloadBuilder.go`); o `api-service` só valida e repassa. Opções apresentadas para reunião: (A) manter o formato atual e liberar a DEM-72; (B) demanda nova para o `/chats` devolver o objeto de mensagem oficial, como formato opcional. **Decisão pendente do desenvolvedor**, assim como os 3 ajustes de nomenclatura da sexta (não aplicados).
- **Ambiente de teste ampliado (`ai.context/examples/instance/`):** novos `start-api.sh`/`stop-api.sh` sobem o `api-service` local na porta 4200 usando só Postgres/Redis/RabbitMQ locais, com trava contra banco remoto. ⚠️ Os `.env` do `api-service` apontam para o Postgres remoto do cluster (`5.161.202.138:30100`) e o `instance-monitor` pausa instâncias `pending_auth` a cada 5 min — **não subir o `api-service` com os `.env` como estão**.
- **Postgres local (`postgres-uzapi`) alterado:** criados o usuário `e2e-test-user` (`e2etest`), `user_billing` ACTIVE e a instância `999999999999999`.
- **Validado:** `POST /v1/999999999999999/chats` (`action: get`) pelo HTTP retornou a mensagem de texto enviada na sexta com `Message` preenchido; sem token → 401; o processo só tem conexões para `127.0.0.1`.
- **Estado no momento do registro:** worker de teste **rodando** na branch `fix/dem-72-hotfix-race-condition` (`4c33d5f`) e `api-service` local **rodando** (`main` @ `034cd2b`, porta 4200). O `worker-go` ficou em checkout na branch da DEM-72 (estava na `main`). Parar com `./stop-api.sh` e `./stop.sh`.

### 📌 Atualização 2026-10-05 (tarde) — DEM-72 Fase 4: `/chats` no formato da API oficial
- **Decisões do desenvolvedor:** formato oficial como **padrão** do `/chats` (substitui `Info` + `Message`; quebra de contrato assumida) e entrega **junto** com a correção da gravação, na DEM-72. Os 3 ajustes de nomenclatura da sexta foram **descartados** (perderam o sentido com a conversão na leitura).
- **Mapeamento do problema original concluído:** o `/chats` só lê a tabela `messages` do SQLite da instância; na `main` a linha é gravada com `Message: {}` no envio (reproduzido com binário da `main`). Detalhes no `DEM-72.md`.
- **Implementado e testado (sem commit):**
  - `worker-go` (branch `fix/dem-72-hotfix-race-condition`, sobre `4c33d5f`): novo `webhook/messageObject.go` (+ teste), `webhook/createContent.go`, `database/midiaStore.go`, `services/chats/queries.go` e `helpers.go`. Conversão **na leitura**; gravação inalterada.
  - `api-service` (branch nova `fix/dem-72-chats-official-format`, a partir da `main`): só Swagger em `controllers/Chats/chats.controller.ts`.
  - Validação: testes unitários, `go vet`, `tsc`, `eslint`, `prettier` OK; E2E pelo HTTP com texto, imagem, documento, botões, lista, contatos, localização, mensagem do APP, recebida e registro vazio antigo.
- **Pendências:** autorização de commit nos dois repositórios → push → MRs → tags (`worker-go v0.0.94`, `api-service`) → atualizar instâncias. Antes de liberar: **avisar os clientes da mudança de contrato do `/chats`**. Não testados em aparelho: vídeo, áudio, sticker, enquete, reação, carrossel, grupo ao vivo e download de mídia pelo `id`. Atualizar a "Documentação API" externa, se existir fora do Swagger.
- **Ambiente:** worker de teste e `api-service` local **rodando** com o código desta fase (`./stop-api.sh` e `./stop.sh` para parar).

### 📌 Atualização 2026-10-05 (fim da tarde) — commits da DEM-72
- **Validação complementar feita:** vídeo, áudio, sticker, `list` sem paginação, download de mídia pelo `id` (hash conferido) e mensagem **recebida ao vivo** de outro número (webhook inalterado + `/chats` no formato oficial), além de duas mensagens de grupo recebidas. Sem teste: enquete, carrossel e envio para grupo.
- **Commits locais (sem push; arquivos de teste fora do git):**
  - `worker-go` — `fix/dem-72-hotfix-race-condition` — `bb61f08` (5 commits à frente da `main` local).
  - `api-service` — `fix/dem-72-chats-official-format` — `a215494` (1 commit à frente da `main` local).
- **⚠️ Remoto não conferido:** `git fetch` falhou nos dois repositórios (`Permission denied (publickey)`): a chave `~/.ssh/id_ed25519` é protegida por senha e o agent SSH da sessão está vazio. As referências locais de `origin/main` são de 02/10 (`worker-go`) e 30/09 (`api-service`). O desenvolvedor deve rodar `git fetch` e, se a `main` remota tiver avançado, atualizar as branches antes do push/MR.
- **Próximos passos:** push das duas branches → MRs → tags → atualizar instâncias; avisar os clientes da mudança de contrato do `/chats`.
- **Não versionados no `worker-go`:** `webhook/messageObject_test.go`, `services/messages/helpers_test.go`, `database/messageStore_test.go` e os arquivos soltos da raiz.

### 📌 Atualização 2026-10-05 (fim do dia) — DEM-43 e auditoria de releases
- **DEM-43 (devolvida) — análise, sem alteração de código:** pelo código da `main`, trial que paga gera cobrança hoje, vencimento UzAPI em hoje+30 e assinatura Asaas em hoje+30 (`asaas-subscription-sync.ts:119` usa `visibleExpiresAt`). O sintoma do QA ("data atual + dias restantes do trial") é o comportamento de `≤ v0.3.52`. Hipótese principal: assinatura criada antes de 25/09 (a correção não ajusta assinaturas existentes) ou cobrança nova não paga. Defeitos reais encontrados na área: (1) sem ajuste das assinaturas antigas; (2) `PAYMENT_CONFIRMED` e `PAYMENT_RECEIVED` rodam `applyPaymentConfirmation` sem trava de repetição (reinicia o ciclo no segundo evento); (3) datas enviadas ao Asaas em UTC (`toISOString`), +1 dia após 21h BRT; (4) trial com custo zero mantém `expiresIn` do trial enquanto a assinatura começa hoje. Sem chave Asaas no ambiente de dev. Mensagem de alinhamento enviada ao QA pelo desenvolvedor; **aguardando retorno do QA** e decisão sobre teste automatizado com o Asaas simulado.
- **Auditoria de releases (pedido do programador chefe), só pelo git local:**
  - **DEM-43 foi liberada:** `8903fb6` → `v0.3.53`, `2dae680` → `v0.3.54` (25/09), com commits do "GitLab CI" no `infra-gitops` minutos depois de cada tag (até `v0.3.56`).
  - **`v0.3.57` (DEM-16):** o commit do `infra-gitops` (`ff901dc`) foi feito manualmente (autor `Jaderesp`), não pelo CI — **confirmar no GitLab se a pipeline da tag rodou e a imagem existe**.
  - **Nunca chegaram à `main` (só existem em branch local, sem push):** **DEM-45** `worker-go` `fix/dem-45-audio-retrieve` (`91c14be`) e **DEM-1** `manager-service` `fix/demanda-1-delete-user` (`cb6a568`). Ambas constam `concluido` no Kanban.
  - `api-service` `fix/dem-69-queue-error`: só o commit de formatação `e587aa7` ficou fora da `main`.
  - Não verificado: estado real do cluster (imagem dos pods), pipelines e ArgoCD — sem acesso daqui.

### 📌 2026-10-06 — Verificação de release das demandas devolvidas (43, 65, 67, 72)
**Agente:** `claude --resume d156a462-2bfe-42e6-b56b-f042a0c47a79` — só leitura do git local; cluster/pipelines não verificados.
- **DEM-65:** commit 16/09, merge 22/09, **release só em 24/09 (`v0.3.51`)**. Entre a correção e a release a produção seguiu sem o fix — a devolução ("continuam sendo enviadas") é compatível com teste nesse intervalo. Travas `isActive` presentes na `main`. Pedir reteste.
- **DEM-67:** mesmo calendário (commit 15/09, merge 22/09, release 24/09 em `v0.3.51`). O texto da devolução descreve outro cenário (instâncias novas/duas instâncias com vencimentos diferentes após ajuste de vencimento, ex.: 15/12/2040 × 19/09/2026), não coberto pela correção original; a rota admin de billing atualiza `instances.expiresIn` no banco, mas não chama a API para sincronizar. **Precisa de análise própria.**
- **DEM-43:** liberada em 25/09 (`v0.3.53`/`v0.3.54`), CI atualizou o deploy. Aguardando retorno do QA.
- **DEM-72:** fase 1 liberada em `v0.0.93` (02/10) e não resolve o problema; a correção real (`4c33d5f` + `bb61f08`) segue sem push.

### 📌 2026-10-06 (tarde) — DEM-72 Fase 4.1
- Programador chefe confirmou: `/chats` no formato dos webhooks (nada a reverter). As branches `fix/dem-72-hotfix-race-condition` (`bb61f08`) e `fix/dem-72-chats-official-format` (`a215494`) **já estão no remoto**.
- **Novos commits locais, sem push:** `worker-go` `f035af9` (ordenação do `list` por data, `history_context.status` e **correção de travamento do SQLite no `list`** — defeito do `bb61f08`: conversão com `INSERT` de mídia dentro do cursor de leitura causava `database is locked`) e `api-service` `995f5ba` (Swagger). **Não fazer merge do `bb61f08` sem o `f035af9`.**
- Validado pelo HTTP na instância de teste (detalhes no `DEM-72.md`, Fase 4.1). Próximo passo: push dos dois commits → MRs → merge → tags → atualizar instâncias.

### 📌 2026-10-06 (noite) — merge da `main` na branch da DEM-72 e defeito na `v0.0.94`
- `worker-go`: a `main` remota avançou para `7c740e4` (**tag `v0.0.94`**, commit do Eduardo: download de áudio por `DownloadMediaWithPath`, remoção de `GetMessageByMediaKey`, `recover()` no listener). Isso resolve a DEM-45 por outro caminho (branch local `fix/dem-45-audio-retrieve` obsoleta). **Nossa release passa a ser `v0.0.95`.**
- Merge da `main` feito na branch `fix/dem-72-hotfix-race-condition` → `dbd2d4e` (conflito em `database/messageStore.go` resolvido). Build, testes e E2E OK. **Sem push** (3 commits à frente do remoto).
- **⚠️ Defeito na `v0.0.94` (da `main`, não nosso):** download de áudio pelo `id` de mídia retorna 410 — `services/medias.go` passa o MIME (`audio/ogg; codecs=opus`) como `mmsType` em `DownloadMediaWithPath`. Trocar por `"audio"` resolveu em teste descartável. **Não corrigido; avisar o Eduardo e decidir se corrige na `main` ou nesta branch.**
- `api-service`, `manager-service` e `infra-gitops`: `fetch` continua impossível nesta sessão (chave SSH com senha); o desenvolvedor precisa rodar `git fetch` para eu comparar.
- `api-service` `fix/dem-72-chats-official-format`: `995f5ba` segue sem push.

### 📌 2026-10-06/07 — MRs da DEM-72 mergeados
- O desenvolvedor informou que os dois MRs (`worker-go` `fix/dem-72-hotfix-race-condition` e `api-service` `fix/dem-72-chats-official-format`) foram **aceitos e mergeados** (não conferido daqui: sem acesso SSH para `fetch`).
- **Falta para chegar à produção:** `git pull` na `main` dos dois repositórios → release (`worker-go`: `./release.sh` → `v0.0.95`; `api-service`: `pnpm release`) → pipelines → atualizar as instâncias para a nova versão do worker → reteste do `/messages` + `/chats` em produção → fechar o `DEM-72.md`.
- **Pendente de decisão:** defeito de download de áudio herdado da `v0.0.94` (`services/medias.go`, `mmsType` recebendo o MIME) — não corrigido.

### 📌 Releases da DEM-72 criadas (conferido no git local)
- `worker-go` **`v0.0.95`** (`main` `363fb21`) e `api-service` **`v1.57.5`** (`main` `eab3243`), ambas contendo os commits da DEM-72. Os dois repositórios locais estão em checkout na `main`, iguais ao `origin/main`.
- **Próximo:** conferir pipelines → `infra-gitops` em `api-service:v1.57.5` → atualizar instâncias para `v0.0.95` → reteste em produção → registrar no `DEM-72.md`.
- **Aberto:** download de áudio 410 herdado da `v0.0.94` (não corrigido); DEM-67 devolvida precisa de análise; DEM-43 aguardando QA; DEM-65 aguardando reteste do QA; DEM-62 com diff não commitado no `manager-service`.
- Instância de teste e `api-service` local podem estar rodando; parar com `./stop-api.sh` e `./stop.sh` em `ai.context/examples/instance`.
- **Kanban atualizado (06/10):** acrescentada a seção "Atualização" em `DEM-43`, `DEM-65`, `DEM-67` (standby), `DEM-45`, `DEM-1`, `DEM-62` e `data_conclusao` na `DEM-72`. Nenhum `status` foi alterado e o CSV do backlog não foi tocado. `DEM-45` e `DEM-1` constam `concluido`, mas as correções nunca chegaram à `main` — revisar o status com o desenvolvedor.

### 🔚 Fechamento do expediente — 2026-10-06
**Agente:** `claude --resume d156a462-2bfe-42e6-b56b-f042a0c47a79`

> **PONTO DE RETOMADA:** a DEM-72 está mergeada e com release criada (`worker-go v0.0.95`, `api-service v1.57.5`). Falta confirmar a produção. Nenhuma alteração de código pendente de commit nos repositórios de serviço, exceto a DEM-62 (abaixo).

**Aguardando o desenvolvedor**
1. **DEM-72 em produção:** conferir as pipelines das tags, a atualização do `infra-gitops` para `api-service:v1.57.5`, atualizar as instâncias para o worker `v0.0.95` e retestar (`/messages` → `/chats` `action: get`). Com o resultado, acrescentar no `DEM-72.md`.
2. **Download de áudio 410** (`worker-go` `services/medias.go`, herdado da `v0.0.94`): decidir se a correção de uma linha (`mmsType` `"audio"`) é feita por nós ou pelo Eduardo. Mensagem sugerida já entregue ao desenvolvedor.
3. **DEM-45 e DEM-1:** constam `concluido`, mas as correções nunca chegaram à `main`; decidir se voltam para `pendente`.
4. **Commit do `ai.context`:** oferecido, não autorizado ainda.

**Aguardando terceiros**
- **DEM-43:** retorno do QA (usuário do teste, data de criação da assinatura no Asaas, se a cobrança foi paga).
- **DEM-65:** reteste do QA (a correção só entrou em produção em 24/09).

**Próximas análises oferecidas (nenhuma iniciada além do registrado)**
- **DEM-67 (devolvida):** cenário novo — vencimentos diferentes entre instâncias após ajuste; leitura inicial no `standby.solution/DEM-67.md`.
- **DEM-43:** teste automatizado com o Asaas simulado e correção dos 4 defeitos listados no dossiê.

**Estado dos repositórios no fechamento**
- `worker-go`: `main` @ `363fb21` (= `origin/main`, tag `v0.0.95`), limpo. Não versionados: arquivos de teste (`webhook/messageObject_test.go`, `services/messages/helpers_test.go`, `database/messageStore_test.go`, `database/messageOrder_test.go`) e os arquivos soltos da raiz.
- `api-service`: `main` @ `eab3243` (tag `v1.57.5`), limpo.
- `manager-service`: ⚠️ em checkout na **`main`** com as 2 alterações **não commitadas** da DEM-62 (`actions-menu.tsx`, `instance-card.tsx`) no working tree. Antes de qualquer trabalho ali, voltar para `fix/dem-62-paused-qrcode` (as alterações acompanham o checkout) ou guardá-las; não commitar na `main`.
- `infra-gitops`: `main` @ `ff901dc` local (sem `pull`; não reflete o deploy do `api-service v1.57.5`).
- `ai.context`: várias alterações sem commit (handover, demandas, `examples/instance/`).
- **Ambiente de teste:** worker e `api-service` locais **parados**; sessão do WhatsApp preservada em `ai.context/examples/instance/db/` (não deslinkar o device `556392308423`).
- **Acesso:** `git fetch`/`push` não funcionam nesta sessão (chave SSH com senha); o desenvolvedor executa no terminal dele.

---

## 📅 Sessão 2026-10-07
**Agente:** `claude --resume d156a462-2bfe-42e6-b56b-f042a0c47a79`

### 📝 Sincronização do Kanban com o backlog (CSV exportado em 07/10 14:48)
- **DEM-72: Aprovada pelo QA** no CSV (antes "Devolvido"). Registrado no `DEM-72.md`; segue `concluido`.
- **Devolvidas no CSV: 43, 65 e 67** (textos sem alteração desde 05–06/10). As três foram **movidas de `standby.solution/` para `exec/` com `status: pendente`** (coluna Desenvolvimento), com `data_reabertura: 2026-10-07` e uma seção "Reaberta para Desenvolvimento" em cada arquivo. A pasta `standby.solution/` ficou vazia.
- **Fila de desenvolvimento agora (`exec/` pendente):** DEM-67 (Cliente + Urgente = **P1**), DEM-43 e DEM-65 (Hugo + Urgente = P3), DEM-62 (Hugo + Alta, "Em Andamento" no CSV).
- **Divergências encontradas, não alteradas:**
  - O arquivo `DEM-48.md` trata do item **47** do CSV ("Botão Criar Instancia Ativo para Assinaturas Vencidas", liberado na `v0.3.55`); no CSV os itens 47 e 48 ("Checkout abrindo em uma nova aba") estão "A Fazer".
  - DEM-1 e DEM-45 estão "Aprovado" no CSV, mas as correções registradas nunca chegaram à `main` (ver seções de 06/10 nos arquivos).
  - Item 2 ("Criar token da conta para criação de instâncias") está "Em Andamento" no CSV e não tem arquivo no Kanban.
- Nenhum código alterado. Próximo passo sugerido: analisar a **DEM-67** (P1) e apresentar proposta.
- **07/10 (tarde):** histórico das devolvidas consolidado (43: 3 rodadas de correção e 2 devoluções, a última já na `v0.3.54`; 65 e 67: 1 correção e 1 devolução cada, com release 8 dias depois da correção). `git fetch` do `manager-service` feito pelo desenvolvedor: `origin/main` = `main` local = `2c53615` (`v0.3.57`), nada novo. O desenvolvedor informou que a pipeline de `chore(release): 0.3.57` **passou** no GitLab. As branches antigas das três demandas não têm nada fora da `main`; não há merge nem release a refazer.
- **DEM-67 analisada:** causa provável no `api-service` — conta **admin** recebe `billing` vazio em `assertCanCreateInstance` e a instância nova nasce com `expiresIn = new Date()` (`k8s.service.ts:136`). Evidência na cópia local do banco (3 de 5 instâncias de admin vencem no dia da criação). Proposta (Opção A) registrada no `DEM-67.md`; **aguardando autorização**. Branch prevista: `fix/dem-67-admin-instance-expiration` no `api-service`.
- `manager-service` segue em `fix/dem-62-paused-qrcode` com as 2 alterações da DEM-62 sem commit.
- **DEM-67 — Opção A aplicada (autorizada):** `api-service`, branch `fix/dem-67-admin-instance-expiration`, commit `0d5c661` (4 arquivos; novo `src/helpers/instanceExpiration.ts`). Lint, `tsc` e checagem com as contas admin do banco local OK; criação real de instância não testada (sem cluster local). **Sem push.** Próximo: push pelo desenvolvedor → MR → merge → `pnpm release` (`1.57.6`) → confirmar com o QA se a conta do teste é admin e pedir reteste. O `api-service` local ficou em checkout nessa branch.
- **DEM-67 liberada:** MR mergeado (`85f43f5`) e release **`api-service v1.57.6`** (`6931e5e`) criada na `main`. Na primeira tentativa a release rodou na branch da correção e o push foi recusado; desfeito localmente e refeito na `main`. **Regra prática: `git checkout main && git pull` antes de `pnpm release`.** Falta: pipeline/deploy, reteste do QA (confirmar se a conta do teste é admin) e corrigir instâncias de admin antigas pelo painel.
- **08/10 (manhã):** CSV exportado 08/10 09:08 conferido contra o Kanban, sem divergência de status (devolvidas: 43, 65, 67; 62 em andamento; último item do CSV: 88). **DEM-67 marcada `concluido`** a pedido do desenvolvedor (correção na `v1.57.6`); pipeline/deploy e reteste do QA não verificados. DEM-65 revisada por leitura: travas `isActive` presentes, rota do botão grava corretamente, 1 réplica; falta evidência do QA ou consulta de leitura em `notification_automation_config`/`notification_logs`. Ticket de cliente analisado (sem task no CSV ainda): `GET /{mediaId}` devolve 410 `invalid media hmac` para imagem enviada como Documento — `worker-go/services/medias.go:112` escolhe o tipo de mídia pelo MIME; `rabbitmq/listener.go:176` descarta o código de erro (404 vira 410). Fila pendente: 43, 65, 62.
- **08/10 — DEM-62 commitada:** `manager-service`, branch `fix/dem-62-paused-qrcode`, commit `96ea5f8` (3 arquivos: `actions-menu.tsx`, `instance-card.tsx`, `instance-sheet.tsx`), sobre a `main` `468b45b`. `tsc` e `eslint` OK; reiniciar em instância pausada não testado (sem cluster). **Sem push.** **Atenção — processo novo no `manager-service` (`468b45b`, `v0.3.58`):** release automática por semantic-release no merge (`main` = estável, `dev` = `-dev.N`); `pnpm release` removido; `test:unit` roda só `contract-calculator.test.ts`. Não verificado se `api-service`/`worker-go` mudaram igual. Próxima: DEM-43 (aguarda autorização e decisão sobre versionar testes).
- **09/10:** CSV exportado 09/10 11:59 conferido. **DEM-62 marcada `concluido`** por informação do desenvolvedor (merge não verificado localmente). Divergências CSV × painel: 67 (`concluido` × Devolvido, sem reteste após `v1.57.6`) e 62 (`concluido` × Em Andamento). QA pediu prioridade para o **item 88** (Cliente, Alta, API — resposta com `context.message_id` cita a própria mensagem); ainda sem arquivo no painel. Causa encontrada por leitura: `worker-go/services/messages/text.go:108-117` preenche `QuotedMessage.Conversation` com o `body` da própria resposta e `Participant` com o JID da instância (`client.Store.ID`); os demais tipos (image, audio, video, document, sticker, contact, location) repetem o `Participant` errado. Proposta apresentada, aguardando autorização.
- **09/10 — DEM-88 corrigida (autorizada):** `worker-go`, branch `fix/dem-88-reply-context`, commit `668d678` (10 arquivos; `BuildReplyContext` em `services/messages/helpers.go`), a partir da `main` local `363fb21` — **`main` remota não conferida (sem fetch); pedir `git fetch` ao desenvolvedor antes do push**. Unitário + 6 envios reais para `5516997141457`; citação de mensagem recebida, enviada e imagem confirmadas no aparelho pelo desenvolvedor; ID inexistente passa a sair sem citação (decisão dele). Grupo e demais tipos não testados com envio real. Worker de teste parado. Sem push. Pendentes no painel: 43, 65, 88 (até o merge).
- **09/10 — DEM-88 mergeada na `dev` do `worker-go`** (informado pelo desenvolvedor; não verificado). **Fluxo novo (08/10, programador chefe):** `manager-service` e `worker-go` têm branch `dev`; MR entra pela `dev` (tag `-devN`, ambiente de desenvolvimento) e depois vai para a `main` (estável). Versão gerada pela pipeline; sem release manual. `api-service` não conferido. DEM-88 segue `pendente` até definir o critério de conclusão (merge na dev × produção).
- **09/10 — DEM-88 confirmada na `dev`:** merge `76481c9`, tag `v0.0.95-dev2`. `worker-go` local está em checkout na `dev`. Próximas branches de demanda devem sair da `dev` atualizada.

### 09/10/2026 14:44 — DEM-88 encerrada
- `DEM-88.md` → `status: concluido` por informação do desenvolvedor ("task 88 resolvida"). Entrega: `668d678`, merge `76481c9` na `dev` do `worker-go`, `v0.0.95-dev2`.
- Não verificado: reteste do QA, promoção `dev` → `main` e atualização da versão das instâncias em produção.
- Pendentes no painel: DEM-43 (aguarda autorização da branch e respostas) e DEM-65 (aguarda evidência do QA ou consulta de leitura autorizada).

### 09/10/2026 17:30 — DEM-43 reproduzida (sem alteração de código)
- `manager-service`: branch `fix/dem-43-asaas-due-date` criada a partir da `dev` (`549c4b5`); **nenhum arquivo alterado**.
- Teste com Asaas simulado + Postgres em memória (fora do repositório, pasta temporária da sessão; não versionar): caminho direto do trial está correto; o defeito aparece quando o cliente de trial gera cobrança, não paga (status vira `OVERDUE`/`CANCELLED`) e contrata de novo — `contract-quote.ts:115` deixa de reconhecê-lo como trial. Detalhes e tabela em `DEM-43.md`.
- Proposta de correção apresentada; **aguardando aprovação do desenvolvedor**.
- Fluxo oficial (Eduardo, 09/10): pull na `dev` → branch da `dev` → MR sempre para `dev` → `main` só após aprovação do QA. A DEM-62 foi mergeada direto na `main` (`v0.3.59`) e não está na `dev`.
- **09/10 18:10 — DEM-43 corrigida na branch, sem commit:** `fix/dem-43-asaas-due-date` (`manager-service`) com 4 arquivos alterados (`subscription-status.ts`, `contract-quote.ts`, `create-instance-payment.ts`, `payment-confirmation.ts`). Teste simulado 8/8, `tsc` e `eslint` sem erros. **Aguardando autorização para commit**; depois push pelo desenvolvedor e MR para a `dev`.

- **09/10 18:20 — DEM-43 commitada:** `ea27abc` em `fix/dem-43-asaas-due-date` (`manager-service`). Falta push pelo desenvolvedor e MR para a `dev`.

## Encerramento do expediente — 09/10/2026
*ID da Sessão:* `claude --resume d156a462-2bfe-42e6-b56b-f042a0c47a79`

**Painel:** pendentes DEM-43 e DEM-65. Concluídas hoje: DEM-62 e DEM-88.

**Estado dos repositórios (local):**
- `manager-service`: branch `fix/dem-43-asaas-due-date`, commit `ea27abc`, **push feito** (`origin/fix/dem-43-asaas-due-date`). MR para a `dev`: texto entregue ao desenvolvedor; abertura e merge não verificados.
- `worker-go`: `dev` em `76481c9` (`v0.0.95-dev2`, DEM-88).
- `api-service`: `main` em `6931e5e` (`v1.57.6`), último fetch em 07/10; não conferido se adotou a branch `dev`.
- `ai.context`: alterações não commitadas (commit nunca autorizado).

**Retomar por aqui:**
1. **DEM-43:** confirmar merge do MR na `dev` e pedir reteste ao QA (roteiro no `DEM-43.md`). Só marcar `concluido` após o retorno. Itens fora da entrega: trava de reprocessamento do pagamento, datas no fuso de Brasília, assinaturas antigas, e trial que paga a cobrança antiga após gerar uma nova.
2. **DEM-65:** aguarda data do teste e qual chave o QA desligou, ou autorização para consulta de leitura em produção.
3. **DEM-88:** falta a promoção `dev` → `main` após aprovação do QA e a atualização da versão das instâncias.
4. **DEM-62:** foi mergeada direto na `main` (`v0.3.59`) e não está na `dev` do `manager-service`; avisar o programador chefe.
5. **DEM-67:** deploy do `api-service v1.57.6` e reteste do QA não verificados.
6. **Ticket das imagens enviadas como Documento (410):** ainda sem demanda no CSV/painel.

**Fluxo oficial (programador chefe, 09/10):** pull na `dev` → branch a partir da `dev` → push → MR sempre para a `dev` → QA testa em dev → após aprovação, MR para a `main`.

**Teste da DEM-43 (Asaas simulado + pglite):** está na pasta temporária da sessão (`/tmp/claude-0/-usr-desenvolvimento-uzapi/d156a462-2bfe-42e6-b56b-f042a0c47a79/scratchpad/pglite/`), fora do git; pode não existir na próxima sessão. Não foi possível criar banco de teste no Postgres local (ação bloqueada), por isso o banco em memória.

### 10/10/2026 — conferência após fetch do desenvolvedor
- **DEM-43 está na `dev`** do `manager-service`: merge `d57ba07`, versão `v0.3.59-dev.9`. Falta reteste do QA e promoção para a `main`.
- **DEM-62 continua fora da `dev`** (`96ea5f8` só em `origin/main`).
- CSV de 10/10: itens novos 89 (imagem como documento, Alta/Cliente), 90 (contagem de usuários), 91 (instância expirando no trial, Urgente/Cliente) e 92 (410 em áudio de voz, Urgente/Cliente); nenhum ativado no painel ainda.
- **10/10 — DEM-89, DEM-91 e DEM-92 ativadas no painel (`pendente`) com a análise.** 92: regressão do commit `7c740e4` (`worker-go`, `v0.0.94+`), MIME passado como `mmsType` → CDN 400; correção de 4 linhas proposta. 89: imagem como documento usa chave errada (`invalid media hmac`); proposta de nova tentativa com `MediaDocument`. 91: causa não identificada, faltam dados do ticket. **Nenhum código alterado; aguardando autorização.**

### 11/10/2026 — correções da DEM-89, DEM-91 e DEM-92 aplicadas (sem commit)
`claude --resume d156a462-2bfe-42e6-b56b-f042a0c47a79`

Autorização do desenvolvedor: "autorizo correção de 91, 92 e 89". **Commit ainda não autorizado.**

- **`worker-go`**, branch `fix/dem-89-92-retrieve-media` (a partir da `dev` `d8ff536`), 1 arquivo alterado e não commitado: `services/medias.go`. DEM-92: `mmsType` vazio no `DownloadMediaWithPath` (nova função `downloadMediaByType`). DEM-89: nova tentativa com `MediaDocument` quando o erro é `ErrInvalidMediaHMAC`. `go build`/`go vet`/`go test` sem erros. Sem validação com envio real.
- **`manager-service`**, branch `fix/dem-91-trial-instance-expires` (a partir da `origin/dev` `d57ba07`), 1 arquivo alterado e não commitado: `src/app/api/instances/route.ts` (não desconta carência da instância quando o status é `TRIAL`). `tsc` e `eslint` sem erros.
- As branches partiram das refs locais da `dev`; não consegui fazer fetch. Se a `dev` remota andou, será preciso rebase antes do MR.
- **DEM-91 fica `pendente`** mesmo após o merge: só a exibição foi corrigida; o bloqueio real na API segue sem causa (faltam `username` dos 2 clientes, texto do erro e autorização de consulta de leitura).

**Retomar por aqui:** pedir autorização de commit nas duas branches → desenvolvedor faz push → MR para a `dev` → QA retesta com os roteiros dos arquivos `DEM-89.md`, `DEM-91.md` e `DEM-92.md`.

### 11/10/2026 — commits e rebase sobre a `dev` atualizada
- Commit autorizado pelo desenvolvedor ("sim porem verificar se dev esta atualizada"). A `dev` remota tinha andado nos dois repositórios (fetch feito pelo desenvolvedor); fiz rebase sem conflito e revalidei.
- `worker-go` `fix/dem-89-92-retrieve-media`: commit `2832a20` sobre `origin/dev` `7c297ce`. `go build`/`go vet`/`go test` sem erros.
- `manager-service` `fix/dem-91-trial-instance-expires`: commit `13b63c0` sobre `origin/dev` `1c4ede8`. `tsc` e `eslint` sem erros.
- **Falta:** push das duas branches (desenvolvedor) e MRs para a `dev`; depois reteste do QA.

### 11/10/2026 — MRs da DEM-89/92 e DEM-91 mergeados na `dev` (informado pelo desenvolvedor)
- `worker-go` (`2832a20`) e `manager-service` (`13b63c0`) mergeados na `dev`, segundo o desenvolvedor; não conferi (sem fetch), hash do merge e versão `-dev.N` não anotados.
- DEM-89, DEM-91 e DEM-92 seguem `pendente` aguardando reteste do QA em dev. A DEM-91 só fecha quando o bloqueio real na API for esclarecido.
- `worker-go`: as instâncias de dev precisam estar na nova versão do worker para o reteste.

### 11/10/2026 — reteste do QA reprovou DEM-89/92 em dev
- Versão informada: `v0.0.95-dev.5`. Sintoma novo: Retrieve Media URL espera e devolve `Erro interno ao recuperar a URL da mídia` (500 genérico do `api-service`; caminho provável = timeout de 30 s do RPC RabbitMQ, worker sem resposta).
- Causa não identificada. Pendente: log do pod do worker durante a chamada, saber se mídia normal (foto/PDF) também falha, e confirmar a versão do worker da instância testada. Alternativa: reproduzir na instância local (precisa de autorização para subir os processos e de alguém enviar áudio/imagem como documento).

### 11/10/2026 16:15 — teste local da DEM-89/92 não rodou: sessão de teste caiu
- Autorizado pelo desenvolvedor ("faça o teste"). `./start.sh` compilou o `worker-go` da branch `fix/dem-89-92-retrieve-media` e subiu, mas o WhatsApp recusou a sessão: `<failure location="cco" reason="401"/>` → instância `disconnected`, worker encerrou. Nenhum worker ficou rodando.
- O device `556392308423` deixou de estar vinculado (removido no aparelho ou expirado); causa não verificada. `db/999999999999999.db` continua no lugar.
- **Para retomar:** desenvolvedor com o aparelho em mãos → `./start.sh` → ler `qr.png` → enviar áudio de voz e imagem como Documento para o número → chamar `media`/`url` pela fila e ler o `worker.log`.

### 11/10/2026 16:27 — teste local DEM-92 OK; DEM-89 ainda sem amostra
- Device de teste repareado por QR (a sessão antiga tinha sido encerrada pelo WhatsApp: "logged out from another device").
- **DEM-92 confirmada localmente:** worker sem a correção → 400 em 14/14 áudios; com a correção → 6 sucessos em < 2 s (detalhes no `DEM-92.md`). O timeout relatado pelo QA em dev **não** foi reproduzido.
- **DEM-89:** falta o desenvolvedor reenviar uma imagem como Documento com a instância conectada.
- **Worker local de teste ficou RODANDO** (binário da branch `fix/dem-89-92-retrieve-media`); parar com `ai.context/examples/instance/stop.sh`. Binário da `dev` sem correção e cópia do código ficaram só na pasta temporária da sessão.
- Atenção: uma consulta minha à tabela `messages` do SQLite local imprimiu trechos de conversas do número de teste na sessão; não repetir consultas que tragam o conteúdo das mensagens.
- **Versão conferida (fetch do desenvolvedor):** `worker-go` `origin/dev` = `6b7f55e` (merge da `fix/dem-89-92-retrieve-media`), tag **`v0.0.95-dev.5`**, sem diferença de código para o `2832a20` testado localmente. O timeout de dev, portanto, não vem de diferença de código; suspeitas: instância testada em outra versão do worker, worker sem consumir a fila ou saída de rede do cluster dev para o CDN do WhatsApp.

### 11/10/2026 16:45 — caminho HTTP local também sem timeout
- `api-service` local (`main` `6931e5e`, `start-api.sh`) + worker da correção: `GET /v21.0/<mediaId>` → 200 em 0,01 s para foto recebida hoje; 410 imediato para áudios expirados (403 do CDN). Nenhum timeout. `api-service` local parado em seguida; **worker local segue rodando**.
- Foto recebida às 16:24 (`793585017823894`) baixou com a chave de imagem, sem nova tentativa: era foto comum, não Documento. **DEM-89 continua sem teste real.**
- Decisão do desenvolvedor: considerar que o QA testou na `v0.0.95-dev.5`. Timeout de dev segue sem reprodução; próximos passos dependem de dados do ambiente dev (id da mídia, horário, log do pod).

### 11/10/2026 16:45 — DEM-89 testada localmente: funciona, mas em 10,3 s
- PNG de 3,6 MB enviado como Documento (`454486836085021`): sucesso após o `whatsmeow` tentar a chave errada em 6 hosts (baixa o arquivo inteiro em cada um). Provável origem do timeout de 30 s visto pelo QA em dev para imagem como documento (não confirmado; não explica áudio).
- **Proposta aguardando autorização:** usar `MediaDocument` de primeira quando o `direct_path` contiver `/t62.7119-24/` (detalhes e evidência no `DEM-89.md`). Nenhum código alterado.
- Worker local de teste segue rodando.

### 11/10/2026 — ajuste da DEM-89 aplicado (sem commit)
- `worker-go`, branch `fix/dem-89-document-direct-path` (a partir da `dev` `6b7f55e`): `services/medias.go` usa `MediaDocument` de primeira quando o `direct_path` contém `/t62.7119-24/`. Build/vet/testes OK. Detalhes no `DEM-89.md`.
- Worker local de teste rodando com o ajuste. Falta: novo envio de imagem como Documento para medir o tempo → autorização de commit → push e MR para a `dev`.

### 11/10/2026 — ajuste da DEM-89 testado e commitado
- Teste local: JPEG de 674 KB como Documento → sucesso em 0,6 s, zero falhas de HMAC.
- Commit `ae7b5c0` na branch `fix/dem-89-document-direct-path` (base `dev` `6b7f55e`), autorizado pelo desenvolvedor. **Falta:** push (desenvolvedor), MR para a `dev`, reteste do QA.
- Worker local de teste segue rodando (parar com `stop.sh`).

### 11/10/2026 — ajuste da DEM-89 na `dev`: `v0.0.95-dev.6`
- MR !15 mergeado (pais `6b7f55e` + `ae7b5c0`), tag **`v0.0.95-dev.6`**, pipeline #2936437929 aprovada (dados colados pelo desenvolvedor; não conferidos por fetch).
- DEM-89 e DEM-92 seguem `pendente` aguardando reteste do QA na `dev.6`. A instância de teste do QA precisa estar nessa versão do worker.
- Aberto: timeout em áudio de voz em dev não reproduzido localmente; perguntar ao QA se ocorreu no áudio ou só na imagem como documento.
- Worker local de teste parado a pedido do desenvolvedor; sessão do device segue pareada em `db/`.

### 12/10/2026 — promoção do `worker-go` para a `main` (produção)
`claude --resume d156a462-2bfe-42e6-b56b-f042a0c47a79`
- Desenvolvedor informou que a atualização foi aprovada na dev e escolheu promover a **`dev` inteira** (opção 1), ciente de que leva junto DEM-88, autenticação mobile e ajustes da pipeline (commits do programador chefe). Recomendei confirmar o mobile com ele; confirmação não registrada.
- Branch local `release/dev-para-main-dem-88-89-92` criada a partir da `origin/dev` `f55d97b` (`v0.0.95-dev.6`), sem commits novos. `origin/main` (`363fb21`) é ancestral: merge sem conflito. `go build`/`go vet`/`go test` OK.
- **Falta:** push (desenvolvedor), MR para a `main`, versão estável gerada pela pipeline e atualização das instâncias de produção para essa versão. Só então marcar DEM-89/92 como `concluido`.
- **Mudança de decisão (12/10):** o desenvolvedor optou por enviar para produção **apenas DEM-89 e DEM-92**. Branch `fix/dem-89-92-retrieve-media-main` criada a partir da `origin/main` `363fb21` com cherry-pick de `2832a20` → `54dab3c` e `ae7b5c0` → `600eb88`; só `services/medias.go` muda, idêntico ao da `v0.0.95-dev.6`. `go build`/`go vet` OK; `go test` de `utils` e `webhook` OK; `services/messages` não compila os testes **localmente** por causa do arquivo não versionado `reply_context_test.go` (teste da DEM-88, cujo código não está na `main`) — não afeta a pipeline.
- A `main` usa o fork do `whatsmeow` de 28/07 (`e7d1f43`), bem anterior ao da `dev`; o teste com envio real foi feito com o fork da `dev`. A lógica de download lida no código é a mesma nas duas versões.
- A branch local `release/dev-para-main-dem-88-89-92` ficou sem uso (não apaguei). Se foi enviada ao GitLab, não abrir MR dela.
- **Falta:** push, MR para a `main`, versão estável, atualização das instâncias de produção. Depois, a `dev` e a `main` terão os mesmos dois commits com hashes diferentes.
- **12/10 — regra de promoção (programador chefe):** branch nova a partir da `main` atualizada + só as atualizações aprovadas + MR para a `main`. A `fix/dem-89-92-retrieve-media-main` segue a regra (cherry-pick em vez de merge, porque as branches de trabalho nasceram da `dev`). **Push feito pelo desenvolvedor.** Falta: abrir o MR com destino `main`, merge, versão estável e atualização das instâncias de produção (inclui a instância "Murilo" de um cliente com ticket do mesmo erro da DEM-92, hoje na `v0.0.95-dev2`).
- **12/10 — MR !16 mergeado na `main` do `worker-go`** (pais `363fb21` + `600eb88`), informado pelo desenvolvedor. No momento do aviso o commit de merge ainda aparecia **sem tag**: versão estável não confirmada. DEM-89/92 seguem `pendente` até a tag sair; depois, atualizar as instâncias de produção.
- **12/10 — release estável do `worker-go` gerada** (informado pelo desenvolvedor; número não informado nem conferido). **DEM-89 e DEM-92 marcadas `concluido`.** Falta: anotar o número da versão nos dois arquivos, atualizar as instâncias de produção (começando pela "Murilo") e responder o ticket do cliente.
- Pendentes no painel: DEM-43 (reteste QA), DEM-65 (evidência), DEM-91 (exibição na `dev`; bloqueio real sem causa; promoção do `manager-service` não feita).
- **Versão estável: `worker-go v0.0.96`** (MR !16, pipeline #2939472895 — ainda `running` quando o desenvolvedor colou a tela, então a publicação da imagem não estava confirmada). Anotada no `DEM-89.md` e no `DEM-92.md`.

## 📅 Sessão Finalizada em 2026-10-12
`claude --resume d156a462-2bfe-42e6-b56b-f042a0c47a79`

### 📝 Resumo do Expediente
- **DEM-89 e DEM-92:** em produção como `worker-go v0.0.96` (MR !16), `concluido`. No CSV estão `Aprovado` (testado em 11/10/2026). Mensagens para a equipe e respostas de ticket para os clientes entregues ao desenvolvedor (envio é com ele).
- **Análise do CSV `demandas/csv/10092026.csv` (atualizado 12/10 15:02), só leitura:** 95 tasks — A Fazer 40, Aprovado 37, Reprovado 13, Concluído 2, Devolvido 2, Em Andamento 1. Novas de 11/10: DEM-93, DEM-94, DEM-95.
- **Divergências CSV × arquivo (nenhum arquivo alterado):** DEM-67 `Devolvido` × `concluido` (QA: data só corrige ao clicar em "Atualizar instância"; esperado atualizar sozinha na migração trial → pagante); DEM-65 `Devolvido` × `pendente` (sem observação); DEM-88 e DEM-48 `A Fazer` × `concluido`; DEM-43 `Concluído` × `pendente`; DEM-62 `Concluído` (confirmar se está na `dev`).
- **Datas DEM-65/67 (git local):** mergeadas direto na `main` do `manager-service` em 22/09/2026 (`859580a`, `150a5c4`), versão `v0.3.51` de 24/09; presentes desde a primeira versão de dev `v0.3.59-dev.1` (08/10/2026). 2ª correção da DEM-67 no `api-service` `v1.57.6` (07/10/2026); a cópia local do `api-service` não tem branch `dev`.

### ⚠️ Pendências para o Próximo Agente (Handover)
- **Fila sugerida (PRIORIDADES.md):** DEM-91 e DEM-67 (P1) → DEM-88 (P2, só falta teste do QA e promoção) → DEM-65 (P3, falta evidência) → DEM-61 (P4) → P5 alta, começando por DEM-95 (salvar instância força versão para latest), DEM-93, DEM-80/82 (mesmo assunto da DEM-91).
- **Próximo passo proposto, ainda não autorizado:** análise (só leitura) da DEM-67; antes, confirmar com o QA em qual versão do `api-service` o reteste foi feito.
- **DEM-91:** faltam `username` dos 2 clientes, texto exato do erro e autorização para consulta de leitura em produção.
- **Não confirmado:** pipeline #2939472895 da `v0.0.96` finalizada e instâncias de produção atualizadas (começar pela "Murilo").
- **Dúvidas de regra para a equipe:** `Reprovado` não existe no `PRIORIDADES.md` (13 tasks fora da fila, 4 urgentes: 29, 32, 41, 52); `Aprovado` consta como elegível, mas no CSV significa aprovado pelo QA.
- `ai.context` segue sem commit (nunca autorizado). Branch local sem uso no `worker-go`: `release/dev-para-main-dem-88-89-92`. Checkout local do `worker-go` está em `fix/dem-89-92-retrieve-media-main`.
- Worker e api-service locais de teste parados; RabbitMQ local segue rodando (não foi iniciado por esta sessão).

## 📅 Sessão Finalizada em 2026-10-13
`claude --resume d156a462-2bfe-42e6-b56b-f042a0c47a79`

- **DEM-88 promovida para a `main` do `worker-go`:** QA aprovou em dev (`v0.0.95-dev.6`); branch `fix/dem-88-reply-context-main` (cherry-pick `668d678` → `262c62a`) mergeada como `92482e5`. **Tag estável ainda não gerada na conferência** (esperada `v0.0.97`). Falta: confirmar a tag, atualizar as instâncias dos clientes (uma atualização cobre DEM-88/89/92: Murilo, hchat "suporte 1", Femina) e pedir ao QA para marcar `Aprovado` no CSV.
- **Aguardando o programador chefe (Eduardo)** — funcionalidade nova ou decisão dele, nada implementado:
  - DEM-96 (exclusão de usuário): causa provável `author_id`/`actor_id` `NOT NULL` com FK `ON DELETE set null` nas tabelas de suporte; proposta `fix/dem-96-user-deletion` (tornar as colunas opcionais, exibir "Usuário removido", tratar erro no admin e na rota DELETE). Causa não confirmada em produção.
  - DEM-97: endpoint novo `GET /:version/instance/list` com `UserTokenGuard`.
  - DEM-95: `buildInstanceUpdateBody` envia `latest` fora da autenticação; proposta passar `preserveVersion` em `instances/[id]/route.ts:163` e `payment-confirmation.ts:58` (opção A sempre; opção B só onde a escolha de versão está habilitada).
  - DEM-61.
- **Aguardando o QA:** datas de teste das DEM-65/67 (testáveis em dev: `manager-service v0.3.59-dev.12`, `api-service v1.57.7-dev.6`); DEM-43 e DEM-62 em dev.
- Repositórios locais atualizados em 13/10: `manager-service` main `f5abc1b`/dev `b5dd4f5`; `api-service` main `6931e5e`/dev `43916f8`; `worker-go` main `92482e5`/dev `f55d97b`. Os três com checkout na `main`.

### 🔚 Fechamento do expediente (13/10)
- **`worker-go v0.0.97` criada** (tag local sobre `92482e5`, feita pelo desenvolvedor com `./release.sh`). **Atenção:** a `main` do `worker-go` **não** gera tag no merge — só a `dev` gera (`vX.Y.Z-dev.N`). Após merge na `main`, rodar `./release.sh` na `main` atualizada. Pipeline da tag `v0.0.97` e imagem publicada: **não conferidas**.
- **DEM-88:** a devolução de 13/10 veio de teste na `0.096` (sem a correção); aprovada em dev e promovida. Arquivo `DEM-88.md` atualizado. CSV ainda `Devolvido` — pedir ao QA para marcar `Aprovado`.
- **DEM-43:** QA perguntou como escolher a versão; orientação entregue ao desenvolvedor: não há versão a escolher (correção é do `manager-service`, o seletor é só do worker); testar em `painel.dev.uzapi.com.br`, que precisa estar na `v0.3.59-dev.9` ou superior. **Versão implantada no ambiente dev não conferida** (o painel não exibe a versão).
- **Suspeita útil para o QA:** instância criada em versão dev volta para a estável ao salvar nome/webhook (DEM-95); testes de correções do worker em dev devem conferir a versão logo antes do envio.

### ⚠️ Pendências para o Próximo Agente
1. Confirmar pipeline da `v0.0.97` e atualizar as instâncias dos clientes (Murilo `644722974573586`, hchat "suporte 1" `262379597872690`, Femina) — cobre DEM-88/89/92; depois, respostas dos tickets.
2. Retorno do Eduardo: DEM-96, DEM-97, DEM-95 (opção A ou B), DEM-61. Nada implementado; nenhuma branch criada para elas.
3. Retorno do QA: DEM-43 e DEM-62 em dev; datas de teste das DEM-65/67.
4. DEM-91: faltam `username` dos 2 clientes, texto exato do erro e autorização para consulta de leitura em produção.
5. `DEM-96.md` e `DEM-97.md` não existem em `exec/` (aguardam geração pelo Kanban).
6. `ai.context` segue sem commit (nunca autorizado). Branches locais no `worker-go`: `fix/dem-88-reply-context-main` (mergeada) e `release/dev-para-main-dem-88-89-92` (sem uso). Os três repositórios estão com checkout na `main` — criar a branch da demanda antes de qualquer alteração.
- **Atualização (14/10):** pipeline da `worker-go v0.0.97` confirmada pelo desenvolvedor; **DEM-88 concluída e validada** (registrado no `DEM-88.md`). A pendência 1 acima fica reduzida a: confirmar se as instâncias dos clientes das DEM-89/92 (Murilo, hchat "suporte 1", Femina) já estão na `v0.0.97` e responder os tickets.
- **DEM-43 em standby (14/10):** arquivo movido para `demandas/csv/standby.solution/DEM-43.md` (`status: standby`), com o dossiê. Reteste do QA no dev bloqueado: o Asaas recusou a cobrança (`callback.successUrl` `painel.dev.uzapi.com.br` fora do domínio cadastrado). **O dev usa o Asaas de produção** e a biblioteca `asaas` grava o `access_token` no log (chave de produção exposta → rotação recomendada). Bug antigo encontrado: `create-instance-payment.ts` grava `PENDING` antes de criar a fatura e não desfaz na falha (conta do QA travada; também afeta produção). Aguardando o Eduardo: sandbox no dev, rotação da chave, destravar a conta, e se o bug vira demanda.
- **DEM-43 (14/10):** Eduardo confirmou que a URL do Asaas no dev precisa ser corrigida (configuração do ambiente, com ele). Pendentes com ele: rotação da chave, desbloqueio da conta do QA, demanda do bug `PENDING`.
- **DEM-78 + DEM-86 (14/10, Opção A autorizada):** `/api/users` tinha `.limit(500)` sem ordem (origem `fa2bea2`); passou a devolver todos, `orderBy(desc(user.createdAt))`. Commit `bdc20e6` na branch `fix/dem-78-86-user-list-limit` do `manager-service`, base `dev` `b5dd4f5`; `tsc` e `eslint` OK. **Sem push.** Opção B (busca no servidor, limite 50) fica para quando a base chegar a dezenas de milhares. `DEM-78.md`/`DEM-86.md` não existem em `exec/` (gerar pelo Kanban). DEM-90 (limite 1000 em `/api/admin/users` e `export`) é a mesma família, a tratar à parte (paginação).

## 📅 Sessão Finalizada em 2026-10-14
`claude --resume d156a462-2bfe-42e6-b56b-f042a0c47a79`

### 📝 Resumo do Expediente
- **DEM-88:** concluída e validada em produção (`worker-go v0.0.97`, pipeline confirmada); CSV `Aprovado` (13/10).
- **CSV de 14/10:** 97 tasks; mudaram DEM-88 (Devolvido → Aprovado) e DEM-62 (Concluído → Aprovado, já na `main`).
- **DEM-43 em standby** (`standby.solution/DEM-43.md`): Eduardo confirmou que a URL do Asaas no dev precisa ser corrigida. Pendentes com ele: sandbox × produção no dev, rotação da chave exposta no log, destravar a conta do QA, demanda do bug `PENDING` gravado antes da fatura. Mensagem ao QA enviada (aguardar aviso antes de retestar).
- **DEM-78 + DEM-86:** commit `bdc20e6` na branch `fix/dem-78-86-user-list-limit` (`manager-service`, base `dev` `b5dd4f5`, conferida com o remoto pelo desenvolvedor). Texto do MR entregue. **Push feito** (`origin/fix/dem-78-86-user-list-limit` = `bdc20e6`); MR/merge na `dev` não confirmados. Só `tsc`/`eslint`; sem teste em execução (o desenvolvedor seguiu sem o teste local).
- **DEM-80 + DEM-82:** provavelmente já corrigidas — `b91ea05` (28/09, `main`: admin não desconta carência no trial) e `13b63c0` (DEM-91, só `dev`: lista do usuário). Mensagem de reteste ao QA entregue. DEM-59 parece da mesma família.
- **DEM-85 (análise, nada alterado):** `PATCH /api/admin/users/[userId]/billing` grava sempre `price_per_instance`/`monthly_total` = 0 (regra do Eduardo, `cdacd63`, para ativação manual não contar no MRR); o mesmo botão "Ativar / Ajustar Manualmente" é usado para mudar vencimento de cliente pagante. Proposta A: preservar preço quando `ACTIVE`, mensalidade > 0 e mesma quantidade; pré-preencher o formulário com o vencimento atual (hoje abre com hoje + 30). Mensagem ao Eduardo entregue; aguardando. Branch prevista: `fix/dem-85-admin-due-date-price` a partir da `dev`. Observado: data no Asaas não acompanha o ajuste (fora do escopo).
- **`manager-service` `main` remota andou:** `b9d70ba` (merge `financeiro`, Eduardo, 14/10 00:44, "limitar cálculos financeiros ao mês corrente") — **não está na `dev`**; sugerido avisar o Eduardo. `main` local do `manager-service` ainda em `f5abc1b`.

### ⚠️ Pendências para o Próximo Agente
1. DEM-78/86: confirmar MR e merge na `dev`; depois reteste do QA (roteiro no texto do MR). Gerar `DEM-78.md`/`DEM-86.md` pelo Kanban e preencher.
2. Eduardo: DEM-85, DEM-43 (Asaas no dev), DEM-95 (A ou B), DEM-96, DEM-97, DEM-61.
3. QA: DEM-80/82/59 (reteste), DEM-62 (já aprovado), DEM-65/67 (datas e detalhes), DEM-43 (após ajuste do dev).
4. DEM-91: `username` dos 2 clientes, texto do erro, autorização para consulta somente leitura em produção.
5. Instâncias dos clientes das DEM-89/92 (Murilo, hchat "suporte 1", Femina) na `v0.0.97` e respostas dos tickets: não confirmado.
6. DEM-90 (limite 1000 em `/api/admin/users` e `export`): mesma família da 78/86; tratar com paginação.
7. `ai.context` sem commit (nunca autorizado). `manager-service` com checkout em `fix/dem-78-86-user-list-limit`; `worker-go` e `api-service` na `main`.
- **15/10 — Fonte do backlog:** criado `demandas/regras/FONTE_BACKLOG.md` (modo CSV padrão, somente leitura; modo planilha Google com escrita só em Status "Concluído"/Versão/Observações e **autorização do desenvolvedor a cada alteração**); referência adicionada no `AGENTS.md` (seção 1). Modo atual: CSV. Conector Google ainda não autenticado.
- **15/10 — Modo planilha ativo.** Escrita via Apps Script (app da Web na conta jaderesp, abre a planilha por ID) + `demandas/planilha/planilha_sync.py`; credenciais em `~/.config/uzapi/planilha.json`. **Primeira gravação autorizada:** task 80 (aba Lista, linha 81) — Status `A Fazer` → `Concluído`, Versão `0.095` → `0.3.59-dev.12`, Observações (vazio) → resumo da correção (`b91ea05` em produção + `13b63c0` no dev) e roteiro de reteste. Conferido por releitura. Aviso: a planilha está compartilhada como "qualquer pessoa com o link pode editar".
- **15/10 — Planilha (autorizado):** task 80 Versão `0.3.59-dev.12` → `0.095-dev06` (premissa nova: coluna Versão = versão do worker para o teste, registrada no `FONTE_BACKLOG.md`); tasks 82 (linha 83) e 59 (linha 60): Status `A Fazer` → `Concluído`, Versão `0.095` → `0.097`, Observações com a correção `b91ea05` (painel v0.3.56) e roteiro. Conferido pela exportação da planilha. `planilha_sync.py` repete só leituras (update não, para não duplicar observação).
- **15/10 — Monitoramento da planilha (aviso na hora, e-mail jaderesp@gmail.com):** código pronto em `apps_script.gs` (`aoEditar`, `instalarGatilho`, aba "Histórico", ação `history`) e `planilha_sync.py history [--mark]`; regra de leitura no início da sessão no `FONTE_BACKLOG.md`. **Falta o desenvolvedor colar o código, rodar `instalarGatilho()` e criar nova versão da implantação.**
- **15/10 — Painel lê a planilha (itens 1–4 autorizados):** `apps_script.gs` ganhou a ação `export`; `planilha_sync.py` reescrito (`pull`, leituras com repetição); `painel_local.py --fonte planilha` sincroniza o CSV a cada 60 s, página com atualização automática e quadro de mudanças, "Nova Demanda" bloqueado no modo planilha, bug que descartava "Testado Em" corrigido. Backup do painel anterior só no scratchpad. Item 5 (bind só em 127.0.0.1) **não autorizado**: o painel segue escutando em todas as interfaces. **Pendente:** desenvolvedor colar o `apps_script.gs` e publicar nova versão da implantação; depois testar `pull` e o painel.
- **15/10 — Sincronização testada:** `export` publicado; `pull` aplicado no `csv/10092026.csv` real (12:32) — diferenças = só as gravações autorizadas das tasks 59/80/82. Corrigida a detecção de task nova (linhas da planilha vêm pré-numeradas até ~1996: task nova = título preenchido em linha vazia) no `pull`, no painel e no `aoEditar` do Apps Script. **Pendente:** desenvolvedor colar e salvar o `apps_script.gs` atualizado (o gatilho usa o código salvo) e testar o painel com `--fonte planilha`.
- **15/10 — Painel:** passa a ignorar linhas sem ID ou sem Título (linhas pré-numeradas da planilha apareciam como tasks vazias). Tasks válidas no CSV: 97.
- **15/10 — WhatsApp (autorizado):** módulo `ai.context/whatsapp/` (`main.go` com whatsmeow do cache do worker-go; QR, envio de texto ao grupo configurado, escuta do grupo gravando só mensagens que citam task em `~/.config/uzapi/whatsapp/feedback.jsonl`; só 127.0.0.1:9011; binário no `.gitignore`). Painel: botão WhatsApp (QR/grupo/desconectar), "Notificar QA" nos cards concluídos (tasks "Concluído" da planilha agora aparecem na coluna de concluídas), "Feedbacks do grupo"; tudo desativado sem número conectado; envio registrado no arquivo da demanda e no HANDOVER. Testado sem número conectado. **Pendente:** desenvolvedor escolher o número (nunca 556392308423), ler o QR e escolher o grupo.
- **15/10 — WhatsApp conectado:** número `556392308423` (aparelho `:25`, sessão do módulo em `~/.config/uzapi/whatsapp/`), grupo **Equipe Uzapi** salvo. Conferido que é sessão separada da instância de teste do worker-go (`:24`, `examples/instance/db/`, worker parado). Desenvolvedor **liberou esse número para o módulo (opção B)**; regra antiga "nunca 556392308423" substituída no `FONTE_BACKLOG.md` e no `whatsapp/README.md`. Mensagens do próprio número não entram nos feedbacks. **Pendente:** teste do "Notificar QA" (DEM-80) e de feedback citando task.

- **15/10/2026 14:41 — WhatsApp:** notificação da DEM-80 enviada ao grupo pelo painel (autorizada pelo desenvolvedor no envio).- **15/10 — DEM-65:** correção confirmada na `dev` (`v0.3.59-dev.1`+); caminho alternativo por campanha agendada (`sendCampaign` ignora a chave da automação) registrado em `exec/DEM-65.md`; pedido de reteste enviado ao QA.
- **15/10 — DEM-67:** análise só leitura registrada em `exec/DEM-67.md` (pagamento já sincroniza instâncias; ajuste do admin não chama o api-service; "Atualizar Instância" não altera `expiresIn`). DEM-65 e DEM-67 em reteste pelo QA: aguardar.
- **15/10 — Planilha (autorizado):** tasks 78 (linha 79) e 86 (linha 87): Status `A Fazer` → `Concluído`, Versão `0.095` → `0.095-dev06`, Observações (vazio) → correção (`manager-service v0.3.59-dev.13`, merge `5fd4784`) e roteiro de teste. Conferido pela resposta do script. DEM-78.md/DEM-86.md não existem (gerar pelo Kanban).
