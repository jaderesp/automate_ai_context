---
id: DEM-1
status: concluido
data_ativacao: 2026-09-10 15:37:09
data_conclusao: 2026-09-10 18:55:00
modulo: Usuários
---

# 🚀 Histórico de Execução: Não exclui usuário

## 📌 Resumo do Problema
O painel administrativo exibia "Sucesso" ao clicar em "Remover Conta", mas o usuário continuava ativo. 

### 1. Falso Positivo no Frontend
O frontend mascarava o erro do backend. A função `authClient.admin.removeUser()` retornava um objeto `{ data, error }`, mas o código em `page.tsx` não verificava a propriedade `error`, assumindo sucesso incondicional e prosseguindo com o alerta visual de sucesso.

### 2. Bloqueio no Banco de Dados (PostgreSQL / Drizzle)
O verdadeiro motivo da exclusão não ocorrer era uma falha de "Foreign Key Constraint" gerada por um conflito de arquitetura no Schema do banco. O PostgreSQL bloqueava a query `DELETE FROM "user"` com um erro `23502 - not-null constraint`.

As tabelas de relacionamento vinculadas ao usuário (`user.id`) que impediam a exclusão eram:
- **Tabela:** `support_ticket_audit`
  - **Coluna:** `actor_id`
  - **Motivo do conflito:** A chave estrangeira estava definida como `onDelete: "set null"` (para preservar o histórico de auditoria quando o autor fosse apagado). No entanto, o Drizzle ORM definia o campo rigidamente como `.notNull()`. O banco impedia a operação ao tentar converter a coluna para nulo.
- **Tabela:** `support_ticket_messages`
  - **Coluna:** `author_id`
  - **Motivo do conflito:** Idêntico à tabela acima. O campo exigia `.notNull()`, barrando a regra `onDelete: "set null"` disparada pela exclusão em cascata do usuário.

## 🛠️ Solução Adotada
1. **Frontend:** Adicionado `if (error) throw new Error(...)` no arquivo `src/app/admin/users/page.tsx` para garantir a captura e exibição de falhas reais do servidor no momento da deleção e outras ações administrativas.
2. **Backend/Banco:** 
   - Removido o método `.notNull()` das colunas `actorId` e `authorId` nas tabelas `support-ticket-audit` e `support-ticket-messages`.
   - Adicionada a coluna `impersonatedBy` na tabela `session` (`users.schema.ts`), corrigindo um crash independente no Better Auth ao compilar a rota de usuários.
   - Adicionado um bloco `.catch(console.error)` no envio de email OTP (`src/lib/auth.ts`) para evitar quedas no ambiente Node caso o provedor SMTP falhe.
3. **Migração:** Realizado push das alterações de schema via `drizzle-kit push`, regularizando a integridade e liberando o fluxo de exclusão em cascata.

## 📂 Arquivos Modificados
- `manager-service/src/app/admin/users/page.tsx`
- `manager-service/src/database/schemas/support-ticket-audit.schema.ts`
- `manager-service/src/database/schemas/support-ticket-messages.schema.ts`
- `manager-service/src/database/schemas/users.schema.ts`
- `manager-service/src/lib/auth.ts`

---

## 🔎 Atualização 06/10/2026: situação real da entrega

> ⚠️ A correção descrita acima **nunca chegou à `main`**. O commit `cb6a568` (`fix(DEM-1): allow user deletion by relaxing schema constraints and adding impersonatedBy to sessions`, 14/09) existe apenas na branch local `fix/demanda-1-delete-user` do `manager-service`, sem push, sem merge e sem tag.

- Parte do conteúdo entrou na `main` por outra demanda: a coluna `impersonatedBy` em `src/database/schemas/users.schema.ts` (DEM-65). O restante do commit (10 arquivos) não foi conferido contra a `main` atual (`v0.3.57`).
- **Encaminhamento:** verificar se a branch ainda aplica sem conflito sobre a `main`, enviar e abrir o MR, ou refazer a correção. O frontmatter foi mantido como `concluido`; revisar o status.

---

## 🔎 Conferência na reclassificação (15/10/2026)
Mantida `concluido` por decisão do desenvolvedor (QA `Aprovado`). Registro técnico: na `origin/main` do `manager-service` as colunas `support_ticket_audit.actor_id` e `support_ticket_messages.author_id` continuam `.notNull()` com `onDelete: "set null"`, e `src/app/admin/users/page.tsx:296` não confere o `error` de `authClient.admin.removeUser`. A exclusão de usuário que tenha ticket de suporte/auditoria deve continuar falhando com mensagem de sucesso; usuários sem ticket são excluídos normalmente (provável cenário da aprovação). Se voltar a ser relatado, a correção é a descrita acima (commit local `cb6a568`, nunca publicado), refeita a partir da `dev`, com migração autorizada pelo Eduardo.
