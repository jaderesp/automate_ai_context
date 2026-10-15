---
id: DEM-73
status: concluido
data_ativacao: 2026-09-22 15:26:57
data_conclusao: 2026-09-22 16:02:00
modulo: API
---

# 🚀 Histórico de Execução: Não gera evento de button reply no iphone

## 📌 Resumo do Problema
Ao clicar em um botão de resposta (button reply) usando um WhatsApp de iPhone, o webhook do cliente **não recebia nenhum payload**, inviabilizando automações para contatos iOS. No Android, o payload era gerado normalmente.

## 🛠️ Solução Adotada

### Diagnóstico (Causa Raiz)
O clique em botão é empacotado pelo WhatsApp em **tipos protobuf diferentes conforme a plataforma do cliente**, e o `worker-go` tratava apenas parte deles em `webhook/createContent.go`:

| Tipo protobuf | Plataforma observada | Situação antes da correção |
|---|---|---|
| `TemplateButtonReplyMessage` | Android | ✅ tratado (`createContent.go:577`) |
| `ListResponseMessage` | seleção de lista | ✅ tratado (`createContent.go:597`) |
| `ButtonsResponseMessage` | **iPhone (confirmado em teste real)** | ❌ removido no commit `8dbc145` (23/12/2025) |
| `InteractiveResponseMessage` | native flow (clientes mais novos) | ❌ nunca tratado |

Qualquer tipo fora do switch caía em `default` → `result["type"] = "unknown"` → `BuildMessagePayload` retornava `nil` (`payloadBuilder.go:173-178`) → `events.go:225-228` abortava o envio do webhook **silenciosamente**. A api-service não filtra nada (apenas documenta o contrato); o descarte era 100% no worker.

**Evidências externas (tulir/whatsmeow):**
- PR #1235 (aberto): medido em device real que taps em botões native-flow voltam como `InteractiveResponseMessage` com o shape de `<biz>` que o fork `edupoli` já emite.
- PR #1221 (aberto): clientes reais enviam `ButtonsResponseMessage`/`ListResponseMessage` sem nó `<biz>` — confirma que são variantes legítimas de resposta.
- Issue #1144: `quick_reply` (o tipo que o worker envia) renderiza em iOS e Android.

### Correção Aplicada (Opção A — tratar todas as variantes)
1. **`webhook/createContent.go` — novo case `ButtonsResponseMessage`**: `button_reply` com `GetSelectedButtonID()` / `GetSelectedDisplayText()` + `context` (stanzaID/participant). Código equivalente existia no branch `origin/refactor` (commit `7be26a5`), removido no `8dbc145`.
2. **`webhook/createContent.go` — novo case `InteractiveResponseMessage`**: extrai `id`/`display_text` do `ParamsJSON` do `NativeFlowResponseMessage` via helper novo `parseNativeFlowResponse`, com fallback para `Body.Text` quando o JSON está vazio/inválido. Mantém o mesmo contrato público (`interactive.type = "button_reply"`).
3. **`types/messageTypes.go`**: novo campo `InteractiveResponseMessage` em `MessageContent` (auditoria/persistência no SQLite).
4. **`utils/NormalizeHistorySync.go`**: preenchimento do novo campo em `NormalizeMessage` e `NormalizeWebMessageInfo`.
5. **Testes**: `webhook/createContent_test.go` com 7 subtestes (parsing das variantes + teste de integração do `BuildMessagePayload` reproduzindo o caminho que falhava).

### Análise de Impacto
- Mudança aditiva e isolada ao endpoint `messages`/webhook; `TemplateButtonReplyMessage` e `ListResponseMessage` intactos (regressão coberta por teste).
- **A Opção mínima (só `InteractiveResponseMessage`) NÃO resolveria o bug** — comprovado no teste real: o iPhone testado envia `ButtonsResponseMessage`.

## 🧪 Teste Prático e Homologação

### 1) Testes unitários/integração (executados e aprovados)
- **Comando:** `CGO_ENABLED=1 go test -v ./webhook/...`
- **Resultado:** `PASS` — 7 subtestes:
  - `TestParseMessageContentInteractiveResponse`: native flow com `ParamsJSON`; `ParamsJSON` inválido → fallback `Body.Text`; `ButtonsResponseMessage` legado.
  - `TestParseMessageContentTemplateButtonReply`: regressão Android.
  - `TestBuildMessagePayloadButtonReply`: payload **não-nulo** (antes retornava `nil`) + JSON contém `button_reply`, `id` e `title`.
- **Verificações:** `gofmt` limpo, `CGO_ENABLED=1 go build ./...` OK, `CGO_ENABLED=1 go vet ./...` OK.

### 2) Teste E2E real com iPhone (passo a passo executado)
**Ambiente:** worker-go local compilado da branch `fix/dem-73-button-reply-ios` + RabbitMQ/Postgres locais (Docker) + listener HTTP local para capturar o webhook.

1. **Listener de webhook:** script Python em `127.0.0.1:8099` gravando os POSTs em `/tmp/opencode/dem73/webhook_received.log`.
2. **Pairing:** worker subido com `PHONE_NUMBER_ID=999999999999999` (SQLite virgem) e `AUTH_METHOD=QRCode`; QR exibido no terminal e capturado via webhook de autenticação. Device pareado: `556392308423:19@s.whatsapp.net` (slot novo, sem afetar o device de produção). Conexão confirmada: `isAuthenticated=true deploymentStatus=connected`.
   - *Nota:* a primeira tentativa usou o SQLite existente `616846729449965.db` e recebeu `401: logged out from another device` (a instância estava ativa em outro ambiente); o handler de `LoggedOut` deletou a sessão local (comportamento de projeto).
3. **Disparo:** publicação direta via `pika` na exchange `API-WhatsApp`, routing key `999999999999999`, payload `interactive/button` com botão `quick_reply` (`id=btn_dem73_1`, `title=Confirmar`) para o iPhone `556392477769`.
   - Envio confirmado: `Mensagem interativa enviada com sucesso` — messageID `3EB01DF5409B25F5517440` (15:57:25), com nó `<biz><interactive type="native_flow" v="1"><native_flow name="mixed" v="9"/></interactive></biz>`.
4. **Clique no iPhone:** contato tocou "Confirmar" às 15:58:52 → mensagem `2AA507148F4E31B76B7D`.
5. **Retorno no webhook (homologado) — payload completo capturado no listener:**
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "337265591228877",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "556392308423",
              "phone_number_id": "999999999999999"
            },
            "contacts": [
              { "profile": { "name": "Leandro André" }, "wa_id": "556392477769" }
            ],
            "messages": [
              {
                "context": {
                  "from": "66650040742069",
                  "id": "3EB01DF5409B25F5517440"
                },
                "from": "556392477769",
                "id": "2AA507148F4E31B76B7D",
                "interactive": {
                  "button_reply": { "id": "btn_dem73_1", "title": "Confirmar" },
                  "type": "button_reply"
                },
                "isGroup": false,
                "timestamp": "1790103532",
                "type": "interactive"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

**Padrão do retorno (iPhone → protobuf `ButtonsResponseMessage` → webhook Cloud API):**

| Campo no webhook | Origem no protobuf | Observação |
|---|---|---|
| `messages[].type` | fixo pelo parser | `"interactive"` |
| `messages[].interactive.type` | fixo pelo parser | `"button_reply"` |
| `messages[].interactive.button_reply.id` | `ButtonsResponseMessage.selectedButtonID` | mesmo `id` enviado no botão (`btn_dem73_1`) |
| `messages[].interactive.button_reply.title` | `ButtonsResponseMessage.SelectedDisplayText` | texto exibido (`"Confirmar"`) |
| `messages[].context.id` | `contextInfo.stanzaID` | ID da mensagem do botão (`3EB01DF5409B25F5517440`) |
| `messages[].context.from` | `contextInfo.participant` | JID do remetente sem sufixo (`@lid` removido) |
| `messages[].from` / `contacts[].wa_id` | remetente | número do contato que clicou |
| `messages[].id` | `Info.ID` | ID da mensagem de resposta (`2AA507148F4E31B76B7D`) |
| `messages[].timestamp` | `Info.Timestamp` | Unix em string |
| `messages[].isGroup` | `Info.IsGroup` | `false` em conversa privada |

> Os mesmos campos são produzidos para `TemplateButtonReplyMessage` (Android) e `InteractiveResponseMessage` (native flow) — o contrato público é idêntico; só o tipo protobuf de entrada muda.
6. **Persistência no SQLite (auditoria):** linha `2AA507148F4E31B76B7D` gravada com o campo **`ButtonsResponseMessage`** preenchido (`selectedButtonID: btn_dem73_1`, `SelectedDisplayText: "Confirmar"`, `contextInfo.stanzaID` = ID da mensagem enviada). **Confirmou-se que o iPhone envia `ButtonsResponseMessage`** — variante que havia sido removida do worker.

### 3) Teste E2E real com Android (regressão validada)
**Objetivo:** confirmar que o Android continua enviando `TemplateButtonReplyMessage` e que o fluxo ponta-a-ponta não regrediu com a mudança aditiva.

1. **Ambiente:** mesmo setup do teste iOS (worker local da branch + listener em `127.0.0.1:8099` + device pareado `556392308423:19`).
2. **Disparo:** botão `quick_reply` (`id=btn_dem73_android`, `title=Confirmar`) para o Android `5516997141457` — messageID `3EB041C0C9BA7AB0670A32` (16:59:14).
3. **Clique no Android** às 16:59:23 → mensagem de resposta `A550CED35014A58A13D07A76ADD41504` (contato "Jader Jmsoft").
4. **Retorno no webhook — payload completo capturado no listener:**
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "337265591228877",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "556392308423",
              "phone_number_id": "999999999999999"
            },
            "contacts": [
              { "profile": { "name": "Jader Jmsoft" }, "wa_id": "5516997141457" }
            ],
            "messages": [
              {
                "context": {
                  "from": "66650040742069",
                  "id": "3EB041C0C9BA7AB0670A32"
                },
                "from": "5516997141457",
                "id": "A550CED35014A58A13D07A76ADD41504",
                "interactive": {
                  "button_reply": { "id": "btn_dem73_android", "title": "Confirmar" },
                  "type": "button_reply"
                },
                "isGroup": false,
                "timestamp": "1790107163",
                "type": "interactive"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```
**Mapeamento (Android → protobuf `TemplateButtonReplyMessage` → webhook):** `button_reply.id` ← `selectedID`; `button_reply.title` ← `selectedDisplayText`; `context.id` ← `contextInfo.stanzaID`; `context.from` ← `contextInfo.participant` (sem `@lid`); `from`/`wa_id` ← número do contato. Contrato idêntico ao do iPhone — muda apenas a origem protobuf.
5. **Persistência no SQLite:** campo **`TemplateButtonReplyMessage`** preenchido (`selectedID=btn_dem73_android`, `selectedDisplayText="Confirmar"`, `selectedIndex=0`), comprovando a variante Android.

**Resultado comparativo (device real):**

| Plataforma | Tipo protobuf recebido | Webhook gerado |
|---|---|---|
| iPhone | `ButtonsResponseMessage` | ✅ `button_reply` (id/title) |
| Android | `TemplateButtonReplyMessage` | ✅ `button_reply` (id/title) |

**Conclusão da homologação:** bug resolvido de ponta a ponta (envio → clique iOS → webhook com `button_reply` → persistência) e **regressão Android validada com device real**; o contrato do webhook é idêntico nas duas plataformas.

## 📂 Arquivos Modificados
- `worker-go/webhook/createContent.go`
- `worker-go/webhook/createContent_test.go` (novo)
- `worker-go/types/messageTypes.go`
- `worker-go/utils/NormalizeHistorySync.go`

### Commit
- **worker-go** — branch `fix/dem-73-button-reply-ios` — commit `434ddb4`: `fix(dem-73): tratar ButtonsResponseMessage e InteractiveResponseMessage no webhook`
