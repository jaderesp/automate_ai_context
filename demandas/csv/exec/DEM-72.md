---
id: DEM-72
status: concluido
data_ativacao: 2026-09-24 09:32:02
data_conclusao: 2026-10-06 19:08:00
modulo: API
---

# 🚀 Histórico de Execução: Mensagem enviada pela API

## 📌 Resumo do Problema
Foi identificado um problema ao consultar mensagens enviadas pela API por meio do endpoint /chat.
Quando uma mensagem é enviada pelo próprio número utilizando a API e, posteriormente, consultada através do endpoint /chat, a requisição é processada com sucesso (status: success), porém o conteúdo da mensagem não é retornado.
No retorno recebido, o campo IsFromMe está definido como true, indicando que a mensagem foi enviada pelo próprio número, entretanto o objeto Message é retornado vazio.

## 🐛 Causa Raiz Descoberta
Após a auditoria no microserviço `worker-go` (responsável pela ponte com o WhatsApp e a persistência em banco SQLite), constatou-se que as mensagens com `IsFromMe: true` ecoadas de volta pelo servidor do WhatsApp vêm empacotadas em um envelope oculto do protocolo chamado `DeviceSentMessage`. A função responsável pela formatação da mensagem para o banco (`NormalizeMessage`) tentava iterar pelas propriedades do escopo exterior (ex: `ExtendedTextMessage`, `ImageMessage`) e recebia retornos NULOS, gravando um registro vazio no SQLite. Como o endpoint `/chat` apenas serve o que está no banco, a mensagem aparecia nula/em branco para os clientes.

## 🛠️ Solução Adotada
Implementamos uma camada de **Unwrap** (desempacotamento) condicional nas funções `NormalizeMessage` e `NormalizeWebMessageInfo` dentro do arquivo `worker-go/utils/NormalizeHistorySync.go`.
O código agora detecta se `msg.Message.GetDeviceSentMessage() != nil` e, caso positivo, extrai preventivamente a mensagem interna original via `GetMessage()`. Dessa forma, o parser de mapeamento (que constrói a struct para persistência JSON na coluna `data` da tabela `messages`) consegue varrer corretamente o tipo original (`GetExtendedTextMessage`, `GetImageMessage`, etc.) e popular o corpo completo.

## 🧪 Teste Prático e Homologação
Um ambiente de teste unitário focado `TestNormalizeMessage_DeviceSentMessage` foi concebido artificialmente mockando o envio de uma `DeviceSentMessage` que carrega a string "Teste de mensagem via API". O framework de testes Go atestou rigorosamente a eficácia do desempacotamento (`PASS - 0.028s`).
A correção foi integrada na *branch* `fix/dem-72-chat-empty-message` e mesclada de volta à `main`.

## 📂 Arquivos Modificados
- `worker-go/utils/NormalizeHistorySync.go` (Unwrap logic adicionada)
- `worker-go/utils/NormalizeHistorySync_test.go` (Arquivo de asserção unitária)


## 🚨 Fase 2: O Problema Específico da API (Hotfix e Race Condition)

Após a primeira correção (`DeviceSentMessage`), o usuário relatou que mensagens enviadas pelo APP passaram a retornar o conteúdo perfeitamente, mas mensagens enviadas **pela API da UzAPI** continuavam retornando `{}`.

### 🐛 Causa Raiz da API:
1. **Condição de Corrida (Race Condition):** O código original usava `UpsertMessage` de forma indiscriminada. Se a requisição HTTP da API demorasse milissegundos a mais do que o WebSocket do `HistorySync` para responder, a API sobrescrevia a mensagem completa gravada pelo Webhook com um registro "vazio" (`stub`) contendo apenas o ID e um Timestamp em formato Unix bruto (ex: `1790955157`).
2. **Ausência do Evento de Sincronização:** Diferente das mensagens enviadas pelo aplicativo mobile do WhatsApp (APP), o servidor do WhatsApp **não efetua o echo do evento de sincronização do corpo da mensagem para a própria sessão que a originou via API**. Ou seja, a API ficaria esperando eternamente por um evento do WebSocket que nunca viria para preencher o corpo vazio, mantendo a coluna permanentemente como `Message: {}`.

### 🛠️ Solução do Hotfix Adotada:
1. Em `worker-go/database/messageStore.go`, implementamos o `InsertOnlyMessage` (`INSERT OR IGNORE`), garantindo que "stubs" vazios da API jamais esmaguem dados ricos recebidos via WebSocket do celular.
2. Em `worker-go/services/factory.go`, injetamos um **Interceptador de Payload**: assim que a API aciona o envio, nós injetamos manualmente o nó `text.body` vindo do JSON HTTP diretamente para dentro da estrutura (`Conversation`) do banco SQLite, cobrindo o buraco deixado pela ausência do `HistorySync`. Adicionalmente, padronizamos o `Timestamp` do *stub* para aderir rigorosamente ao formato **ISO 8601** (`time.RFC3339`), mantendo o espelhamento estrito com os eventos normais do APP.

### 🧪 Homologação e Validação:
Desenvolvemos suítes de testes unitários validando a eficácia anti-colisão do SQLite e scripts independentes (bypassing the PostreSQL infrastructure) usando sessões geradas por *Pairing Code* injetando payloads nativamente. Como resultado irrefutável, comprovou-se que `Conversation` preenche o JSON e a interface recebe sua formatação e corpo textual. A intervenção completa foi comitada com sucesso na branch `fix/dem-72-hotfix-race-condition`.


## 🔁 Fase 3: Releitura da solução e substituição pela Opção B (2026-10-02)

> **Estado:** código aplicado e validado localmente na branch `fix/dem-72-hotfix-race-condition` do `worker-go`. **Commit `4c33d5f` (12 arquivos de código; arquivos de teste fora do git a pedido do desenvolvedor), sem push e sem release. E2E em aparelho executado em 2026-10-02 (ver "E2E em aparelho real").** O hotfix da Fase 2 nunca chegou a produção.

### 🔎 Revisão do diagnóstico das Fases 1 e 2
1. **Origem real do `Message: {}`:** o commit `fa587a3` (DEM-66) passou a gravar em `services/factory.go` (`ExecuteMessageFunction`) um registro na tabela SQLite `messages` (`id TEXT PRIMARY KEY`, `data JSON`) contendo apenas `Info` (ID, Chat, Sender, IsFromMe, IsGroup, Timestamp) e `Message` vazio, para o revoke localizar o chat pelo `messageId`. Antes da DEM-66 mensagens enviadas pela API não eram gravadas. O endpoint `/chats` (`action: get`, `services/chats/queries.go:85`) apenas devolve a coluna `data`, logo retornava o corpo vazio.
2. **Unwrap da Fase 1 é redundante para eventos ao vivo:** o fork do whatsmeow já desempacota `DeviceSentMessage` em `events.Message.UnwrapRaw()` antes de despachar o evento (`message.go:306` e `message.go:1124` do fork `edupoli/whatsmeow@e7d1f434cfe7`). O código da Fase 1 em `utils/NormalizeHistorySync.go` é inofensivo e foi mantido.
3. **A "race condition" da Fase 2 não ocorre no envio pela API:** `client.SendMessage` não despacha `events.Message` para o próprio dispositivo (`send.go` não chama `dispatchEvent`), portanto nenhum registro completo chega antes do registro gravado pelo worker. O único outro gravador do mesmo ID é o `HistorySync`, que usa `UpsertMessage`.

### 🐛 Lacunas da Fase 2 (motivo da substituição)
- Preenchia o corpo **somente para `msgType == "text"`**; imagem, vídeo, áudio, documento, sticker, localização, contato, enquete e interativo continuavam com `Message: {}`.
- Gravava o texto em `Conversation`, enquanto o envio real é um `ExtendedTextMessage`; perdia `ContextInfo` (resposta citada), preview de link e menções.
- `factory.go` chamava `messages.ValidateJID` uma segunda vez após o envio, disparando um segundo `IsOnWhatsApp` (usync) por mensagem enviada a usuário; em caso de falha dessa consulta a mensagem não era gravada, sem log.
- O erro de gravação era descartado (`_ = database.InsertOnlyMessage(...)`).

### 🛠️ Solução Adotada (Opção B — gravar a mensagem real enviada)
1. **`services/messages/helpers.go`**
   - `SendAndStore(client, jid, message, extra...)`: chama `client.SendMessage` e, em caso de sucesso, grava no SQLite o **mesmo `*waE2E.Message` enviado** via `database.InsertOnlyMessage`. Erro de gravação é logado e não interrompe o envio. O JID já resolvido pela função de envio é reaproveitado (sem segunda consulta `IsOnWhatsApp`).
   - `buildSentMessage(chat, sender, message, id, timestamp)`: monta um `events.Message` (`IsFromMe: true`, `IsGroup` pelo server `g.us`, `Sender = client.Store.ID.ToNonAD()`), aplica `UnwrapRaw()` (mesmo desempacotamento de viewOnce/ephemeral das mensagens recebidas) e passa pelo `utils.NormalizeMessage` já existente. Resultado: registro no **mesmo formato** das mensagens recebidas/enviadas pelo app. Timestamp em RFC3339 UTC; se vier zerado, usa o horário atual.
   - `sentMessageType(message)`: preenche `Info.Type` com a mesma classificação do whatsmeow (`text`, `media`, `poll`).
2. **Funções de envio** (`text.go`, `image.go`, `video.go`, `audio.go`, `document.go`, `sticker.go`, `location.go`, `contact.go`, `poll.go`, `interactive.go`): a chamada principal `client.SendMessage(...)` foi trocada por `SendAndStore(...)`. `revoke.go` e `reaction.go` não gravam, como antes.
3. **`services/factory.go`**: removido todo o bloco de gravação de `ExecuteMessageFunction` (volta a ser `return messageFunc(client, data)`) e os imports `database`, `config`, `types` e `time`.
4. **`database/messageStore.go`**: `InsertOnlyMessage` (`INSERT OR IGNORE`) mantido e usado pelo helper.

**Efeitos adicionais:** mensagens de mídia enviadas pela API passam a ter `URL`, `DirectPath`, `MediaKey`, `FileEncSHA256` e `FileSHA256` gravados (binários em base64), o que também permite a `GetMessageByMediaKey` (`services/medias.go:139`) encontrá-las. O revoke por `messageId` (DEM-66) continua funcionando, pois `Info.Chat`/`Info.IsFromMe` seguem gravados.

**Mudança de comportamento:** envios de **edição** (`editMessageID`) deixam de gerar registro próprio no SQLite (antes geravam um registro vazio com o ID da edição). O registro da mensagem original não é atualizado com o novo conteúdo.

**Limitação conhecida:** registros vazios já gravados nos SQLite das instâncias (DEM-66 em diante) não são recuperáveis, pois o corpo nunca foi persistido.

### 🧪 Teste Prático e Homologação (Fase 3)
Validação executada em 2026-10-02 no `worker-go` (pacotes exceto a raiz, que contém os scripts soltos `test_send.go`/`generate_json.go` não versionados e com `main` duplicado):
- `go build` (com CGO) e binário `./cmd/main.go`: OK.
- `gofmt -l services/factory.go services/messages`: sem pendências.
- `go vet`: sem apontamentos.
- `go test -count=1`: `worker/database`, `worker/services/messages`, `worker/utils`, `worker/webhook` — todos `ok`.
- Novo `services/messages/helpers_test.go`:
  - `TestBuildSentMessage` (4 subtestes): texto preserva `ExtendedTextMessage` + `ContextInfo`; imagem preserva `MediaKey`/`DirectPath` e marca `Type: media`; viewOnce é gravado desempacotado; enquete marca `Type: poll` e timestamp zerado cai no horário atual.
  - `TestBuildSentMessage_RoundTripSQLite`: grava em SQLite em memória e confere que o JSON da coluna `data` traz `fileName` e `mediaKey` em base64, e que `GetMessageByID` devolve `Info.Chat`/`IsFromMe` (caminho do revoke).

#### E2E em aparelho real (2026-10-02, 17:28–17:30 BRT)

**Ambiente**
- Worker compilado do commit `4c33d5f` (`CGO_ENABLED=1 go build ./cmd/main.go`), rodando local e isolado: `PHONE_NUMBER_ID=999999999999999`, `PORT=3011`, SQLite e mídias em pasta temporária da sessão, RabbitMQ e Postgres locais (containers `rabbitmq` e `postgres-uzapi`), exchange `API-WhatsApp`, webhooks desligados.
- Device pareado por QRCode: `556392308423:22@s.whatsapp.net` (Android). O HistorySync do pareamento gravou 316 mensagens no SQLite de teste.
- Disparo: script Python (`pika`) publicando na exchange com `routing_key = 999999999999999`, no mesmo envelope do `api-service` (`rabbitmq.service.ts`, `send()`): `{"pattern": <endpoint>, "data": {...}}`, com `reply_to` + `correlation_id` para receber a resposta do worker. O `api-service` não participou do teste (payload publicado direto na fila), e o `waMessageID` não foi enviado (ID gerado pelo whatsmeow).

**Payloads enviados (campo `data`)**
```json
{"endpoint":"messages","type":"text","to":"<destino>","text":{"body":"[DEM-72 E2E 17:28:47] texto enviado pela API","preview_url":false}}
{"endpoint":"messages","type":"image","to":"<destino>","image":{"link":"https://www.gstatic.com/webp/gallery/1.jpg","caption":"[DEM-72 E2E 17:28:47] imagem pela API"}}
{"endpoint":"messages","type":"document","to":"<destino>","document":{"link":"https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf","filename":"dem72-teste.pdf","caption":"[DEM-72 E2E 17:28:47] documento pela API"}}
{"endpoint":"chats","action":"get","chats":{"message_id":"<ID retornado no envio>"}}
{"endpoint":"chats","action":"list","chats":{"sendForMe":true,"startDate":"<início do teste, RFC3339 UTC>","page":1,"pageSize":20}}
{"endpoint":"messages","type":"revoke","revoke":{"message_id":"<ID do texto>"}}
```

**Rodadas**
| Rodada | Destino | Texto | Imagem | Documento |
|---|---|---|---|---|
| 1 | próprio número pareado (`556392308423`) | `3EB0EB607F7D4E51D957D4` | `3EB0A186A34C30D1EE765E` | `3EB0B182AC0DD1D8DC7868` |
| 2 | `5516997141457` (indicado pelo desenvolvedor) | `3EB0E88241216DDF69A3FA` | `3EB07BEE6364DD9AE87FFC` | `3EB048B961362F8B1EE9A8` |

**Resultados**
- Os 6 envios retornaram `status: success`, e o `chats`/`get` de cada ID retornou `Message` preenchido (antes: `Message: {}`).
- `chats`/`list` com `sendForMe: true` e `startDate` = início da rodada retornou `totalCount: 3` com exatamente os 3 IDs da rodada, nas duas rodadas (o filtro de datas compara `Info.Timestamp` em RFC3339 e funciona com o novo formato).
- **Regressão DEM-66:** revoke só com `message_id` (sem `to`) do texto da rodada 1 retornou `status: success` (o chat foi localizado pelo registro gravado). Na rodada 2 o revoke não foi executado, para as mensagens permanecerem no aparelho de destino.
- Nenhum erro de gravação no log do worker (`Erro ao salvar mensagem enviada`: 0 ocorrências).
- **Não verificado nesta sessão:** conferência visual das mensagens nos aparelhos (fica a cargo do desenvolvedor) e o fluxo completo passando pelo `api-service` (HTTP → fila).

#### 📦 Formato do novo retorno do `/chats` (`action: get`) para mensagens enviadas pela API

Antes (DEM-66 / Fase 2), o retorno era `{"Info": {...}, "Message": {}}` (ou só `Conversation` para texto). Agora:

**Texto** (rodada 1)
```json
{
  "status": "success",
  "data": {
    "Info": {
      "Chat": "66650040742069@lid",
      "Sender": "556392308423@s.whatsapp.net",
      "IsFromMe": true,
      "IsGroup": false,
      "ID": "3EB0EB607F7D4E51D957D4",
      "Type": "text",
      "PushName": "",
      "Timestamp": "2026-10-02T20:28:47Z"
    },
    "Message": {
      "ExtendedTextMessage": { "text": "[DEM-72 E2E 17:28:47] texto enviado pela API" }
    }
  }
}
```

**Imagem** (rodada 1; URL e thumbnail encurtados)
```json
{
  "status": "success",
  "data": {
    "Info": { "Chat": "66650040742069@lid", "Sender": "556392308423@s.whatsapp.net", "IsFromMe": true, "IsGroup": false,
              "ID": "3EB0A186A34C30D1EE765E", "Type": "media", "PushName": "", "Timestamp": "2026-10-02T20:28:54Z" },
    "Message": {
      "ImageMessage": {
        "URL": "https://mmg.whatsapp.net/o1/v/t24/f2/m269/…&mms3=true",
        "mimetype": "image/jpeg",
        "caption": "[DEM-72 E2E 17:28:47] imagem pela API",
        "fileSHA256": "3b25zbXxCcVn0qr9B2KIzVcYfnqX2UiYxyWR2/4oI1w=",
        "fileLength": 44891,
        "mediaKey": "YNOONXhNOKlJUrn5mLNi8S7cuvPnzbhL8+S/vmgq9gw=",
        "fileEncSHA256": "n3lbf0Uy2E3Ks1Qa+CSinBjAzsRwIacPG7xZfRLbut4=",
        "directPath": "/o1/v/t24/f2/m269/…",
        "JPEGThumbnail": "/9j/2wCEAAIBAQEBAQIBAQEC…<base64, 28836 caracteres>"
      }
    }
  }
}
```

**Documento** (rodada 1; URL encurtada)
```json
{
  "status": "success",
  "data": {
    "Info": { "Chat": "66650040742069@lid", "Sender": "556392308423@s.whatsapp.net", "IsFromMe": true, "IsGroup": false,
              "ID": "3EB0B182AC0DD1D8DC7868", "Type": "media", "PushName": "", "Timestamp": "2026-10-02T20:28:58Z" },
    "Message": {
      "DocumentMessage": {
        "URL": "https://mmg.whatsapp.net/v/t62.7119-24/…enc?…&mms3=true",
        "mimetype": "application/pdf",
        "fileSHA256": "PfedNKu8qZMI55y5RGHBiTWCYE1oMppB/UvsGIXmrbQ=",
        "fileLength": 13264,
        "mediaKey": "fz6p+li3sz5lMwj1Y/SUzQnp6yvNJ6pEF8azU4tlajc=",
        "fileName": "dem72-teste.pdf",
        "fileEncSHA256": "Jv2kpypfwIE3fhWJfPpvElhFKu30678DHuGEgQM/gg0=",
        "directPath": "/v/t62.7119-24/…",
        "caption": "[DEM-72 E2E 17:28:47] documento pela API"
      }
    }
  }
}
```

**Observações sobre o formato**
- A chave dentro de `Message` é o tipo protobuf realmente enviado (`ExtendedTextMessage`, `ImageMessage`, `DocumentMessage`, `VideoMessage`, `AudioMessage`, `StickerMessage`, `LocationMessage`, `ContactsArrayMessage`, `PollCreationMessage`, `InteractiveMessage`…). Texto enviado pela API chega em `ExtendedTextMessage.text`, **não** em `Conversation` (formato do hotfix da Fase 2, que nunca foi para produção).
- Campos binários (`mediaKey`, `fileSHA256`, `fileEncSHA256`, `JPEGThumbnail`) vêm em base64. A imagem inclui o `JPEGThumbnail` inteiro, o que deixa o retorno grande (~29 KB neste teste).
- `Info.Type`: `text`, `media` ou `poll`. `Info.Timestamp`: RFC3339 em UTC. `Info.PushName`: vazio para mensagens enviadas.
- `Info.Chat` é o JID devolvido pelo `IsOnWhatsApp` no envio; nos dois destinos testados veio no formato **`@lid`** (`66650040742069@lid` e `194334435573950@lid`), não `<telefone>@s.whatsapp.net`. Esse comportamento já existia no registro gravado pela DEM-66 (mesma origem do JID). Quem filtrar mensagens por `Info.Chat` com o número de telefone não encontrará essas mensagens.
- **Comparação com mensagens do histórico do aparelho (HistorySync) no mesmo SQLite:** mesmas chaves em `Info`; o `DocumentMessage` do histórico tem as mesmas chaves do enviado pela API mais `pageCount`; o `ImageMessage` do histórico traz chaves extras preenchidas pelo app (`height`, `width`, `mediaKeyTimestamp`, `scansSidecar`, `scanLengths`, `midQualityFileSHA256`) e não traz `JPEGThumbnail`. As chaves de mídia (`URL`, `directPath`, `mediaKey`, `fileSHA256`, `fileEncSHA256`, `fileLength`, `mimetype`) estão presentes nos dois casos. No histórico, `Info.Type` vem vazio. Não foi feita comparação com uma imagem enviada ao vivo pelo app durante o teste.

#### E2E pelo HTTP, com o `api-service` local (2026-10-05, 10:51–10:55 BRT)

Complementa o E2E de 02/10, que publicava direto na fila. Aqui o caminho foi completo: **HTTP → `api-service` → RabbitMQ → `worker-go` → WhatsApp → consulta pelo `/chats`**.

**Ambiente:** `api-service` (`main` @ `034cd2b`) em `http://localhost:4200`, iniciado por `ai.context/examples/instance/start-api.sh` usando só Postgres/Redis/RabbitMQ locais; worker de teste na branch `fix/dem-72-hotfix-race-condition` (`4c33d5f`), device `556392308423`. Token JWT da instância de teste `999999999999999` (usuário local `e2etest`). Destino dos envios: o próprio número pareado.

**Sequência (a mesma do relato do cliente)**
```bash
# 1) envio — a resposta traz "messageId" (ID gerado pelo api-service), usado na consulta
curl -s -X POST http://localhost:4200/v1/999999999999999/messages \
  -H "Authorization: Bearer $T" -H 'Content-Type: application/json' \
  -d '{"messaging_product":"whatsapp","to":"556392308423","type":"text","text":{"body":"[DEM-72 HTTP] texto enviado pelo api-service local","preview_url":false}}'

# 2) consulta
curl -s -X POST http://localhost:4200/v1/999999999999999/chats \
  -H "Authorization: Bearer $T" -H 'Content-Type: application/json' \
  -d '{"type":"chats","action":"get","chats":{"message_id":"<messageId>"}}'
```

**Resultados**
| Tipo | `messageId` | `Message` retornado pelo `/chats` |
|---|---|---|
| Texto | `3EB069E904A3A6AF368B97` | `ExtendedTextMessage.text` preenchido |
| Imagem (`image.link` + `caption`) | `3EB0D424CB9DB0DC9EA722` | `ImageMessage` com `URL`, `directPath`, `mediaKey`, `fileSHA256`, `fileEncSHA256`, `fileLength`, `mimetype`, `caption`, `JPEGThumbnail` |
| Documento (`document.link` + `filename` + `caption`) | `3EB0A2EDA5A8C51DD04417` | `DocumentMessage` com as mesmas chaves de mídia + `fileName: "dem72-http.pdf"` e `caption` |

- O `messageId` devolvido pelo `api-service` no envio é o mesmo `Info.ID` gravado pelo worker (o E2E de 02/10 não usava o `waMessageID` do `api-service`).
- `action: list` com `sendForMe: true` e intervalo de datas a partir do início dos envios de mídia retornou `totalCount: 2`, com exatamente os IDs da imagem e do documento.
- O retorno pelo HTTP vem embrulhado pelo `api-service` em `{"status":"success","data":{"data":{"Info":…,"Message":…},"status":"success"}}`.
- Chamada sem token: HTTP 401.
- O envio é assíncrono (o `/messages` responde antes de o worker enviar); a consulta foi feita 6–10 s depois.
- **Não verificado:** conferência visual no aparelho; comparação lado a lado com o worker da `main` (comportamento de produção, `Message: {}`).

#### Mapeamento do caminho da consulta e reprodução do problema original (2026-10-05, ~11:55 BRT)

**Caminho de `POST /v1/{phone_number_id}/chats` (`action: get`)**
1. `api-service/src/controllers/Chats/chats.controller.ts` (`getChats`): valida o corpo e chama `rabbitmqService.send(bodyData, bodyData, true)`.
2. `api-service/src/rabbitmq/rabbitmq.service.ts` (`send`): publica `{pattern, data}` na exchange `API-WhatsApp`, `routing_key = phone_number_id`, com `replyTo` + `correlationId`; aguarda a resposta por até 30 s.
3. `worker-go/rabbitmq/listener.go` (`processMessage`): lê `data.endpoint = "chats"` e `data.action = "get"` → `services.ExecuteChatsFunction`.
4. `worker-go/services/factory.go`: `ChatsFunctions["get"]` → `chats.GetMessageByID`.
5. `worker-go/services/chats/queries.go:85`: `SELECT data FROM messages WHERE id = ?` no **SQLite da instância** (`${DATABASE_PATH}/${PHONE_NUMBER_ID}.db`), com `id = chats.message_id`. Devolve a coluna `data` como está.
6. O worker responde na fila de resposta; `handleReply` resolve a promessa e o controller devolve `{"status":"success","data":<resposta do worker>}`.

Não há consulta ao WhatsApp nem a outro banco: **o `/chats` só devolve o que estiver gravado na tabela `messages` do SQLite**.

**Quem grava na tabela `messages`**
| Origem da mensagem | Onde é gravada | Conteúdo |
|---|---|---|
| Recebida, ou enviada pelo APP (eco) | `webhook/events.go` (`events.Message` → `utils.NormalizeMessage` → `UpsertMessage`) | completo |
| Histórico do pareamento | `webhook/events.go` (`events.HistorySync` → `UpsertMessage`) | completo |
| Enviada pela API | **`main`:** `services/factory.go` (DEM-66) grava só o `Info`. **Branch da DEM-72:** `services/messages/helpers.go` (`SendAndStore`) grava a mensagem enviada. | `main`: `Message` vazio. Branch: completo |

**Reprodução com o worker da `main` (`6af311b`, mesmo código da tag `v0.0.93`)** — binário compilado a partir de `git archive main`, fora do repositório; mesma instância de teste e `api-service` local.
- Envio: `POST /messages` (texto) → `messageId = 3EB02B8FE6119D5D3DCA75`.
- Consulta `POST /chats` (`action: get`) → resposta HTTP:
```json
{"status":"success","data":{"data":{"Info":{"Chat":"66650040742069@lid","Sender":"556392308423@s.whatsapp.net","IsFromMe":true,"IsGroup":false,"ID":"3EB02B8FE6119D5D3DCA75","Type":"","PushName":"","Timestamp":"1791212134"},"Message":{}},"status":"success"}}
```
- Linha lida direto do SQLite (`SELECT data FROM messages WHERE id = '3EB02B8FE6119D5D3DCA75'`): idêntica — `"Message":{}`, `"Type":""` e `Timestamp` em Unix (`"1791212134"`).
- Mesma sequência com a branch da DEM-72 (`4c33d5f`), ID `3EB069E904A3A6AF368B97`: a linha no SQLite tem `"Type":"text"`, `Timestamp` RFC3339 e `"Message":{"ExtendedTextMessage":{"text":"…"}}`.

**Conclusão:** a consulta chega ao worker e encontra a linha; o dado já está vazio **na gravação** (momento do envio), não na leitura nem no `api-service`. O problema original é reproduzido na `main` e não ocorre na branch.

### 📂 Arquivos Modificados (Fase 3)
- `worker-go/services/messages/helpers.go`
- `worker-go/services/messages/helpers_test.go` (novo)
- `worker-go/services/messages/{text,image,video,audio,document,sticker,location,contact,poll,interactive}.go`
- `worker-go/services/factory.go`


## 🌐 Fase 4: retorno do `/chats` no formato de mensagem da API oficial (2026-10-05)

> **Estado:** commitado localmente em 05/10, **sem push**. `worker-go`: branch `fix/dem-72-hotfix-race-condition`, commit `bb61f08` (`feat(dem-72): devolver mensagens do /chats no formato da API oficial`), sobre o `4c33d5f`. `api-service`: branch `fix/dem-72-chats-official-format`, commit `a215494` (`docs(dem-72): documentar o retorno do /chats no formato da API oficial`). Arquivos de teste fora do git, a pedido do desenvolvedor. Não foi possível conferir se as branches estão atualizadas com o remoto (sem acesso SSH ao GitLab nesta sessão). Decisões do desenvolvedor em 05/10: formato oficial como **padrão** do `/chats` (substitui `Info` + `Message`) e entrega **junto** com a correção da gravação, na mesma demanda.

### 🎯 Motivo
O `/chats` devolvia a estrutura interna do worker (`types.NormalizedMessage`: `Info` + `Message` com os nomes do protocolo do WhatsApp Web), enquanto envio e webhooks seguem o padrão da API oficial. A API oficial não tem endpoint de consulta de mensagens; a referência adotada é o objeto de mensagem dos webhooks, em especial o eco de mensagens enviadas (`smb_message_echoes`: `from`, `to`, `id`, `timestamp`, `type` e o objeto do tipo).

### 🛠️ Solução Adotada
A gravação no SQLite **não muda** (continua o formato interno, com as chaves de mídia, usado pelo revoke e pelo download). A conversão acontece **na leitura**, no worker.

1. **`worker-go/webhook/messageObject.go` (novo)**
   - `BuildStoredMessageObject(client, stored)`: converte um registro da tabela `messages` no objeto oficial. Remonta a mensagem do protocolo (`storedToProto`), aplica o mesmo `UnwrapRaw()` das mensagens recebidas (viewOnce, ephemeral, documentWithCaption — o histórico grava esses invólucros sem desempacotar) e reaproveita o conversor dos webhooks.
   - Campos comuns: `id`, `timestamp` (Unix em texto; aceita o `Info.Timestamp` gravado em RFC3339 ou no Unix legado da DEM-66), `from`, `to`, `isGroup` e `group_id` (extensões que os webhooks do projeto já usam).
   - `from`/`to`: mensagem enviada (`IsFromMe`) → `from` = número da instância, `to` = número do chat; recebida → `from` = remetente, `to` = número da instância. JIDs `@lid` são convertidos para telefone por `client.Store.LIDs.GetPNForLID`; sem mapeamento, o campo sai vazio. Grupo é detectado pelo servidor `g.us` do chat (o histórico grava `IsGroup` sempre `false`); em mensagens de grupo vindas do histórico o remetente não é gravado, então `from` sai vazio.
   - `findOrInsertMedia`: reaproveita o `id` da tabela `midias` quando já existe registro com a mesma `media_key`; só insere na primeira consulta.
   - `parseVCardContact`, `buildListInteractive`, `buildSentInteractive`: tipos enviados que o conversor não cobria (contatos em lista, lista interativa, botões/carrossel — este último gravado como mapa genérico por causa do `oneof` do protobuf).
   - Registro sem conteúdo ou de tipo não mapeado → `type: "unsupported"` + `errors[{code: 131051, …}]`.
2. **`worker-go/webhook/createContent.go`**: `ParseMessageContent` passou a delegar para `parseMessageContent(message, registerMedia)`; os 5 pontos que chamavam `database.InsertMedia` usam a função injetada. Os webhooks continuam inserindo sempre (`insertMedia`), **sem mudança de comportamento**. Novos `case` para `ContactsArrayMessage` e `ListMessage` (antes caíam em `unknown`; nos webhooks esses tipos só ocorrem em mensagens recebidas, que antes eram descartadas como `unknown`).
3. **`worker-go/database/midiaStore.go`**: `FindMediaIDByMediaKey` e índice `idx_midias_media_key` (`CREATE INDEX IF NOT EXISTS`, criado na subida do worker).
4. **`worker-go/services/chats/queries.go` e `helpers.go`**: `GetMessageByID` devolve `BuildStoredMessageObject(...)`; `executeMessageQuery` recebe o `client` e `PaginatedMessages.Messages` passa a ser a lista de objetos oficiais (lista vazia sai como `[]`, antes `null`). O invólucro de paginação (`messages`, `totalCount`, `page`, `pageSize`, `totalPages`) foi mantido.
5. **`api-service/src/controllers/Chats/chats.controller.ts`** (só documentação): descrição do retorno, exemplos de resposta (texto, imagem, documento, `unsupported`, lista), exemplos renomeados para "Listar Mensagens" / "Obter uma Mensagem pelo ID" e a orientação de usar o `messageId` do envio em `message_id`. Resposta documentada no status **201**, que é o que o endpoint devolve.

### ⚠️ Mudança de contrato (quebra para quem consome o `/chats`)
| Antes | Agora |
|---|---|
| `data.data.Info.ID` | `data.data.id` |
| `Info.Timestamp` (RFC3339) | `timestamp` (Unix, texto) |
| `Info.Chat` / `Info.Sender` (JIDs `@lid` / `@s.whatsapp.net`) | `from` / `to` (números) |
| `Info.IsFromMe` | `from` igual ao número da instância |
| `Message.Conversation` / `Message.ExtendedTextMessage.text` | `type: "text"`, `text.body` |
| `Message.ImageMessage.{URL,directPath,mediaKey,…}` | `type: "image"`, `image.{id,mime_type,sha256,caption}` |
| `Message: {}` (enviadas pela API antes da correção) | `type: "unsupported"` + `errors` |

`Info.PushName` e `Info.Type` não têm equivalente no objeto de mensagem e deixaram de ser devolvidos. O invólucro do `api-service` (`{"status","data":{"data":…,"status"}}`) não mudou.

### 🧪 Teste Prático e Homologação (Fase 4)
**Automatizado (`worker-go`, pacotes exceto a raiz):** `gofmt` sem pendências nos arquivos alterados, `go build`, `go vet` e `go test -count=1` OK. Novo `webhook/messageObject_test.go` (7 testes): texto enviado com `context`; `Conversation` + timestamp Unix legado; documento com `id` de mídia e sem chaves internas; documentWithCaption de grupo vindo do histórico; contatos (vCard com `TEL;type=…;waid=…` e `itemN.TEL`) e lista; botões (`quick_reply` → `reply`, `cta_url`); registro vazio → `unsupported`.
**`api-service`:** `prettier --check`, `eslint` e `tsc --noEmit` OK; `/swagger-json` local confirma descrição, exemplos de corpo renomeados e 5 exemplos na resposta 201.

**E2E pelo HTTP** (`api-service` local na porta 4200 + worker de teste com o código desta fase; device `556392308423`; envios para o próprio número):

| Caso | ID | `type` retornado | Observação |
|---|---|---|---|
| Texto enviado pela API | `3EB069E904A3A6AF368B97` | `text` | `text.body` preenchido |
| Imagem enviada pela API | `3EB0D424CB9DB0DC9EA722` | `image` | `image.id = 540609559314199`; **mesmo `id` na 2ª consulta** |
| Documento enviado pela API | `3EB0A2EDA5A8C51DD04417` | `document` | `filename`, `caption`, `mime_type`, `id` |
| Botões (`interactive.type: button`) | `3EB0F52051340A954AA62E` | `interactive` | `header`, `body`, `footer`, `action.buttons[].reply.{id,title}` |
| Lista (`interactive.type: list`) | `3EB03B23FA4677FC9D654A` | `interactive` | `action.button`, `action.sections[].rows[]` |
| Contatos | `3EB0AC53A7CE00C6C75A6C` | `contacts` | `name.formatted_name`, `phones[].{phone,type}` |
| Localização | `3EB01DDD8D1F0C57E78703` | `location` | `latitude`, `longitude`, `name`, `address` + extras já existentes no conversor |
| Registro vazio gravado pela `main` | `3EB02B8FE6119D5D3DCA75` | `unsupported` | `errors[0].code = 131051` |
| Texto enviado pelo APP (histórico) | `ACAD71E2…` | `text` | `from` = número da instância |
| Imagem recebida (histórico) | `AC1223BE…` | `image` | `id` de mídia gerado |

Exemplos reais de retorno:
```json
{"status":"success","data":{"data":{"from":"556392308423","id":"3EB069E904A3A6AF368B97","isGroup":false,"text":{"body":"[DEM-72 HTTP] texto enviado pelo api-service local"},"timestamp":"1791208304","to":"556392308423","type":"text"},"status":"success"}}
{"status":"success","data":{"data":{"from":"556392308423","id":"3EB0D424CB9DB0DC9EA722","image":{"caption":"[DEM-72 HTTP] imagem pelo api-service","id":"540609559314199","mime_type":"image/jpeg","sha256":"3b25zbXxCcVn0qr9B2KIzVcYfnqX2UiYxyWR2/4oI1w="},"isGroup":false,"timestamp":"1791208499","to":"556392308423","type":"image"},"status":"success"}}
{"status":"success","data":{"data":{"from":"556392308423","id":"3EB0F52051340A954AA62E","interactive":{"action":{"buttons":[{"reply":{"id":"btn_sim","title":"Sim"},"type":"reply"},{"reply":{"id":"btn_nao","title":"Nao"},"type":"reply"}]},"body":{"text":"[DEM-72 OFICIAL] confirma?"},"footer":{"text":"teste"},"header":{"text":"DEM-72","type":"text"},"type":"button"},"isGroup":false,"timestamp":"1791215780","to":"556392308423","type":"interactive"},"status":"success"}}
```
- `action: list` (`sendForMe: true` + intervalo de datas): `totalCount: 2`, com os IDs dos botões e da lista, já no formato oficial.
- Tabela `midias`: 2037 → 2039 linhas após consultar 3 mídias, uma delas duas vezes (reaproveitamento confirmado).

**Validação complementar (2026-10-05, ~13:25 BRT)** — mesma instância e `api-service` local, envios para o próprio número:

| Caso | ID | Retorno do `/chats` (`action: get`) |
|---|---|---|
| Vídeo (`video.link` + `caption`) | `3EB0F7819B581618E3DED9` | `type: video`, `video.{id: 968746811654895, mime_type: video/mp4, sha256, caption}` |
| Áudio (`audio.link`, mp3 convertido para ogg/opus) | `3EB02050896BAB82CCC963` | `type: audio`, `audio.{id, mime_type: "audio/ogg; codecs=opus", sha256}` |
| Sticker (`sticker.link`, webp) | `3EB064CA803EF739648873` | `type: sticker`, `sticker.{id, mime_type: image/webp, sha256, animated: false}` |
| `get` com ID inexistente | — | `{"status":"success","data":{"message":"nenhuma mensagem encontrada com o ID especificado","status":"error"}}` (comportamento anterior, inalterado) |
| `list` sem `page`/`pageSize` | — | lista simples (sem o invólucro de paginação) com os 3 objetos acima |

**Download de mídia pelo `id` devolvido no `/chats`:** `GET /v1/{mediaId}` com o token da instância, para a imagem (`540609559314199`), o documento (`771665921858179`) e o vídeo (`968746811654895`). Os três retornaram `{id, url, filename, mime_type, file_size, sha256, messaging_product}` e o worker baixou e descriptografou os arquivos em `MEDIAS_PATH`. O SHA-256 dos arquivos gravados é igual ao `sha256` devolvido (`ddbdb9cd…235c`, `3df79d34…adb4`, `0cd83d94…4451`) e os tipos conferem (JPEG, PDF, MP4). A `url` devolvida respondeu 404 no ambiente local porque o `api-service` procura o arquivo em uma estrutura de pastas diferente da usada pelo worker de teste; é configuração do ambiente local, não foi investigada além disso.

Observação: o endpoint de mídia devolve `sha256` em **hexadecimal**, enquanto o objeto de mensagem (webhooks e agora `/chats`) devolve em **base64**. A divergência já existia entre os dois endpoints.

**Mensagem recebida ao vivo (2026-10-05, 13:32 BRT)** — o desenvolvedor enviou um texto de outro número (`5516…1457`) para a instância de teste:
- **Webhook de recebimento (comportamento não alterado):** o worker montou o payload oficial (`messaging_product: whatsapp`, `messages[{from, id: A56C733D192684D5B12D976661201BAC, timestamp: 1791217940, type: text, text.body, isGroup: false}]`). O POST falhou com `connection refused` porque não há listener de webhook no ambiente de teste (`127.0.0.1:8099`), o que é esperado.
- **Gravação:** linha no SQLite com `Info.Chat`/`Info.Sender` em `@lid`, `Type: text` e `Message.ExtendedTextMessage`.
- **`/chats` (`action: get`):** `{"from":"5516…1457","to":"556392308423","id":"A56C733D192684D5B12D976661201BAC","timestamp":"1791217940","type":"text","text":{"body":…},"isGroup":false}` — mesmo `id`, `timestamp` e `from` do webhook; o `@lid` foi convertido para o telefone.
- **Mensagens de grupo recebidas ao vivo** (duas, chegadas espontaneamente durante o teste: um texto e uma imagem): `/chats` devolveu `isGroup: true`, `group_id` com o JID do grupo, `from` com o telefone do participante (convertido de `@lid`) e, na imagem, `image.{id, mime_type, sha256}`.

Observação: neste ambiente (fuso `-03:00`) o `Info.Timestamp` das mensagens **recebidas** é gravado com o deslocamento local (`2026-10-05T13:32:20-03:00`), enquanto o das enviadas pela API é gravado em UTC (`…Z`). O filtro de datas do `list` compara esses textos; a mistura de formatos pode ordenar/filtrar errado em ambientes fora de UTC. Comportamento anterior a esta demanda (`utils.NormalizeMessage` usa o fuso do processo); não foi alterado nem testado em pod de produção.

### 🔎 Limitações e pontos não verificados
- Não testados em aparelho nesta fase: enquete (o envio exige um grupo), reação (não é gravada pelo worker no envio), carrossel e mensagens **enviadas** a grupos.
- `sha256` sai em base64, igual aos webhooks do projeto; a codificação usada pela Meta nesse campo não foi confirmada na documentação original.
- Enquete e localização mantêm os campos que o conversor dos webhooks já devolvia (a API oficial não tem tipo de enquete; a localização traz `accuracyInMeters`, `speedInMps`, `url`, `isLive`).
- `context.from` é extraído do participante gravado; quando ele é `@lid`, sai o identificador `lid`, como já ocorre nos webhooks.
- Os envios de teste foram para o próprio número, por isso `from` e `to` aparecem iguais nos exemplos.
- Conferência visual no aparelho não realizada.

### 📂 Arquivos Modificados (Fase 4)
- `worker-go/webhook/messageObject.go` (novo) e `worker-go/webhook/messageObject_test.go` (novo)
- `worker-go/webhook/createContent.go`
- `worker-go/database/midiaStore.go`
- `worker-go/services/chats/queries.go`, `worker-go/services/chats/helpers.go`
- `api-service/src/controllers/Chats/chats.controller.ts`


## 🧩 Fase 4.1: ordenação, `history_context` e correção de travamento no `list` (2026-10-06)

> **Estado:** commitado localmente, **sem push** — `worker-go` `f035af9` (sobre `bb61f08`, que já está no remoto) e `api-service` `995f5ba` (sobre `a215494`, já no remoto). Arquivos de teste fora do git.

**Decisão:** o programador chefe (Eduardo) confirmou em 06/10 que o `/chats` deve devolver o mesmo formato dos webhooks e indicou o webhook de histórico como referência. O formato da Fase 4 foi mantido, com dois alinhamentos pedidos pelo desenvolvedor.

### 🛠️ Alterações
1. **Ordenação do `list`** (`services/chats/helpers.go`, `database/messageStore.go`): `ORDER BY database.MessageTimestampOrder, rowid` — das mensagens mais antigas para as mais recentes. A expressão é `CAST(COALESCE(strftime('%s', json_extract(data,'$.Info.Timestamp')), json_extract(data,'$.Info.Timestamp')) AS INTEGER)`: converte RFC3339 de qualquer fuso para Unix e cai no valor bruto quando o registro antigo (DEM-66) guarda Unix em texto. Novo índice `idx_messages_timestamp_unix` sobre a mesma expressão (`CREATE INDEX IF NOT EXISTS`, criado na subida do worker). Antes a consulta não tinha `ORDER BY`.
2. **`history_context.status`** em cada mensagem (`webhook/messageObject.go`), com a mesma regra do webhook de histórico, extraída para `historyMessageStatus` em `webhook/payloadBuilder.go`: `PLAYED` para `audio`/`video`, `READ` para os demais. É um valor fixo por tipo, não o status real de leitura.
3. **Correção de travamento do SQLite no `list`** (defeito introduzido no `bb61f08` e encontrado nesta validação): a conversão de cada mensagem era feita dentro do laço `rows.Next()`. Para mídias ainda sem registro em `midias`, a conversão faz `INSERT`; com o cursor de leitura aberto em outra conexão do pool, o `INSERT` não conseguia o lock exclusivo, esperava o `busy_timeout` (5 s) e falhava com `database is locked`. Efeitos observados: mídias devolvidas como `unsupported`, requisição estourando o tempo limite da API (30 s) e o próprio whatsmeow registrando `Failed to save push name … database is locked`. Agora `executeMessageQuery` lê todos os registros, fecha o cursor e só então converte.
4. **Falha ao registrar mídia** (`findOrInsertMedia`): passa a logar o erro e devolver a mensagem com o tipo e os demais campos, sem o `id`, em vez de degradar para `unsupported`.
5. **Swagger** (`api-service`): descrição e exemplos do `/chats` atualizados com a ordenação e o `history_context`.

### 🧪 Teste Prático e Homologação (Fase 4.1)
- `gofmt`, `go build`, `go vet` e `go test -count=1` OK (pacotes exceto a raiz). Novo `database/messageOrder_test.go`: ordena corretamente Unix em texto, `…Z` e `…-03:00` misturados e valida que o SQLite aceita o índice. `webhook/messageObject_test.go` passou a conferir o `history_context`.
- `api-service`: `prettier`, `eslint` e `tsc --noEmit` OK.
- **E2E pelo HTTP** (instância de teste + `api-service` local):
  - `get`: texto → `history_context.status: READ`; vídeo → `PLAYED`.
  - `list` (`sendForMe`, 05/10 13:00–17:30 UTC, 20 por página): 12 mensagens em ordem crescente de `timestamp`, com `id` de mídia em imagem, documento, vídeo, áudio e sticker; resposta em 0,08 s.
  - `list` sem filtro de remetente (05/10 12:00–18:00 UTC, 100 por página): `totalCount: 331`, 100 devolvidas em ordem crescente (72 imagens, 14 textos, 3 áudios, 2 vídeos e outros), nenhuma mídia sem `id`; resposta em 0,05 s.
  - Após a correção: 0 ocorrências de `database is locked` e 0 erros de registro de mídia no log do worker.
- **Antes da correção** (mesma instância, código do `bb61f08` + ordenação): no `list` paginado a imagem e o documento saíram como `unsupported`, a consulta sem filtro estourou o tempo limite e o log registrou `database is locked`.

### 🔎 Observações
- A criação do índice novo acontece uma vez na primeira subida do worker em cada instância; em bancos grandes pode alongar essa subida. Não foi medido em produção.
- O `list` continua em lista paginada (não agrupa por conversa em `threads` como o webhook de histórico) e mantém o campo `to`.

### 📂 Arquivos Modificados (Fase 4.1)
- `worker-go/services/chats/helpers.go`, `worker-go/database/messageStore.go`, `worker-go/webhook/messageObject.go`, `worker-go/webhook/payloadBuilder.go`
- `worker-go/database/messageOrder_test.go` (novo, fora do git) e `worker-go/webhook/messageObject_test.go` (fora do git)
- `api-service/src/controllers/Chats/chats.controller.ts`


## 🔀 Fase 4.2: merge da `main` (`v0.0.94`) na branch (2026-10-06, ~18:50 BRT)

> **Estado:** `worker-go` `fix/dem-72-hotfix-race-condition` em `dbd2d4e` (merge), 3 commits à frente do remoto (`f035af9`, `7c740e4` da `main` e o merge), **sem push**.

- A `main` remota recebeu o commit `7c740e4` (Eduardo Policarpo, 06/10 16:56), já com a tag **`v0.0.94`**: `services/medias.go` (download de áudio via `DownloadMediaWithPath`, sem `GetMessageByMediaKey`), remoção de `GetMessageByMediaKey` em `database/messageStore.go`, `recover()` em `rabbitmq/listener.go` (`processMessage`) e `.dockerignore`. **A release desta demanda passa a ser `v0.0.95`.**
- **Conflito:** `database/messageStore.go` — a `main` removeu `GetMessageByMediaKey` e a branch tinha acrescentado `InsertOnlyMessage` logo após ela. Resolução: manter a remoção e a função `InsertOnlyMessage` (usada por `SendAndStore`).
- **Validação pós-merge:** `go build`, `go vet` e `go test -count=1` OK; E2E pelo HTTP: texto e áudio enviados pela API, `get` no formato oficial com `history_context` (`READ`/`PLAYED`), `list` ordenado; log sem `database is locked` e sem `panic`.

### ⚠️ Defeito encontrado na `main` `v0.0.94` (não é desta demanda)
O download de **áudio** pelo `id` de mídia (`GET /v1/{mediaId}`) falha com **410** (`download failed with status code 400`) no código do `7c740e4`:
- Em `services/medias.go`, o caso `utils.IsAudio` chama `client.DownloadMediaWithPath(..., whatsmeow.MediaAudio, mimeType, false)`. O 7º parâmetro é o `mmsType` (`"audio"`, `"image"`…), e está recebendo o MIME; para áudio o MIME gravado é `audio/ogg; codecs=opus` (com espaço e `;`).
- Reprodução (instância de teste, arquivo ainda não baixado em disco): áudio **recebido** (mídia `367906916443084`) e áudios enviados pela API → 410 com o binário do `7c740e4`.
- Com o código da branch **antes** do merge (`f035af9`, caminho antigo via mensagem gravada) os áudios enviados pela API baixavam normalmente.
- Experimento em cópia descartável do `7c740e4`, trocando só o argumento `mimeType` por `"audio"` nesse caso: o mesmo áudio recebido baixou (121.743 bytes).
- Imagem, documento e vídeo usam a mesma chamada com o MIME e funcionaram nos testes de 05/10 (`image/jpeg`, `application/pdf`, `video/mp4`).
- **Não corrigido nesta branch** (aguardando decisão do desenvolvedor / programador chefe). Após o merge, a branch herda esse comportamento.


## 🚀 Fase 5: merge e release (2026-10-06, noite)

- **MRs aceitos e mergeados** pelo desenvolvedor: `worker-go` (`main` em `363fb21`, `Merge branch 'fix/dem-72-hotfix-race-condition' into 'main'`) e `api-service`.
- **Releases criadas pelo desenvolvedor e conferidas no git local:**
  - `worker-go` **`v0.0.95`** — contém `4c33d5f` (gravação da mensagem enviada), `bb61f08` (formato dos webhooks no `/chats`) e `f035af9` (ordenação, `history_context`, correção do travamento do SQLite), além da `v0.0.94` da `main`.
  - `api-service` **`v1.57.5`** (`eab3243`, `chore(release): 1.57.5`) — contém `a215494` e `995f5ba` (Swagger do `/chats`).
- **Ainda não verificado / pendente para considerar em produção:**
  1. pipelines das duas tags no GitLab (build das imagens);
  2. atualização do `infra-gitops` pelo CI para `api-service:v1.57.5` (a cópia local ainda mostra `v1.57.4`; não foi feito `pull`);
  3. atualização das instâncias para o worker `v0.0.95` (`appVersion`) — a tag só gera a imagem;
  4. reteste em produção (`/messages` → `/chats` com `action: get`) e registro do resultado aqui.
- **Herdado da `v0.0.94` e presente na `v0.0.95`:** download de áudio pelo `id` de mídia retornando 410 (`services/medias.go`, `mmsType` recebendo o MIME). Não corrigido.
- O frontmatter segue `status: concluido`; o ciclo só fecha de fato após os itens 1 a 4.

## ✅ Aprovação do QA (07/10/2026)

No backlog exportado em 07/10/2026 14:48 a demanda 72 passou de **Devolvido** para **Aprovado**. Releases em uso: `worker-go v0.0.95` e `api-service v1.57.5`. O resultado detalhado do reteste em produção (payloads e retorno) não foi repassado a esta sessão.
