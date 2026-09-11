---
id: DEM-46
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
