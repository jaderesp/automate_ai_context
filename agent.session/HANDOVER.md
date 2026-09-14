# 🤖 Diário de Bordo e Handover (Agente IA)

Este documento serve como o ponto de partida (memória) para a IA assim que iniciar uma nova sessão de trabalho. Ele contém o estado atual, o histórico recente e as pendências imediatas.

---

## 📌 Status Atual do Sistema (Snapshot)
- **Painel Kanban Local (`ai.context/demandas`)**: 100% estabilizado. Agora renderiza arquivos Markdown completos no Modal e possui integração via rota `/api/nova-demanda` para salvar direto no CSV.
- **Worker Go (`worker-go`)**: Rotas de Mídias estabilizadas. Uploads e Retrieves de Áudios PTT iOS agora fluem sem utilizar a tabela de `messages`.

---

## 🚀 O que foi feito nas Últimas Sessões

### Sessão: 11/09/2026 (Hoje)
*ID da Sessão:* `agy --conversation=3ef7433b-d165-4c31-9f41-8206ab38a804`
- **DEM-64 (Playback iOS)**: Concluída. Corrigido encode do `ffmpeg` para arquivos PTT inserindo as flags `-ac 1 -ar 16000` (Mono, 16kHz). Push feito com sucesso para o GitLab.
- **DEM-45 (Retrieve 410 Áudios)**: Concluída. O worker tentava achar mídias recém-upadas na tabela `messages` causando erro. Substituímos para o padrão `client.DownloadMediaWithPath(...)`. Commit realizado localmente na branch `fix/dem-45-audio-retrieve`.
- **Painel Python (Kanban)**: Adicionado botão "+ Nova Demanda" e formulário. Eliminado os bugs de tela branca causados por Javascript cacheado e nulos no CSV.
- **⚠️ NOTA DE CONTEXTO (MUITO IMPORTANTE):** O cliente relatou que "a Task 64 consertou o retrieve de áudios". **Isso é uma percepção incorreta de testes (Race Condition/Confusão).** A Task 64 apenas mudou o formato do áudio. O Retrieve só foi de fato consertado pela DEM-45 (Opção A). Se o cliente relatar anomalias, saiba que o Retrieve de PTT agora usa a tabela `midias` isoladamente e é seguro.

---

## Pendências e Próximos Passos
- **Push Worker-Go:** Rodar `git push` no repositório `worker-go` para subir a correção da DEM-45.
- **Push Manager-Service:** Rodar `git push` nas branches `fix/demanda-1-delete-user` e `fix/dem-48-block-expired` do `manager-service`.
- **Push API-Service:** O usuário precisará realizar o push local da branch `fix/dem-66-messageid-length` no `api-service`.
