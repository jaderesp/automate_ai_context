---
id: DEM-96
status: standby
data_ativacao: 2026-10-15 16:33:20
modulo: Meu Perfil
data_standby: 2026-10-15
aguardando: Eduardo
pendencia: decidir a correção da exclusão de conta (opção A colunas opcionais + migração, ou B cascade) e ajudar a confirmar a causa do "Unauthorized"
---

# 🚀 Histórico de Execução: Usuário não consegue excluir sua conta

## 📌 Resumo do Problema
Ao tentar excluir sua conta, usuário receber a mensagem "Unauthorized" mesmo informando o código de verificação corretamente.

OBS: AO TENTAR EXCLUIR ESSE MESMO USUÁRIO PELO ADMIN, APARECE MENSAGEM DE SUCESSO, PORÉM O MESMO NÃO É EXCLUÍDO.

## ⏸️ Standby / Aguardando Decisão (15/10/2026)
> **Motivo:** aguardando alinhamento com o Eduardo (alteração de schema com migração no banco de produção). Planilha: Bug, Alta, **Cliente** → **P2**. Análise só leitura na `origin/dev` do `manager-service` (`5fd4784`/`ec27a49`); nada alterado.

### Sintoma 2 — admin mostra sucesso e o usuário não é excluído (causa confirmada no código)
- **Banco (Drizzle/PostgreSQL):** `src/database/schemas/support-ticket-audit.schema.ts` (`actor_id`) e `src/database/schemas/support-ticket-messages.schema.ts` (`author_id`) são `text(...).notNull().references(() => user.id, { onDelete: "set null" })`. Ao apagar um usuário com ticket de suporte ou registro de auditoria, o Postgres tenta gravar `NULL` na coluna `NOT NULL` e recusa o `DELETE FROM "user"` (erro `23502 not_null_violation`). Usuários sem ticket são excluídos normalmente.
- **Tela do admin:** `src/app/admin/users/page.tsx:296` chama `authClient.admin.removeUser({ userId })` e mostra `toast.success(... foi removido)` sem conferir o `error` devolvido pelo Better Auth (o client não lança exceção; devolve `{ data, error }`).
- Mesma causa registrada na DEM-1 (correção de 14/09, commit local `cb6a568`, nunca publicada).

### Sintoma 1 — "Unauthorized" na exclusão pelo próprio usuário (causa não confirmada)
Fluxo: `src/app/dashboard/profile/profile-client.tsx:219` (`handleDeleteAccount`) → `DELETE /api/user/profile` (`src/app/api/user/profile/route.ts:126`):
1. `auth.api.getSession` → sem sessão devolve `401 {"error":"Unauthorized"}` (único ponto do código que gera esse texto);
2. conta com senha exige `password`; conta só Google exige `otp`, validado com `auth.api.verifyEmailOTP` (erro → 400 "Código de verificação inválido ou expirado");
3. apaga as instâncias no `api-service` e cancela as assinaturas no Asaas (erros ignorados) — **antes** de excluir o usuário;
4. `auth.api.deleteUser({ body: { password }, headers })` (Better Auth `^1.6.11`, `user.deleteUser.enabled: true` em `src/lib/auth.ts:113`), sem `try/catch`.

Hipóteses a confirmar (com log do servidor no momento do erro):
- **H1:** `verifyEmailOTP` serve para **verificação de e-mail**; ao ser usado como confirmação de exclusão, pode trocar/invalidar a sessão do usuário (auto login após verificação), e o `deleteUser` seguinte recebe uma sessão inválida → `UNAUTHORIZED` do Better Auth.
- **H2:** o `deleteUser` sem senha (conta Google) exige sessão "recente" (`freshAge` do Better Auth); sessão antiga → erro do Better Auth propagado sem tratamento.
- **H3:** o próprio `deleteUser` falha pelo mesmo `NOT NULL` do sintoma 2 (usuário com ticket) e o erro chega sem tratamento.
- **Efeito colateral grave:** como os passos 3 (instâncias e Asaas) rodam antes do `deleteUser`, uma falha no passo 4 deixa o usuário **existindo sem instâncias e sem assinatura** — compatível com o texto da DEM-1 ("excluiu a conta do usuário e sua assinatura no Asaas").

### Proposta (aguardando o Eduardo)
**Opção A (recomendada)** — branch `fix/dem-96-user-deletion` a partir da `dev`:
1. Schema: remover `.notNull()` de `actorId`/`authorId` + migração Drizzle (`ALTER TABLE support_ticket_audit ALTER COLUMN actor_id DROP NOT NULL;` idem `support_ticket_messages.author_id`); exibir "Usuário removido" quando o autor for nulo nas telas de suporte.
2. Admin: conferir `error` de `removeUser` e mostrar a mensagem real.
3. Autoexclusão: validar senha/OTP e **excluir o usuário primeiro** (ou numa transação), e só depois limpar instâncias e Asaas; envolver `deleteUser` em `try/catch` devolvendo a mensagem do Better Auth; confirmar H1/H2 e, se for o caso, trocar a confirmação por OTP pelo fluxo próprio de exclusão do Better Auth (`sendDeleteAccountVerification`) ou validar o OTP sem mexer na sessão.
- Prós: resolve DEM-96 e o caso pendente da DEM-1; evita conta "meio excluída". Contras: migração em produção (precisa de aval); muda telas de suporte.

**Opção B** — excluir em cascata (`onDelete: "cascade"`) os registros de suporte do usuário: mais simples, mas **apaga o histórico de atendimento**, o que costuma ser indesejado para auditoria.

### Para decidir com o Eduardo
1. Pode alterar as duas colunas e rodar a migração em produção? (A ou B)
2. Histórico de suporte de usuário excluído deve ser mantido (A) ou apagado (B)?
3. Log do `manager-service` no horário do "Unauthorized" relatado, para confirmar H1–H3.

## 🛠️ Solução Adotada
(IA preencherá este campo após autorização)

## 📂 Arquivos Modificados
- (A preencher)


### 📣 WhatsApp: cobrança de alinhamento enviada ao grupo (16/10/2026 11:04)
```
⏸️ *Task #96 aguardando alinhamento*
📌 Usuário não consegue excluir sua conta
👤 @259824130470069, pode me dar um retorno?
❓ decidir a correção da exclusão de conta (opção A colunas opcionais + migração, ou B cascade) e ajudar a confirmar a causa do "Unauthorized"
⏳ Em standby desde 15/10/2026
```
