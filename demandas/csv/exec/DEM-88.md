---
id: DEM-88
status: concluido
data_ativacao: 2026-10-09 12:09:00
data_conclusao: 2026-10-09 14:44:00
modulo: API
---

# 🚀 Histórico de Execução: Erro ao responder a mensagem

## 📌 Resumo do Problema
Ao enviar texto com "context": {"message_id": "<id>"}, que é o único campo do esquema Context no Swagger de vocês, a mensagem chega ao destinatário citando a si mesma (o balão da citação mostra o texto da própria resposta), e não a mensagem do id informado. Testamos com o id de uma mensagem recebida do cliente (AC22E072C023E0FC7516328023BFA199). Como enviar uma resposta citando corretamente uma mensagem anterior?



## 🛠️ Solução Adotada

> **Estado (09/10/2026):** commit `668d678` na branch `fix/dem-88-reply-context` do `worker-go`, a partir da `main` local `363fb21` (`v0.0.95`). **Sem push.** `status` segue `pendente` até o merge e a liberação. A `main` remota não pôde ser conferida nesta sessão (sem `git fetch`).

### Causa
O envio com `"context": {"message_id": "<id>"}` (formato da API oficial) é lido em `ParseSendOptions` (`worker-go/services/messages/helpers.go`) e vira `options.Context.MessageID`. Cada função de envio montava o `ContextInfo` do protocolo por conta própria. Em `services/messages/text.go` (linhas 108–117 antes da correção, trecho de `5c2075c`, 16/12/2025):

```go
participantJID := client.Store.ID.String()
textMessage.ContextInfo = &waProto.ContextInfo{
    StanzaID:    options.Context.MessageID,
    Participant: &participantJID,
    QuotedMessage: &waProto.Message{
        Conversation: proto.String(body),
    },
}
```

Dois erros:
1. **`QuotedMessage` recebia `body`, o texto da própria resposta.** O WhatsApp desenha o balão de citação a partir do `QuotedMessage` enviado junto, não buscando a mensagem pelo `StanzaID`; por isso o destinatário via a resposta "citando a si mesma" — o relato do cliente.
2. **`Participant` (autor da mensagem citada) era sempre o JID da instância** (`client.Store.ID`, inclusive com o sufixo de device), mesmo ao responder uma mensagem recebida do contato. Esse segundo erro se repetia em `image.go`, `audio.go`, `video.go`, `document.go`, `sticker.go`, `contact.go` e `location.go`, que não enviavam `QuotedMessage` algum.

### Correção
- Nova função `BuildReplyContext(client, chat, options)` em `services/messages/helpers.go`:
  - lê a mensagem original na tabela `messages` do SQLite da instância (`database.GetMessageByID`, chave `id`);
  - `QuotedMessage` = conteúdo original (`webhook.StoredToProto`), clonado e sem o `ContextInfo` que a original carregava (não se encadeia citação);
  - `Participant` = autor original: a instância quando `Info.IsFromMe`, senão `Info.Sender` sem o device (pode ser `@lid`);
  - `StanzaID` = `message_id` informado.
- **Mensagem não encontrada no SQLite, ou registro sem conteúdo (stubs antigos da DEM-66):** retorna `nil` e a mensagem é enviada **sem citação**, com um aviso no log (`Mensagem citada não encontrada; enviando sem citação`). Decisão do desenvolvedor após ver no aparelho o balão vazio da primeira versão.
- Os oito tipos de envio passaram a usar a função. `webhook.storedToProto` foi exportada como `StoredToProto` para reaproveitamento.
- O contrato da API não muda (`context.message_id`); não há alteração no `api-service`.

### Limites conhecidos
- A citação depende de a mensagem original estar no SQLite da instância. Mensagens anteriores ao pareamento, ou de instância recriada, saem sem citação.
- `poll` e `interactive` não tratam `context` (já não tratavam).

## 🧪 Teste Prático e Homologação

**Unitário** (`services/messages/reply_context_test.go`, fora do git por regra do projeto): mensagem recebida, mensagem enviada pela instância, grupo com citação aninhada, sem registro, registro vazio, sem `context`. `go test ./services/messages/ ./webhook/ ./database/` OK; `go build` e `go vet` OK.

**Aparelho real** — instância de teste local (`ai.context/examples/instance`, device `556392308423`), publicando na fila `API-WhatsApp` no envelope do `api-service`, destino `5516997141457`, em 09/10/2026:

```json
{"endpoint":"messages","type":"text","to":"5516997141457",
 "text":{"body":"[DEM-88 teste 1] resposta a uma mensagem RECEBIDA"},
 "context":{"message_id":"3EB02E5BBAF11CCEF4F97E"}}
```

| # | Hora | Envio | ID gerado | Citação gravada | No aparelho |
|---|---|---|---|---|---|
| 1 | 12:14 | texto → mensagem recebida | `3EB0EADF3696EFB1418098` | texto original, autor `194334435573950@lid` (o contato) | citação correta (confirmado pelo desenvolvedor) |
| 2 | 12:14 | texto → mensagem enviada pela API | `3EB03AB8158653BFDE2D80` | `documentMessage` original, autor `556392308423@s.whatsapp.net` | citação correta (confirmado) |
| 3 | 12:14 | texto → ID inexistente (1ª versão) | `3EB0A9DFCBF07956E7300C` | texto vazio | balão vazio — rejeitado |
| 4 | 12:14 | imagem → mensagem recebida | `3EB01DF0D6376F009D1F1B` | texto original, autor o contato | citação correta (confirmado) |
| 5 | 12:18 | texto → ID inexistente (versão final) | `3EB05C85BDEA2F13E8C6A5` | nenhuma (`contextInfo` ausente) + aviso no log | não conferido visualmente |
| 6 | 12:18 | texto → mensagem recebida (versão final) | `3EB060B7E97371E6ACAB68` | texto original, autor o contato | não conferido visualmente |

**Não testado:** resposta em grupo com envio real; áudio, vídeo, documento, figurinha, contato e localização com envio real (mesma função, cobertos só pela compilação).

**Roteiro para o QA:** enviar `POST /v1/{phone_number_id}/messages` com `context.message_id` de (a) uma mensagem recebida, (b) uma enviada pela API, (c) em grupo, de outro participante; o balão deve mostrar o conteúdo e o autor da mensagem original.

### Liberação
Push → MR → merge → release do `worker-go` → **atualizar a versão das instâncias** (`appVersion`), senão a correção não chega aos clientes.

## 📂 Arquivos Modificados
- `worker-go/services/messages/helpers.go` (nova `BuildReplyContext`)
- `worker-go/services/messages/text.go`, `image.go`, `audio.go`, `video.go`, `document.go`, `sticker.go`, `contact.go`, `location.go`
- `worker-go/webhook/messageObject.go` (`StoredToProto` exportada)

---

## 🔀 Merge na `dev` (09/10/2026)

- O desenvolvedor informou que o MR da branch `fix/dem-88-reply-context` (`668d678`) foi mergeado na branch **`dev`** do `worker-go`. Não verificado daqui (sem `git fetch` nesta sessão).
- **Fluxo novo do `worker-go` (pipeline da `dev`, lida em `origin/dev` `e3e6947`):** merge em `dev` gera a tag `vX.Y.Z-devN` e a imagem correspondente; merge em `main` gera a versão estável. A pipeline roda `go vet ./...` e `go test ./...`. Não há deploy pela CI: a versão das instâncias é atualizada à parte. `./release.sh` manual deixou de ser o caminho.
- **Situação:** entregue para homologação no ambiente de desenvolvimento. Falta a promoção `dev` → `main` e a atualização da versão das instâncias em produção. `status` segue `pendente` até o desenvolvedor indicar o critério de conclusão neste fluxo novo.
- **Confirmado em 09/10 (após `git pull` do desenvolvedor):** merge `76481c9` (`Merge branch 'fix/dem-88-reply-context' into 'dev'`) na `dev` do `worker-go`, com a tag **`v0.0.95-dev2`** gerada pela pipeline. Na `dev` local (`76481c9`), `go build` e `go test ./services/messages/ ./webhook/` passam. Pendente: homologação no ambiente de desenvolvimento e promoção `dev` → `main`.

---

## ✅ Encerramento (09/10/2026)

- O desenvolvedor informou em 09/10/2026 que a demanda está **resolvida**; `status` alterado para `concluido`.
- Entrega: commit `668d678`, merge `76481c9` na `dev` do `worker-go`, versão **`v0.0.95-dev2`**.
- **Não verificado nesta sessão:** resultado do reteste do QA, promoção `dev` → `main` (a `main` local segue em `363fb21`/`v0.0.95`) e atualização da versão das instâncias em produção. A correção só chega aos clientes depois da versão estável e da atualização do `appVersion` das instâncias.

---

## 🚀 Promoção para a `main` (13/10/2026)

- **Devolução do QA em 13/10** ("quando vai responder um usuário ela responde a si mesma"): o teste havia sido feito na `0.096`, que não continha a correção (`cb1e56f`/`668d678` estavam só na `dev`). O sintoma descrito é o do código antigo (`text.go:114` da `main`, `QuotedMessage` com o corpo da própria resposta). Nenhuma alteração de código foi necessária.
- **Reteste do QA no ambiente dev, `v0.0.95-dev.6`: aprovado** (informado pelo desenvolvedor em 13/10).
- **Promoção (regra do programador chefe):** branch `fix/dem-88-reply-context-main` criada da `main` `8a22857` (`v0.0.96`), com cherry-pick do `668d678` → commit `262c62a` (os mesmos 10 arquivos, sem conflito; a `main` não havia alterado nenhum deles). `go build`, `go vet` e `go test ./...` OK numa cópia só com os arquivos versionados.
- **MR mergeado na `main` do `worker-go`:** merge `92482e5` (conferido após `git pull` do desenvolvedor).
- **Versão estável: `v0.0.97`**, tag criada pelo desenvolvedor com `./release.sh` sobre o merge `92482e5` (a pipeline da `main` do `worker-go` não cria tag no merge; build e imagem rodam só em tags). Tag conferida no git local; pipeline da tag confirmada pelo desenvolvedor.
- **Encerramento definitivo:** o desenvolvedor informou que a DEM-88 está concluída e validada em produção (`worker-go v0.0.97`). `status: concluido` mantido.
