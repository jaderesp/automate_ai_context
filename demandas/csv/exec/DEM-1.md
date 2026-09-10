---
id: DEM-1
status: concluido
data_ativacao: 2026-09-10 15:37:09
data_conclusao: 2026-09-10 18:55:00
modulo: Usuários
---

# 🚀 Histórico de Execução: Não exclui usuário

## 📌 Resumo do Problema
O painel administrativo exibia "Sucesso" ao clicar em "Remover Conta", mas o usuário continuava ativo. O frontend mascarava o erro do backend. A falha no servidor era um erro de restrição do banco de dados (erro 500) causado por um conflito no schema (Drizzle): tabelas de logs e mensagens forçavam `notNull()` enquanto a chave estrangeira (FK) tentava aplicar `onDelete: "set null"`.

## 🛠️ Solução Adotada
1. Tratamento de erro injetado no Frontend para exibir alertas reais caso o servidor falhe.
2. Remoção do `.notNull()` das colunas `actorId` e `authorId` nas tabelas `support-ticket-audit` e `support-ticket-messages`.
3. Injeção da coluna `impersonatedBy` na tabela `session` exigida pela versão atual do Better Auth.
4. Adição de `.catch` no envio de email OTP (auth.ts) para evitar crashes do servidor NodeJS local sem SMTP.
5. Push do Schema via `drizzle-kit` para aplicar as cascatas no banco.

## 📂 Arquivos Modificados
- `manager-service/src/app/admin/users/page.tsx`
- `manager-service/src/database/schemas/support-ticket-audit.schema.ts`
- `manager-service/src/database/schemas/support-ticket-messages.schema.ts`
- `manager-service/src/database/schemas/users.schema.ts`
- `manager-service/src/lib/auth.ts`
