---
id: DEM-90
status: concluido
data_ativacao: 2026-10-15 16:02:21
data_conclusao: 2026-10-15 16:20:00
modulo: Usuários
data_producao: 2026-10-16
versao_producao: manager-service v0.3.61
versao_worker: v0.0.98
---

# 🚀 Histórico de Execução: Limitação na contagem de usuários

## 📌 Resumo do Problema
A contagem de usuários stá sendo limitada em 1.000

## 🛠️ Solução Adotada
**Causa (arquitetura):** duas rotas do `manager-service` limitavam a consulta a 1000 linhas (Drizzle ORM, `db.select(...).from(user).leftJoin(userBilling, eq(user.id, userBilling.userId)).orderBy(desc(user.createdAt)).limit(1000)`, tabelas `user` e `user_billing`, join por `user_billing.user_id` → `user.id`):
- `src/app/api/admin/users/route.ts:48` — lista do admin. A tela `src/app/admin/users/page.tsx` exibe `{users.length} usuários cadastrados` (linha 504), por isso o total travava em 1000; a paginação (TanStack Table, `pageSize: 20`) e a busca rodam no navegador sobre a lista já cortada, então os cadastros mais antigos que o 1000º não apareciam nem na busca. A mesma rota é usada em `src/app/admin/support/[ticketId]/page.tsx:277` para listar os atendentes (filtra `role === "admin"`), que também podia perder admins.
- `src/app/api/admin/users/export/route.ts:43` — exportação em Excel (`xlsx`), que saía cortada em 1000 linhas.

**Correção (Opção A, autorizada em 15/10/2026):** removido o `.limit(1000)` das duas consultas; ordenação `createdAt desc` mantida. Mesma abordagem da DEM-78/86. Opção B (paginação, busca e total no servidor, com reescrita da tabela) descartada por ora: cada linha tem ~0,5 KB, então alguns milhares de usuários somam poucos MB; vale revisitar se a base chegar a dezenas de milhares.

**Git:** branch `fix/dem-90-admin-users-limit` (base `dev` `5fd4784`), commit `fb7ca3d` (`fix(dem-90): listar e exportar todos os usuários no admin`), MR mergeado na `dev` como `ec27a49` → tag **`manager-service v0.3.59-dev.14`**. Promoção para a `main` ainda não feita (aguarda aprovação do QA).

## 📂 Arquivos Modificados
- `manager-service/src/app/api/admin/users/route.ts`
- `manager-service/src/app/api/admin/users/export/route.ts`

## 🧪 Teste Prático e Homologação
- `tsc --noEmit` e `eslint` sem erros; hook de pré-commit (`eslint --fix --max-warnings=0`) OK.
- Sem teste em execução no ambiente local (a cópia local não tem mais de 1000 usuários).
- **Roteiro para o QA (dev, painel v0.3.59-dev.14; coluna Versão = worker `0.095-dev06`):** 1) entrar como admin → Usuários e conferir que o total mostra o número real (acima de 1000); 2) buscar um usuário antigo e conferir que aparece; 3) clicar em Exportar e conferir que a planilha traz todos.

## 📋 Backlog (planilha, 15/10/2026, autorizado)
Linha 91: Status `A Fazer` → `Concluído`, Versão `0.095` → `0.095-dev06`, Observações com resumo e roteiro (cita `v0.3.59-dev.14`, confirmada depois no git).

## 🗂️ Registro no Kanban
Arquivo gerado em 15/10/2026 pela ação "Ativar" do painel (`POST /api/ativar`) depois da conclusão, pois a task foi trabalhada sem ativação prévia.

---

## 🔁 Reclassificação (15/10/2026)
`status: concluido` → `em_teste` pela regra nova de etapas (`AGENTS.md`, seção 3: `concluido` só após aprovação do QA, promoção para a `main` e release): entregue só na `dev` (`manager-service v0.3.59-dev.14`), aguardando teste do QA.

## 🚀 Promoção para produção (16/10/2026)
- QA aprovou no dev em 15/10 (planilha `Aprovado`; grupo: total real, busca de usuário antigo e exportação OK).
- `manager-service` branch `promote/dem-80-90-prod` a partir da `main` `b9d70ba` (`v0.3.60`): `git cherry-pick -x fb7ca3d` → `01a205e` (aplicou limpo), junto com `13b63c0` → `03ee865` (DEM-80/91). Diff contra a `main`: só `admin/users/route.ts`, `admin/users/export/route.ts` e `api/instances/route.ts`.
- `tsc --noEmit` e `eslint` nos 3 arquivos: OK.
- MR !31 mergeado na `main` (pais `b9d70ba` + `03ee865`), tag **`v0.3.61`** (informado pelo desenvolvedor). Pipeline/deploy da tag não verificados daqui.


### 📣 WhatsApp: aviso de produção enviada ao grupo (16/10/2026 10:28)
```
🚀 *Task #90 em produção*
📌 Limitação na contagem de usuários
📦 Versão: manager-service v0.3.61
Já disponível para os clientes.
```
