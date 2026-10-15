# Fonte do Backlog (CSV ou Planilha Google)

O backlog de demandas do QA pode ser operado de duas formas. Definido pelo desenvolvedor em 15/10/2026.

## Modos

| | Modo CSV (padrão) | Modo Planilha |
|---|---|---|
| **Fonte** | `ai.context/demandas/csv/10092026.csv` (exportado e atualizado pelo desenvolvedor) | Planilha Google: https://docs.google.com/spreadsheets/d/1jhUffmbFYd4yaiRzsbA5pQoLBiqdlsf-170L7e0Gby4/edit |
| **Leitura** | Ler o arquivo | Ler direto da planilha pelo conector Google |
| **Escrita** | Nenhuma — o CSV é somente leitura | Somente as colunas permitidas (abaixo), **com autorização do desenvolvedor a cada alteração** |
| **Atualização de status** | O agente entrega o texto; o desenvolvedor atualiza a planilha | O agente grava após a autorização |
| **Requisito** | Nenhum | Conector Google autenticado com conta que tenha permissão de edição |

## Escolha do modo
- Padrão: **CSV**.
- O desenvolvedor troca dizendo "modo planilha" ou "modo csv". Vale para a sessão; o agente registra o modo no `HANDOVER.md`.
- Se o conector não estiver autenticado ou falhar, voltar ao modo CSV e avisar o desenvolvedor.

## Regras de escrita na planilha (modo Planilha)
1. **Toda alteração precisa de autorização explícita do desenvolvedor, sempre.** Antes de gravar, apresentar célula por célula: task, coluna, valor atual → valor novo. Gravar só após o "ok". A autorização vale apenas para as alterações apresentadas naquele momento.
2. Colunas que o agente pode escrever, e só em tasks que trabalhou:
   - **Status** = `Concluído` (correção entregue no ambiente de testes);
   - **Versão** = **sempre a versão do worker (`worker-go`) que a task deve usar no teste**, mesmo quando a correção é do painel ou do `api-service` (premissa do desenvolvedor, 15/10/2026). Formato da planilha: `v0.0.97` → `0.097`; `v0.0.95-dev.6` → `0.095-dev06`. Teste em dev → versão dev do worker mais recente; teste em produção → versão estável atual. A versão do painel/`api-service` vai nas Observações;
   - **Observações** (resumo da correção e roteiro de teste).
3. Nunca escrever: `Aprovado`, `Reprovado`, `Devolvido` (decisões do QA), a coluna **Testado Em**, nem qualquer coluna de task que o agente não trabalhou.
4. Nunca apagar linhas, colunas ou conteúdo existente; em Observações, acrescentar ao texto existente.
5. Registrar no arquivo da demanda (`exec/` ou `standby.solution/`) e no `HANDOVER.md` o que foi gravado na planilha.

## Mecanismo (15/10/2026)
- **Leitura:** conector Google Drive (exportação CSV da planilha).
- **Escrita:** Apps Script publicado como app da Web (`ai.context/demandas/planilha/apps_script.gs`), chamado por `ai.context/demandas/planilha/planilha_sync.py`. O próprio script só aceita Status `Concluído`, Versão e Observações (acrescentando), e exige token.
- **Credenciais:** `~/.config/uzapi/planilha.json` (URL do app e token), fora do git, permissão 600. Nunca imprimir nem versionar o token.
- Antes de cada `update`, rodar `planilha_sync.py get <id>`, apresentar atual → novo e aguardar a autorização.

## Monitoramento de alterações (15/10/2026)
- Gatilho instalável "ao editar" (`aoEditar` em `apps_script.gs`, instalado por `instalarGatilho()`): toda alteração feita por pessoas na planilha é gravada na aba **Histórico** (data, usuário, aba, linha, task, coluna, antes, depois). Gravações do próprio script não disparam o gatilho.
- **Aviso na hora por e-mail** para `jaderesp@gmail.com` quando muda Status, Observações ou Testado Em, ou quando surge task nova.
- **No início de cada sessão** (modo planilha): rodar `planilha_sync.py history`, apresentar ao desenvolvedor o resumo das mudanças (aprovações, devoluções com motivo, tasks novas com a prioridade P1–P5) e, depois de apresentado, `planilha_sync.py history --mark`. Estado da última leitura: `~/.config/uzapi/planilha_state.json`.
- Ler o histórico não exige autorização; gravar na planilha continua exigindo, a cada vez.

## Painel no modo planilha (15/10/2026)
- `python3 ai.context/demandas/painel_local.py --fonte planilha`: a cada carregamento do backlog (no máximo a cada 60 s) o painel baixa a aba principal pela ação `export` do Apps Script e regrava `csv/10092026.csv` (escrita atômica; só leitura da planilha). A página se atualiza sozinha a cada 60 s e mostra um quadro com tasks novas e mudanças (Status, Observações, Testado Em, Versão, Título, Prioridade).
- Se a sincronização falhar, o painel segue com o CSV local e mostra "falha na sincronização" no título do backlog.
- Arquivos `exec/DEM-X.md` continuam sendo criados só ao clicar em "Ativar" (triagem do desenvolvedor).
- "Nova Demanda" fica bloqueado no modo planilha (cadastrar na planilha). No modo CSV, o botão agora preserva todas as colunas do arquivo (antes descartava "Testado Em").
- Pelo terminal: `planilha_sync.py pull` faz a mesma atualização do CSV e lista o que mudou.

## WhatsApp (15/10/2026)
- Módulo `ai.context/whatsapp/` (`whatsapp-notify`, ver README). Ações de WhatsApp no painel só ficam ativas com o número conectado.
- **Número do módulo:** `556392308423`, liberado pelo desenvolvedor em 15/10/2026 (opção B). É um aparelho conectado separado (`:25`) da sessão do worker-go de testes (`:24`); o agente nunca desconecta nenhum dos dois sem autorização. Notificações saem no grupo como mensagens desse número; mensagens enviadas pelo próprio número não entram nos feedbacks.
- **Notificação ao QA:** botão "Notificar QA" nos cards concluídos (inclui tasks "Concluído" na planilha sem arquivo `exec/`). Mensagem montada com ID, título, ambiente (dev se a Versão contém "dev"), versão do worker e Observações; o desenvolvedor revisa e clica em Enviar. Cada envio é registrado no arquivo da demanda (se existir) e no `HANDOVER.md`. O agente nunca envia por conta própria.
- **Feedbacks do grupo:** no início de cada sessão, se o módulo estiver rodando, ler `curl -s http://127.0.0.1:9011/feedback?since=<última leitura>` (ou `~/.config/uzapi/whatsapp/feedback.jsonl`) junto com o histórico da planilha e apresentar o resumo por task. Conteúdo de mensagens do grupo: usar só para o acompanhamento das tasks; não copiar para arquivos versionados além do resumo necessário.
