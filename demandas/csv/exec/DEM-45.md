---
id: DEM-45
status: concluido
data_ativacao: 2026-09-11 16:59:04
data_conclusao: 2026-09-11 18:39:00
modulo: API
---

# 🚀 Histórico de Execução: Retrieve de áudio PTT retorna 410 com “MediaKey não encontrada”

## 📌 Resumo do Problema
O retrieve de Áudios PTT (`handleMediaURL`) estava retornando erro (`sql: no rows in result set` -> `"mensagem com MediaKey não encontrada"`) quando solicitado logo após um upload via API.
Ao subir uma mídia via `/media/upload`, o `worker-go` armazena os metadados apenas na tabela `midias`. Contudo, o bloco lógico responsável por processar o tipo de Áudio (`case utils.IsAudio`) possuía um comportamento anômalo: ele tentava forçosamente localizar o áudio fazendo uma query na tabela `messages` (`database.GetMessageByMediaKey`).
Como a mídia recém-enviada ainda não era uma mensagem efetiva de um chat, o registro não existia na `messages`, lançando erro e falhando no retrieve (diferente de Imagens/PDFs, que nunca faziam essa checagem).

## 🛠️ Solução Adotada
A **Opção A** (Refatoração para Padrão de Recuperação de Mídia) foi implementada.
Foi removida toda a dependência que o `worker-go` tinha com a estrutura `waE2E.AudioMessage` e a tabela `messages` durante a fase de retrieve (`handleMediaURL`).
Em vez de baixar a mensagem chamando `client.Download(context.Background(), audioMsg)`, substituiu-se o bloco pelo uso explícito de `client.DownloadMediaWithPath(...)` em conjunto com a flag oficial `whatsmeow.MediaAudio`, equiparando o tratamento do áudio ao que já ocorria com sucesso para Imagens e Documentos.
Isso impede consultas sujas, limpa o código e mantém 100% da compatibilidade com a Cloud API.

## 📂 Arquivos Modificados
- `worker-go/services/medias.go`

---

## 🔎 Atualização 06/10/2026: situação real da entrega

> ⚠️ A correção descrita acima **nunca chegou à `main`**. O commit `91c14be` (`fix(media): remove dependência de 'messages' no retrieve de PTT (DEM-46)`, 11/09) existe apenas na branch local `fix/dem-45-audio-retrieve`, sem push, sem merge e sem tag.

- Em 06/10 o programador chefe (Eduardo) tratou o mesmo ponto por outro caminho, direto na `main`: commit `7c740e4`, release **`v0.0.94`** — `services/medias.go` passou a baixar o áudio com `client.DownloadMediaWithPath(...)` e `GetMessageByMediaKey` foi removida de `database/messageStore.go`. A branch local `fix/dem-45-audio-retrieve` ficou **obsoleta**.
- **Defeito observado na `v0.0.94` (presente também na `v0.0.95`):** o download de áudio pelo `id` de mídia (`GET /v1/{mediaId}`) retorna **410** (`download failed with status code 400`). No caso `utils.IsAudio` de `services/medias.go`, o parâmetro `mmsType` de `DownloadMediaWithPath` recebe o MIME (`audio/ogg; codecs=opus`). Reproduzido na instância de teste com um áudio recebido e com áudios enviados pela API (arquivos ainda não baixados em disco). Em cópia descartável, trocar o argumento por `"audio"` fez o download funcionar (121.743 bytes).
- **Situação:** o sintoma da demanda (retrieve de áudio PTT retornando 410) **não está resolvido** pelo que foi testado localmente. Correção de uma linha proposta e ainda **sem decisão**. O frontmatter foi mantido como `concluido`; revisar o status.
