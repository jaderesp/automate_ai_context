---
id: DEM-89
status: concluido
data_conclusao: 2026-10-12 13:21:51
data_ativacao: 2026-10-10 10:32:59
modulo: API
---

# 🚀 Histórico de Execução: Erro ao fazzer retriveURL da imagem enviada como documento

## 📌 Resumo do Problema
Ao envia ruma imagem como documento, o webhook retorna o ID dela no payload. Porém ao fazer um retriveURL com o ID deessa mídia, dá erro:

Referente ao ticket: https://painel.uzapi.com.br/admin/support/f591cd90-dfd9-4d20-b78d-74b61791d716

## 🛠️ Solução Adotada

> **Estado (10/10/2026):** análise concluída por leitura de código; causa confirmada pelo corpo do erro informado pelo QA em 08/10 (`invalid media hmac`). **Nenhum código alterado; proposta aguardando aprovação.** Prioridade P2 (Cliente + Alta).

### Causa
`worker-go/services/medias.go` (`handleMediaURL`, linhas 112–165) escolhe a chave de descriptografia pelo **MIME** gravado na tabela `midias`: `utils.IsImage(mimeType)` → `whatsmeow.MediaImage`. Uma imagem enviada **como Documento** chega no protocolo como `DocumentMessage` com MIME `image/jpeg` ou `image/png`; a mídia foi cifrada com a chave derivada de `"WhatsApp Document Keys"`, mas o worker tenta `"WhatsApp Image Keys"` (`hkdfutil.SHA256(mediaKey, nil, []byte(appInfo), 112)`). O HMAC não confere e o `whatsmeow` devolve `failed to download media from last host: invalid media hmac`.

A tabela `midias` não guarda o tipo de mensagem de origem (só o MIME), por isso o worker não tem como distinguir "foto" de "imagem enviada como documento".

O `api-service` transforma qualquer erro do worker em **410** (`src/controllers/Midias/midia.controller.ts:309`: `result.code === '404' ? NOT_FOUND : GONE`), e o `rabbitmq/listener.go` descarta o mapa com `code` e devolve só `err.Error()`. Por isso o cliente vê 410 ("mídia expirada") para um erro que não é de expiração.

### Proposta (aguardando aprovação)
- **Opção A (recomendada):** em `handleMediaURL`, quando o download falhar com `whatsmeow.ErrInvalidMediaHMAC` usando a chave do MIME, repetir com `whatsmeow.MediaDocument` (e o inverso para documento). Não exige mudança de banco e recupera também as mídias **já gravadas**.
- **Opção B:** gravar o tipo de origem em nova coluna de `midias` e usá-lo no download. Mais limpo, porém exige migração no SQLite de cada instância e não resolve registros antigos sem a Opção A.
- Em conjunto com a DEM-92 (mesma função, mesma branch a partir da `dev`).

### Limites
Não reproduzido com envio real nesta sessão.

### Correção aplicada (11/10/2026) — Opção A, autorizada pelo desenvolvedor, commit `2832a20`
Repositório `worker-go`, branch `fix/dem-89-92-retrieve-media` (a partir da `dev` `d8ff536`), junto com a DEM-92.

Em `services/medias.go` (`handleMediaURL`): o `switch` por MIME define o `whatsmeow.MediaType` e o download é feito por `downloadMediaByType`. Se o erro for `whatsmeow.ErrInvalidMediaHMAC` (`errors.Is`) e o tipo escolhido não for `MediaDocument`, o download é repetido com `whatsmeow.MediaDocument` (chave `"WhatsApp Document Keys"`). Cobre imagem, vídeo e áudio enviados como Documento, inclusive registros já gravados em `midias`. Sem mudança de banco.

O caminho inverso (MIME de documento com chave de outro tipo) não foi implementado: não existe no protocolo um PDF/planilha trafegando como `ImageMessage`/`VideoMessage`.

Custo: no caso "imagem como documento" o arquivo cifrado é baixado duas vezes (a 1ª tentativa falha no HMAC); só na primeira consulta, pois depois o arquivo fica em `MEDIAS_PATH`.

### Fora do escopo (continua igual)
- Arquivo enviado como Documento com MIME fora das listas de `utils/processMidias.go` (ex.: `image/heic`) continua caindo em `unsupported file type for download`.
- O `api-service` continua devolvendo 410 para qualquer erro do worker que não seja 404.

### Validação
- `gofmt`, `go build`, `go vet ./services/`, `go test` (`services/messages`, `utils`, `webhook`): sem erros.
- **Não validado com envio real.**

### Roteiro para o QA (ambiente dev)
1. Enviar uma imagem **como Documento** para o número da instância.
2. Chamar Retrieve Media URL com o `id` do webhook → esperado 200 (antes: 410 com `invalid media hmac`).
3. Repetir com vídeo enviado como Documento e com uma foto normal (não deve mudar).

## 📂 Arquivos Modificados
- `worker-go/services/medias.go` (correção `2832a20` e ajuste da branch `fix/dem-89-document-direct-path`)

### Merge na `dev` (11/10/2026)
MR mergeado na `dev`, conforme informado pelo desenvolvedor (não conferido por fetch). Aguardando reteste do QA no ambiente dev.

### Reteste do QA em dev — REPROVADO (11/10/2026)
Ambiente `painel.dev.uzapi.com.br`, versão informada `v0.0.95-dev.5`. O erro mudou: o Retrieve Media URL fica alguns segundos e termina com `Erro interno ao recuperar a URL da mídia`.

Leitura do código: essa mensagem é o `catch` genérico de `api-service/src/controllers/Midias/midia.controller.ts:340` (HTTP 500), e o caminho que leva a ele depois de uma espera é o `Timeout waiting for response from RabbitMQ` de 30 s (`rabbitmq.service.ts:203`) — o worker não respondeu a tempo. Antes o worker respondia com erro (410).

Causa **não identificada**. Hipóteses a separar com o log do pod: (a) worker preso nas novas tentativas do `whatsmeow` (`downloadPossiblyEncryptedMediaWithRetries`: até 5 tentativas por host, com espera crescente, para erro de rede/5xx/429); (b) worker da instância não está consumindo a fila (pod reiniciando, desconectado ou em outra versão); (c) a hipótese do `mms-type` da DEM-92 estava incompleta. Falta saber se foto/PDF normais também dão timeout.

### Teste local (11/10/2026) — ainda não executado para este caso
A instância local foi repareada e o Retrieve Media URL funcionou para áudio (ver `DEM-92.md`), mas nenhuma imagem enviada como Documento foi localizada entre as mídias recebidas: as 40 imagens mais recentes eram do histórico e retornaram 403 (expiradas), sem nenhuma nova tentativa com chave de documento no log. Falta um envio novo de imagem como Documento com a instância conectada.

Versão conferida em 11/10/2026: merge `6b7f55e` na `dev` do `worker-go`, tag `v0.0.95-dev.5`, código idêntico ao commit `2832a20`.

## 🧪 Teste Prático e Homologação (local, 11/10/2026 16:42)
Instância local de teste, worker da branch `fix/dem-89-92-retrieve-media` (`2832a20`, mesmo código da `v0.0.95-dev.5`), chamada `media`/`url` direto na fila RabbitMQ.

- Mídia `454486836085021`: PNG de 3.649.365 bytes enviado como **Documento** (`mime_type` `image/png`, `direct_path` iniciando em `/v/t62.7119-24/`).
- Resultado: **`status: success`**, arquivo gravado — mas em **10,3 s**.
- Log: `Failed to download media: invalid media hmac, trying with next host...` 5 vezes (16:42:55 → 16:42:58) mais a falha no último host, depois `HMAC inválido com a chave do MIME image/png, tentando como documento` (16:43:02) e sucesso.
- Não regressão: 6 fotos comuns (0,2–0,4 s) e 1 PDF de 3,7 MB (1,0 s) retornaram com sucesso, sem nova tentativa.

### Achado: a nova tentativa funciona, mas é lenta
`DownloadMediaWithPath` (`whatsmeow/download.go:275-290`) só interrompe o laço de hosts para `ErrInvalidMediaSHA256`, 403, 404, 410 e cancelamento. `ErrInvalidMediaHMAC` faz o `whatsmeow` **baixar o arquivo inteiro de novo em cada host do CDN** (6 hosts neste teste) antes de devolver o erro; só então o worker tenta a chave de documento. O tempo desperdiçado cresce com o tamanho do arquivo e a rede: com arquivo maior ou rede mais lenta passa dos 30 s do `api-service` (`rabbitmq.service.ts:203`) e vira `Erro interno ao recuperar a URL da mídia`. É uma explicação plausível para o timeout que o QA viu em dev **neste caso (imagem como documento)**; não confirmada com o log de dev e não explica timeout em áudio de voz.

### Proposta de ajuste (aguardando aprovação)
O `direct_path` identifica o tipo de origem. Na tabela `midias` local (5.148 registros): `t62.7118-24` só imagem, `t62.7117-24`/`t62.7114-24` só áudio, `t62.7161-24` só vídeo, **`t62.7119-24` = documento** (31 PDFs e o PNG deste teste). Caminhos novos `/o1/v/t24/...` não trazem o tipo.
- Em `handleMediaURL`, se `direct_path` contiver `/t62.7119-24/`, usar `whatsmeow.MediaDocument` de primeira, independentemente do MIME. A nova tentativa por `ErrInvalidMediaHMAC` continua como rede de segurança para caminhos sem o tipo.
- 1 arquivo (`worker-go/services/medias.go`), nova branch a partir da `dev`.

### Ajuste aplicado (11/10/2026) — autorizado pelo desenvolvedor ("faça."), commit `ae7b5c0`
Repositório `worker-go`, branch `fix/dem-89-document-direct-path`, criada a partir da `dev` atual (`6b7f55e`, `v0.0.95-dev.5`). Arquivo: `services/medias.go`.

**O que mudou em `handleMediaURL`:**
1. Nova função `isDocumentDirectPath(directPath)`: retorna `true` quando o `direct_path` contém `/t62.7119-24/`, o bucket de documentos do CDN do WhatsApp.
2. O `switch` por MIME continua definindo o `whatsmeow.MediaType`. Depois dele, se o tipo escolhido não for `MediaDocument` e o caminho for de documento, a ordem é invertida: **`MediaDocument` passa a ser a primeira tentativa** e o tipo do MIME vira a segunda (`fallbackType`).
3. Nos demais casos nada muda: tipo do MIME primeiro, `MediaDocument` como segunda tentativa quando o erro é `whatsmeow.ErrInvalidMediaHMAC`.
4. O `switch` ganhou um `case isDocumentDirectPath(...)` antes do `default`: arquivo enviado como Documento com MIME fora das listas de `utils/processMidias.go` (ex.: `image/heic`) deixa de retornar `unsupported file type for download` quando o caminho indica documento. Isso resolve parte do item "Fora do escopo" registrado acima.
5. A mensagem de log da segunda tentativa passou a informar as duas chaves: `HMAC inválido com a chave <tipo> (MIME <mime>), tentando <tipo>: <arquivo>`.

**Por quê:** elimina, no caso comum, os downloads repetidos com a chave errada em todos os hosts do CDN (10,3 s no teste local com PNG de 3,6 MB), que podem estourar o timeout de 30 s do `api-service`.

**Limite conhecido:** mídias com `direct_path` no formato novo (`/o1/v/t24/...`) não trazem o tipo; para elas vale a ordem antiga (MIME primeiro), com a mesma lentidão se tiverem sido enviadas como Documento. Na base local esse formato apareceu só em imagens e vídeos do histórico, nenhum documento.

**Validação:** `gofmt`, `go build`, `go vet ./services/` e `go test` (`services/messages`, `utils`, `webhook`) sem erros. Worker local reiniciado com o ajuste. **Medição de tempo pendente**: depende de um novo envio de imagem como Documento (o PNG anterior já está em disco e não seria baixado de novo).

### Teste do ajuste (local, 11/10/2026)
Worker local compilado da branch `fix/dem-89-document-direct-path` (ajuste ainda sem commit), chamada `media`/`url` pela fila.
- Mídia `725211364102052`: JPEG de 673.791 bytes enviado como **Documento** (`mime_type` `image/jpeg`, `direct_path` em `/v/t62.7119-24/`).
- Resultado: **`status: success` em 0,6 s**, com **zero** ocorrências de `invalid media hmac` no log — a chave de documento foi usada de primeira.
- Comparação com o teste anterior (10,3 s, 6 falhas de HMAC): o arquivo anterior era um PNG de 3,6 MB, então os tempos não são diretamente comparáveis; o que o teste prova é a ausência das tentativas com a chave errada.

### Versão para reteste (11/10/2026)
Ajuste da DEM-89 (`ae7b5c0`) mergeado na `dev` pelo MR !15 → **`v0.0.95-dev.6`**, pipeline aprovada (informado pelo desenvolvedor). Aguardando reteste do QA nessa versão.

### Promoção para a `main` (12/10/2026)
Branch `fix/dem-89-92-retrieve-media-main`, criada da `main` (`363fb21`) com cherry-pick de `2832a20` (→ `54dab3c`) e `ae7b5c0` (→ `600eb88`); `services/medias.go` idêntico ao da `v0.0.95-dev.6` aprovada pelo QA. MR !16 mergeado na `main` (informado pelo desenvolvedor). Versão estável ainda não confirmada no momento do registro.

## ✅ Encerramento (12/10/2026)
- Correção aprovada pelo QA no ambiente dev (`worker-go v0.0.95-dev.6`).
- Promovida para produção pelo MR !16 na `main` do `worker-go`; versão estável **`v0.0.96`** (tag no commit de merge, pipeline #2939472895; dados colados pelo desenvolvedor).
- **Pendência operacional fora do código:** as instâncias de produção só recebem a correção quando forem atualizadas para a versão estável nova. Há um ticket de cliente com o mesmo erro da DEM-92 (instância "Murilo", `v0.0.95-dev2`) aguardando essa atualização.
- A `dev` e a `main` têm os mesmos dois commits com hashes diferentes (cherry-pick); o próximo merge `dev` → `main` deve reconhecer o conteúdo idêntico em `services/medias.go`.
