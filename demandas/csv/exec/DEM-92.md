---
id: DEM-92
status: concluido
data_conclusao: 2026-10-12 13:21:51
data_ativacao: 2026-10-10 10:32:59
modulo: API
---

# 🚀 Histórico de Execução: Erro 410 ao fazer retriveURL em midia de áudio de voz

## 📌 Resumo do Problema
Ao tentar fazer retriveURL com id de um áudio de voz retornando no payload do webhook, dá erro 410: error downloading media: failed to download media from last host: download failed with status code 400

Referente aos tickets:

https://painel.uzapi.com.br/admin/support/761adbdf-eb6e-4be5-8e5e-86a440bab088

https://painel.uzapi.com.br/admin/support/50920f55-088b-4337-a621-0802afbe9cbd

## 🛠️ Solução Adotada

> **Estado (10/10/2026):** análise concluída por leitura de código. **Nenhum código alterado; proposta aguardando aprovação.** Não reproduzido com envio real. Prioridade P1 (Cliente + Urgente).

### Causa provável (regressão de 06/10/2026)
O commit `7c740e4` (`refactor(medias): simplificar download de áudio com DownloadMediaWithPath`, 06/10/2026 16:56), presente a partir da **`v0.0.94`**, trocou o download de áudio em `worker-go/services/medias.go`:

- **Antes:** `client.Download(ctx, audioMsg)` — o `whatsmeow` usava o tipo MMS interno `"audio"`.
- **Depois (linhas 137–149):** `client.DownloadMediaWithPath(..., whatsmeow.MediaAudio, mimeType, false)` — o 7º parâmetro é o `mmsType`, e está recebendo o **MIME**.

No `whatsmeow` (`download.go:277`) o `mmsType` entra cru na URL:
`fmt.Sprintf("https://%s%s&hash=%s&mms-type=%s&__wa-mms=", host, directPath, hash, mmsType)`.
Áudio de voz tem MIME `audio/ogg; codecs=opus`: o espaço e o `;` quebram a query string e o CDN do WhatsApp responde **HTTP 400** → `failed to download media from last host: download failed with status code 400`, exatamente o texto do ticket. Imagem e vídeo também passam o MIME (`image/jpeg`, `video/mp4`), mas sem espaço, e o CDN aceita.

O `api-service` devolve 410 para qualquer erro do worker que não seja 404 (`midia.controller.ts:309`), por isso o cliente recebe 410.

Relação com a DEM-45 (410 em áudios, concluída em setembro): mesmo endpoint, causa diferente; esta é uma regressão posterior.

### Proposta (aguardando aprovação)
Passar `""` como `mmsType` nos quatro `DownloadMediaWithPath` de `handleMediaURL`: com o parâmetro vazio o `whatsmeow` usa a tabela oficial (`mediaTypeToMMSType`: `image`, `audio`, `video`, `document`). Alteração de 4 linhas, na mesma branch da DEM-89, a partir da `dev`.

### Validação prevista
Instância local de teste: receber áudio de voz, chamar Retrieve Media URL com o `id` do webhook e conferir 200 antes/depois da correção.

### Correção aplicada (11/10/2026) — autorizada pelo desenvolvedor, commit `2832a20`
Repositório `worker-go`, branch `fix/dem-89-92-retrieve-media` criada a partir da `dev` (`d8ff536`).

Em `services/medias.go`, as quatro chamadas duplicadas de `DownloadMediaWithPath` em `handleMediaURL` viraram uma função única, `downloadMediaByType(client, mediaData, mediaType)`, que passa `""` como `mmsType`. Com o parâmetro vazio o `whatsmeow` (`download.go:272`) usa `mediaTypeToMMSType[mediaType]` (`image`, `audio`, `video`, `document`), o mesmo valor que `client.Download` usava antes do commit `7c740e4`. O `switch` por MIME passou a escolher apenas o `whatsmeow.MediaType`.

### Validação
- `gofmt`, `go build` (todos os pacotes exceto a raiz, que tem arquivos locais não versionados com `main` duplicado), `go vet ./services/` e `go test` (`services/messages`, `utils`, `webhook`): sem erros.
- **Não validado com envio real**: a causa (MIME na query string → HTTP 400) segue como hipótese sustentada por leitura de código. Só o reteste do QA no ambiente dev confirma.

### Roteiro para o QA (ambiente dev)
1. Enviar um áudio de voz (gravado no app) para o número da instância.
2. Pegar o `id` do áudio no payload do webhook.
3. Chamar Retrieve Media URL com esse `id` → esperado 200 com `mime_type` `audio/ogg; codecs=opus`.
4. Repetir com imagem, vídeo e PDF para conferir que não houve regressão.

## 📂 Arquivos Modificados
- `worker-go/services/medias.go`

### Merge na `dev` (11/10/2026)
MR mergeado na `dev`, conforme informado pelo desenvolvedor (não conferido por fetch). Aguardando reteste do QA no ambiente dev.

### Reteste do QA em dev — REPROVADO (11/10/2026)
Ambiente `painel.dev.uzapi.com.br`, versão informada `v0.0.95-dev.5`. O erro mudou: o Retrieve Media URL fica alguns segundos e termina com `Erro interno ao recuperar a URL da mídia`.

Leitura do código: essa mensagem é o `catch` genérico de `api-service/src/controllers/Midias/midia.controller.ts:340` (HTTP 500), e o caminho que leva a ele depois de uma espera é o `Timeout waiting for response from RabbitMQ` de 30 s (`rabbitmq.service.ts:203`) — o worker não respondeu a tempo. Antes o worker respondia com erro (410).

Causa **não identificada**. Hipóteses a separar com o log do pod: (a) worker preso nas novas tentativas do `whatsmeow` (`downloadPossiblyEncryptedMediaWithRetries`: até 5 tentativas por host, com espera crescente, para erro de rede/5xx/429); (b) worker da instância não está consumindo a fila (pod reiniciando, desconectado ou em outra versão); (c) a hipótese do `mms-type` da DEM-92 estava incompleta. Falta saber se foto/PDF normais também dão timeout.

## 🧪 Teste Prático e Homologação (local, 11/10/2026 16:20–16:27)
Instância local de teste (`ai.context/examples/instance`, `PHONE_NUMBER_ID` `999999999999999`), device repareado por QR pelo desenvolvedor. Chamadas feitas direto na fila RabbitMQ, no mesmo envelope do `api-service` (`{"pattern":"media","data":{"mediaId":"<id>","action":"url","endpoint":"media","type":"media"}}` com `reply_to`/`correlation_id`); o `api-service` não participou.

| Binário | Áudios `audio/ogg; codecs=opus` consultados | Resultado |
|---|---|---|
| Branch `fix/dem-89-92-retrieve-media` (`2832a20`) | 8 mais recentes | **6 `status: success`** em 0,2–1,2 s (arquivo `.ogg` gravado em `medias/`); 2 com `download failed with status code 403` (mídia antiga, expirada no CDN) |
| `origin/dev` sem a correção (`7c297ce`, compilado fora do repositório) | 14 seguintes | **14 de 14** com `failed to download media from last host: download failed with status code 400` — o texto do ticket |
| Branch da correção, os mesmos 14 | 14 | 14 com `403` (expiradas): o 400 sumiu e o CDN passou a responder o estado real da mídia |

Conclusão: o erro 400 do ticket foi reproduzido com o código sem a correção e não ocorre com ela. Limite: não houve par "mesmo áudio falha antes / funciona depois", porque os 6 que funcionaram ficaram em disco; a comparação é entre lotes.

**Divergência com o ambiente dev:** o QA relatou timeout (`Erro interno ao recuperar a URL da mídia`) na `v0.0.95-dev.5`. No teste local o worker respondeu em menos de 2 s em todos os casos, então o timeout de dev não foi reproduzido e segue sem causa: falta confirmar se a `v0.0.95-dev.5` contém o commit `2832a20`, se o worker da instância testada estava consumindo a fila e se mídia comum também dá timeout lá.

Versão conferida em 11/10/2026: merge `6b7f55e` na `dev` do `worker-go`, tag `v0.0.95-dev.5`, código idêntico ao commit `2832a20`.

### Versão para reteste (11/10/2026)
Ajuste da DEM-89 (`ae7b5c0`) mergeado na `dev` pelo MR !15 → **`v0.0.95-dev.6`**, pipeline aprovada (informado pelo desenvolvedor). Aguardando reteste do QA nessa versão.

### Promoção para a `main` (12/10/2026)
Branch `fix/dem-89-92-retrieve-media-main`, criada da `main` (`363fb21`) com cherry-pick de `2832a20` (→ `54dab3c`) e `ae7b5c0` (→ `600eb88`); `services/medias.go` idêntico ao da `v0.0.95-dev.6` aprovada pelo QA. MR !16 mergeado na `main` (informado pelo desenvolvedor). Versão estável ainda não confirmada no momento do registro.

## ✅ Encerramento (12/10/2026)
- Correção aprovada pelo QA no ambiente dev (`worker-go v0.0.95-dev.6`).
- Promovida para produção pelo MR !16 na `main` do `worker-go`; versão estável **`v0.0.96`** (tag no commit de merge, pipeline #2939472895; dados colados pelo desenvolvedor).
- **Pendência operacional fora do código:** as instâncias de produção só recebem a correção quando forem atualizadas para a versão estável nova. Há um ticket de cliente com o mesmo erro da DEM-92 (instância "Murilo", `v0.0.95-dev2`) aguardando essa atualização.
- A `dev` e a `main` têm os mesmos dois commits com hashes diferentes (cherry-pick); o próximo merge `dev` → `main` deve reconhecer o conteúdo idêntico em `services/medias.go`.
