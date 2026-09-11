# 🤖 Diário de Bordo e Handover (Agente IA)

Este documento serve como o ponto de partida (memória) para a IA assim que iniciar uma nova sessão de trabalho. Ele contém o estado atual, o histórico recente e as pendências imediatas.

---

## 📌 Status Atual do Sistema (Snapshot)
- **Painel Kanban Local (`ai.context/demandas`)**: 100% estabilizado. Agora renderiza arquivos Markdown completos no Modal e possui integração via rota `/api/nova-demanda` para salvar direto no CSV.
- **Worker Go (`worker-go`)**: Rotas de Mídias estabilizadas. Uploads e Retrieves de Áudios PTT iOS agora fluem sem utilizar a tabela de `messages`.

---

## 🚀 O que foi feito nas Últimas Sessões

### Sessão: 11/09/2026 (Hoje)
- **DEM-65 (Playback iOS)**: Concluída. Corrigido encode do `ffmpeg` para arquivos PTT inserindo as flags `-ac 1 -ar 16000` (Mono, 16kHz). Push feito com sucesso para o GitLab.
- **DEM-46 (Retrieve 410 Áudios)**: Concluída. O worker tentava achar mídias recém-upadas na tabela `messages` causando erro. Substituímos para o padrão `client.DownloadMediaWithPath(...)`. Commit realizado localmente na branch `fix/dem-46-audio-retrieve`.
- **Painel Python (Kanban)**: Adicionado botão "+ Nova Demanda" e formulário. Eliminado os bugs de tela branca causados por Javascript cacheado e nulos no CSV.
- **⚠️ NOTA DE CONTEXTO (MUITO IMPORTANTE):** O cliente relatou que "a Task 65 consertou o retrieve de áudios". **Isso é uma percepção incorreta de testes (Race Condition/Confusão).** A Task 65 apenas mudou o formato do áudio. O Retrieve só foi de fato consertado pela DEM-46 (Opção A). Se o cliente relatar anomalias, saiba que o Retrieve de PTT agora usa a tabela `midias` isoladamente e é seguro.

---

## 🚧 Pendências e Próximos Passos (Para o próximo agente iniciar)
- [ ] **Retomar DEM-48**: O botão "Criar Instância" no Manager Service (`src/lib/subscription.ts`) continua ativo quando a assinatura vence. Precisa implementar bloqueio validando a data atual contra o `expiresIn`.
- [ ] **Commit Manager Service**: Validar e enviar as modificações pendentes no repositório `manager-service` referentes à branch `fix/demanda-1-delete-user` e arquivos novos criados.
- [ ] **Push da DEM-46**: O desenvolvedor precisa rodar `git push` no repositório do `worker-go` para subir a correção do retrieve.
