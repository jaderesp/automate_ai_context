---
id: DEM-66
status: concluido
data_ativacao: 2026-09-14 09:58:26
modulo: API
---

# 🚀 Histórico de Execução: Exclusões de mensagens pararam de funcionar (DEM-66)

## 📌 Resumo do Problema (Causa Raiz)
A função de exclusão de mensagens (`POST /messages/revoke`) do frontend falhava silenciosamente e abortava a requisição.
Após investigação detalhada em reuniões técnicas e exploração do banco de dados SQLite, descobriu-se que o problema era originário do gerador de ID da `api-service`. O gerador estava criando um ID de mensagem com prefixo `3EB0` contendo um total de **22 caracteres**.
No entanto, a biblioteca `whatsmeow` e o protocolo de servidores da Meta exigem estritamente que os IDs iniciados em `3EB0` tenham **exatamente 20 caracteres**. Ao receber o ID de 22 caracteres, o WhatsApp o ignorava por ser inválido e gerava um novo ID de 32 caracteres (ex: `AC3C...`) internamente. Como o webhook de resposta salvava o ID do WhatsApp, e o frontend tentava deletar pelo ID antigo fornecido pela API (de 22 caracteres), as mensagens nunca eram encontradas no banco de dados, falhando as interações.

## 🛠️ Solução Adotada (Opção C - Ajuste de Protocolo)
A solução implementada foi a mais otimizada e cirúrgica possível:
1. No arquivo `api-service/src/rabbitmq/rabbitmq.service.ts`, o corte da string que compõe o ID foi reduzido de `slice(0, 18)` para `slice(0, 16)`.
2. Isso garante que, concatenado ao prefixo `3EB0`, o resultado final do `messageId` entregue à fila RabbitMQ e retornado na resposta da API tenha o tamanho exato de **20 caracteres**.
3. O WhatsApp passou a aceitar os IDs organicamente.
Com isso, banco de dados, webhooks e os endpoints de Deleção, Reação e Resposta, agora operam utilizando o ID padronizado perfeitamente, sem a necessidade de lógicas de "de-para" ou tradutores de ID, zerando a complexidade.

## 📂 Arquivos Modificados
- `api-service/src/rabbitmq/rabbitmq.service.ts`
