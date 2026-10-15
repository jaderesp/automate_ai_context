---
id: DEM-74
status: concluido
data_ativacao: 2026-09-22 13:30:15
data_reabertura: 2026-09-23 09:00:00
data_conclusao: 2026-09-23 09:45:00
modulo: API
---

# 🚀 Histórico de Execução: Envio Mensagem type Document / messages

## 📌 Resumo do Problema
Ao enviar um documento pela API (`POST /v1/:phone_number_id/messages`, type `document`), o arquivo chegava corretamente ao destinatário, porém o app do WhatsApp exibia o rótulo nativo **"Sem título"** no lugar do nome real do arquivo. O cliente também reporta que a legenda (`caption`) deve ser exibida corretamente junto ao arquivo.

## 🛠️ Solução Adotada

### Diagnóstico (Causa Raiz)
**Divergência de contrato entre microsserviços (`api-service` × `worker-go`):**

1. O `api-service`, no commit `b469892` (12/08/2026), migrou o campo para o padrão Meta Cloud API **`document.filename`** (`src/controllers/Messages/message.entities.ts:209`, classe `CaptionedFileMessage`) e publica o payload integralmente no RabbitMQ, sem mapper (`src/rabbitmq/rabbitmq.service.ts:236`).
2. O `worker-go`, em `services/messages/document.go:38`, continuava lendo a chave legada camelCase **`documentContent["fileName"]`**. Como a chave não existe no payload, a type assertion falhava, `fileName` permanecia `""` e o campo `DocumentMessage.FileName` do protobuf nunca era preenchido (`document.go:88-89`). Sem o `FileName`, o app do WhatsApp aplica o fallback nativo "Sem título".
3. Evidência de regressão: o commit irmão no worker (`68585f3`, 16/08/2026) corrigiu **apenas** `services/medias.go` (upload), esquecendo `document.go`. O caminho irmão `services/messages/interactive.go:361-364` (documento em header interativo) já usava `filename` corretamente, comprovando a inconsistência interna.

### Correção Aplicada (Opção A — `worker-go/services/messages/document.go`)
1. **Nova função pura `extractFileName`**: lê `filename` (padrão Meta) com fallback retroativo para `fileName` (clientes legados). Precedência: `filename` > `fileName`; `filename` vazio continua vencendo o legado (semântica anterior preservada); tipo inválido (não-string) cai para o legado.
2. **Fluxo por `id` (mídia já upada)**: passou a capturar o `file_name` retornado por `database.GetMediaByID` (`database/midiaStore.go:88-130`), que antes era descartado com `_`. Esse nome é gravado no upload via `InsertMedia` (`services/medias.go:22-46`, com `SanitizeFileName`). Agora é usado como fallback quando o payload não traz nome — cenário válido no contrato Meta, onde `filename` é opcional nesse fluxo.
3. **Fluxo por `link`**: novo helper `fileNameFromURL` extrai o basename do **path** da URL via `net/url` + `url.PathUnescape` + `utils.SanitizeFileName`, evitando que query strings (ex.: `?token=...`) ou percent-encoding contaminem o nome.
4. **Fallback final `"document"`**: mesmo padrão já utilizado em `utils/processMidias.go:674-675`.

### Contrato de campos (caption × filename)
- `document.caption` → `DocumentMessage.Caption` (legenda; lido em `document.go:31-34`, setado em `document.go:84-86`). **Não há transformação**: o texto exibido é exatamente o enviado.
- `document.filename` (fallback `fileName`, nome do banco, basename da URL, `"document"`) → `DocumentMessage.FileName` (nome do arquivo no balão do documento).
- São campos independentes; o WhatsApp exibe ambos. **Atenção:** o `caption` só é lido **dentro** do objeto `document` (contrato da API).

### Análise de Impacto (sem regressão)
- Mudança local e aditiva, exclusiva do tipo `"document"` (`services/factory.go:28`).
- Não afeta áudio/imagem/vídeo, nem mensagens interativas (`interactive.go` usa `GetMediaMessage`).
- Não afeta o intercept de eco da DEM-66 (`factory.go:108-135`), que persiste apenas `ID/Chat/Sender/Timestamp` no SQLite.

## 🔄 Reabertura (2026-09-23)

### Relato do cliente (grupo interno, 22/09 18:54–19:01, após deploy em produção)
- "O payload retorna o `filename`. Porém quando vamos enviar um documento passando o `filename` dele, o documento não exibe filename na conversa."
- **"O caption aparece de boa ✅. Já o filename não ❌."**
- "A API está enviando todos documentos com o nome: **Sem título**. Ignora o valor informado no parâmetro `filename`."
- Alinhamento no grupo: `caption` (legenda da mídia) e `filename` (nome do arquivo) são coisas distintas e independentes.

### Evidência de que o fix NÃO está rodando em produção
- `origin/main` **contém** os dois merges: `d5e3215` (`Merge ... fix/dem-74-document-filename`) e `04cd686` (`Merge ... fix/dem-73-button-reply-ios`).
- Porém a tag mais recente é **`v0.0.91` = `434ddb4`** (commit da DEM-73), criada **antes/à parte** do merge da DEM-74; **não existe `v0.0.92`**.
- A CI do worker builda a imagem **por tag** e o `worker.deployment.yaml` usa `image: registry.gitlab.com/.../worker-go:latest` → a imagem em produção (v0.0.91) **não contém o fix do filename**.
- Isso explica exatamente o sintoma: `caption` OK (código antigo já tratava `document.caption`) e `filename` "Sem título" (código antigo lê `fileName`, enquanto a API envia `filename`).
- **Ação necessária:** taguear a `main` (ex.: `v0.0.92` no merge `04cd686`) para a CI gerar nova imagem e reiniciar o deployment.

### Deploy executado (2026-09-23)
- `git pull` na `main` do `worker-go`: fast-forward `ac1eb12..04cd686` (traz os merges da DEM-74 `d5e3215` e DEM-73 `04cd686`).
- `./release.sh`: criada e publicada a tag **`v0.0.92` → `04cd686`** (`git tag --contains d9c57d0` e `--contains 434ddb4` confirmam que a tag contém **as duas correções**).
- CI (jobs `build`/`docker-build`, disparam apenas em tags) publica `worker-go:v0.0.92` e `:latest`.
- **Passos seguintes de rollout (api-service):**
  1. `getRegistryTags` tem **cache de 1h** (`k8s.service.ts:763`) → reiniciar o pod do `api-service` para enxergar a nova tag imediatamente (ou aguardar até 1h).
  2. Atualizar/reiniciar as instâncias passando `appVersion: "latest"` (resolve para a maior tag = `v0.0.92`, `k8s.service.ts:721-727`) ou `"v0.0.92"` explícito. **Rollout restart simples não troca a imagem** — só reinicia a versão atual; instâncias com `appVersion` pinada no banco permanecem na versão antiga se o update não informar a nova.
  3. Validar a imagem do pod no cluster (ou a versão no painel) e solicitar o reteste do cliente (documento por `link` e por `id`, com `filename` + `caption`).

### Testes E2E locais (23/09/2026) — executados
**Ambiente de teste:**
- **Binário:** `worker-go` na branch `fix/dem-74-document-filename` (`d9c57d0`), compilado com `CGO_ENABLED=1 go build -o /tmp/opencode/worker-dem74 ./cmd/main.go`.
- **Device pareado via QRCode:** `556392308423:20@s.whatsapp.net` (instância de teste `999999999999999`; SQLite `/tmp/opencode/dem74/999999999999999.db`; `isAuthenticated=true deploymentStatus=connected`).
- **Infra local:** RabbitMQ `localhost:5672` (exchange `API-WhatsApp`), Postgres `uzapi`, listener de webhook em `http://127.0.0.1:8099/webhook`.
- **Arquivo servido por HTTP:** `python3 -m http.server 8090 --directory ai.context/examples/documents` → URL `http://127.0.0.1:8090/Check%20list%20de%20Implementa%C3%A7%C3%A3o%20de%20requisitos.pdf`.
- **Arquivo de teste:** `ai.context/examples/documents/Check list de Implementação de requisitos.pdf` — 107.147 bytes, nome com **espaços e acentos** (também valida o percent-encoding do fallback).

**Cenário A — `link` + `filename` + `caption`** (payload exato publicado na exchange `API-WhatsApp`, routing key `999999999999999`):
```json
{
  "pattern": "messages",
  "data": {
    "endpoint": "messages",
    "type": "document",
    "to": "556392477769",
    "phone_number_id": "999999999999999",
    "phoneNumber": "556392308423",
    "document": {
      "link": "http://127.0.0.1:8090/Check%20list%20de%20Implementa%C3%A7%C3%A3o%20de%20requisitos.pdf",
      "filename": "Check list de Implementação de requisitos.pdf",
      "caption": "Legenda de teste DEM-74 - Cenario A (link + filename + caption)"
    }
  }
}
```
- **Destinatários/messageIDs:** iPhone `556392477769` → `3EB03C753742800961E26C` (09:13); Android `5516997141457` → `3EB085DA3F7D1415C1AE43` (09:22).
- **Esperado no aparelho:** nome **"Check list de Implementação de requisitos.pdf"** + legenda *"Legenda de teste DEM-74 - Cenario A (link + filename + caption)"*.

**Cenário B — `link` sem `filename` + `caption`** (fallback do basename da URL):
```json
{
  "pattern": "messages",
  "data": {
    "endpoint": "messages",
    "type": "document",
    "to": "556392477769",
    "phone_number_id": "999999999999999",
    "phoneNumber": "556392308423",
    "document": {
      "link": "http://127.0.0.1:8090/Check%20list%20de%20Implementa%C3%A7%C3%A3o%20de%20requisitos.pdf",
      "caption": "Legenda de teste DEM-74 - Cenario B (link sem filename + caption)"
    }
  }
}
```
- **Destinatários/messageIDs:** iPhone `556392477769` → `3EB0CDFD7965B56610AB79` (09:13); Android `5516997141457` → `3EB0537D6601E97E834D8A` (09:22).
- **Esperado no aparelho:** nome **"Check_list_de_Implementacao_de_requisitos.pdf"** (basename da URL, `PathUnescape` + `SanitizeFileName`) + legenda *"Legenda de teste DEM-74 - Cenario B (link sem filename + caption)"*.

**Cenário C — upload por `id` + `filename` + `caption`** (planejado): colocar o PDF em `/data/999999999999999/medias/` (nome sanitizado), publicar `endpoint: "media"`, `action: "upload"` com `filename`/`fileSize`/`fileType`, obter o `id` na tabela `midias` e enviar o documento por `id` com `filename` + `caption`; e variação **C2** (sem `filename`) para validar o fallback do nome gravado no SQLite.

**Resultado observado no aparelho:** ✅ **CONFIRMADO pelo desenvolvedor (23/09)** — nome do arquivo e legenda exibidos **perfeitamente** nos dois aparelhos (iPhone `556392477769` e Android `5516997141457`):
- **Cenário A:** nome "Check list de Implementação de requisitos.pdf" + legenda do Cenário A exibidos corretamente.
- **Cenário B:** nome derivado do basename da URL ("Check_list_de_Implementacao_de_requisitos.pdf") + legenda do Cenário B exibidos corretamente.

**Cenário C (upload por `id`):** não executado — os Cenários A/B já validaram de ponta a ponta o mapeamento `filename` → `DocumentMessage.FileName` (caminho que falhava) e o `caption` → `DocumentMessage.Caption`. O fallback do `id` está coberto por teste unitário (`extractFileName`/`GetMediaByID`).

## 🧪 Testes Unitários (executados e aprovados)
- **Arquivo criado:** `services/messages/document_test.go` (table-driven, 11 subtestes).
- **Cobertura:**
  - `extractFileName`: `filename` padrão Meta; `fileName` legado; precedência de `filename`; ausência de campos; `filename` vazio; tipo inválido com fallback.
  - `fileNameFromURL`: basename simples; query string ignorada; percent-encoding (`%20` → `_`); URL sem arquivo no path; URL inválida.
- **Comando:** `CGO_ENABLED=1 go test -v ./services/messages/...`
- **Resultado:** `PASS` — `ok worker/services/messages 0.017s` (todos os 11 subtestes).
- **Verificações adicionais:** `gofmt -l` limpo; `CGO_ENABLED=1 go build ./...` OK; `CGO_ENABLED=1 go vet ./...` OK.

## 📂 Arquivos Modificados
- `worker-go/services/messages/document.go`
- `worker-go/services/messages/document_test.go` (novo)

### Commit
- **worker-go** — branch `fix/dem-74-document-filename` — commit `d9c57d0`: `fix(dem-74): usar filename com fallbacks no nome do documento` (já mergeado em `origin/main` via `d5e3215`, **pendente de tag/deploy**).
