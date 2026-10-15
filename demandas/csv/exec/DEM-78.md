---
id: DEM-78
status: em_teste
data_ativacao: 2026-10-15 16:02:21
data_conclusao: 2026-10-15 16:20:00
modulo: Cupons
---

# 🚀 Histórico de Execução: Não lista todos usuários para associação do cupom

## 📌 Resumo do Problema
Parece que a lista de usuários (para serem associado à um cupom) está limitada. Não lista os novos usuários da plataforma. Assim, não consigo associar nvoos cupoms aos novos usuários.

## 🛠️ Solução Adotada
**Causa (arquitetura):** a rota `GET /api/users` do `manager-service` (`src/app/api/users/route.ts`), que alimenta os seletores de usuário do admin, fazia `db.select({ id, name, email }).from(user).limit(500)` (Drizzle ORM, tabela `user`), **sem `ORDER BY`**. O Postgres devolvia as 500 primeiras linhas na ordem física da tabela — na prática os cadastros mais antigos —, então qualquer usuário além do 500º não aparecia. A busca dos seletores é feita no navegador, sobre essa lista já cortada.

**Consumidores da rota (todos afetados):**
- `src/app/admin/coupons/components/coupon-modal.tsx:109` e `src/app/admin/coupons/page.tsx:156` — associação de cupom a usuário (**DEM-78**);
- `src/app/instances/components/user-selector.tsx:31` (`UserSelector`), usado em `src/app/admin/k8s/page.tsx:231` (visualização de pods do Kubernetes, **DEM-86**) e em `src/app/instances/page.tsx`.

**Correção (Opção A, autorizada em 14/10/2026):** removido o `.limit(500)` e adicionado `.orderBy(desc(user.createdAt))` (import de `desc` de `drizzle-orm`). A lista traz todos os usuários, dos mais novos para os mais antigos. Opção B (busca paginada no servidor) descartada: a consulta seleciona só 3 colunas (~100 bytes/usuário), suportando milhares de usuários sem impacto perceptível.

**Git:** branch `fix/dem-78-86-user-list-limit` (base `dev` `b5dd4f5`), commit `bdc20e6` (`fix(dem-78, dem-86): listar todos os usuários nos seletores do admin`), MR mergeado na `dev` como `5fd4784` → tag **`manager-service v0.3.59-dev.13`**. Promoção para a `main` ainda não feita (aguarda aprovação do QA).

## 📂 Arquivos Modificados
- `manager-service/src/app/api/users/route.ts`

## 🧪 Teste Prático e Homologação
- `tsc --noEmit` e `eslint` sem erros; hook de pré-commit OK.
- Sem teste em execução no ambiente local (a cópia local não tem mais de 500 usuários para reproduzir o corte).
- **Roteiro para o QA (dev, painel v0.3.59-dev.13; coluna Versão = worker `0.095-dev06`):** 1) entrar como admin → Cupons → criar/editar cupom; 2) no campo de usuários, procurar um usuário cadastrado recentemente; 3) conferir que aparece e pode ser associado.

## 📋 Backlog (planilha, 15/10/2026, autorizado)
Linha 79: Status `A Fazer` → `Concluído`, Versão `0.095` → `0.095-dev06`, Observações com resumo e roteiro. Obs.: o roteiro gravado na planilha cita "atribuir instância / filtros do admin" de forma genérica; o roteiro específico é o acima.

## 🗂️ Registro no Kanban
Arquivo gerado em 15/10/2026 pela ação "Ativar" do painel (`POST /api/ativar`) depois da conclusão, pois a task foi trabalhada sem ativação prévia.

---

## 🔁 Reclassificação (15/10/2026)
`status: concluido` → `em_teste` pela regra nova de etapas (`AGENTS.md`, seção 3: `concluido` só após aprovação do QA, promoção para a `main` e release): entregue só na `dev` (`manager-service v0.3.59-dev.13`), aguardando teste do QA.
