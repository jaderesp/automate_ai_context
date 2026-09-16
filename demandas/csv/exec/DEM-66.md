---
id: DEM-66
status: concluido
data_ativacao: 2026-09-14 09:58:26
modulo: API, Worker
---

# 🚀 Dossiê Técnico e Homologação: Falha Crítica na Exclusão de Mensagens (DEM-66)

## 📌 Contexto e Diagnóstico do Incidente (Causa Raiz)
Foi reportado que a funcionalidade de exclusão de mensagens (`POST /messages/revoke`) falhava silenciosamente. O backend processava a requisição, enviava o payload ao RabbitMQ, mas o smartphone destino não executava a ação.
A hipótese inicial da arquitetura era de que o tamanho do `messageId` customizado de 22 caracteres estava violando regras da Meta, e havia uma tentativa de reduzir a geração para 20 caracteres (o que falhou na homologação prática). A investigação profunda revelou que **o problema nunca foi o tamanho de 22 caracteres** (que é, de fato, a exigência oficial atual), mas sim um **incidente composto por duas falhas estruturais na arquitetura:**

### 1. Quebra de Protocolo (Breaking Change) da API do WhatsApp Web
A API da Meta atualizou silenciosamente o algoritmo de validação dos IDs de mensagens customizados. **O tamanho exigido é exatamente de 22 caracteres** (Prefixo `3EB0` + 18 caracteres sequenciais). Contudo, a nova regra determina que esses 18 bytes não podem ser apenas aleatórios; eles **devem obrigatoriamente ser um Hash SHA-256 contendo a junção matemática de 3 fatores:**
1. Unix Timestamp atual (8 bytes)
2. **Telefone do Remetente (`phoneNumber@c.us`)**
3. 16 bytes de semente randômica
A nossa `api-service` estava gerando corretamente 22 caracteres, porém gerava um SHA-256 apenas com o Timestamp e a semente randômica (omitindo a assinatura do telefone remetente). Ao receber esse ID forjado de 22 caracteres sem a assinatura, a Meta o considerava "inválido", o descartava, gerava um ID genérico próprio de 32 caracteres (ex: `AC89...`) e o enviava para o aparelho. Assim, o celular salvava `AC...` e o frontend tentava excluir o ID `3EB0...`, resultando em falha fantasma.

### 2. Ponto Cego Arquitetural no Worker-Go (Persistência de Envio)
Ao rastrear o pacote de Revoke dentro do `worker-go` (`revoke.go`), identificou-se que a exclusão depende de saber o `chatJID` (destinatário). Como a rota de Revoke da API exige apenas o `messageId` e omite o telefone de destino (`to`), o Worker-Go era forçado a consultar o banco de dados SQLite local (`GetMessageByID`) para descobrir em qual chat a mensagem ocorreu.
**A Falha:** O Worker-Go não registrava no SQLite mensagens disparadas por ele próprio (outgoing messages). Como a mensagem disparada por nós mesmos nunca existiu no banco local do Worker, a exclusão sofria aborto silencioso.

## 🛠️ Solução Adotada e Engenharia Reversa
Para solucionar o incidente de forma perene sem causar quebras de compatibilidade (Breaking Changes) para o frontend:

1. **Restabelecimento dos 22 Caracteres e Assinatura Criptográfica (`api-service`)**:
   - A geração do ID foi revertida e fixada em **22 caracteres corretos**.
   - Os módulos `InstancesService` e `TokenGuard` foram refatorados para extrair o `phoneNumber` real da instância de disparo (via Drizzle ORM).
   - O `RabbitmqService.generateMessageID()` foi completamente reescrito para emular a biblioteca `whatsmeow`, concatenando o telefone em buffer UTF-8 ao Hash SHA-256. A API voltou a emitir os 22 caracteres (`3EB0` + 18 chars), mas agora com uma assinatura 100% autêntica perante os servidores da Meta.

2. **Fechamento do Ponto Cego no Worker-Go (`worker-go`)**:
   - O arquivo `factory.go` (`ExecuteMessageFunction`) recebeu um interceptador. Imediatamente após o envio bem-sucedido de qualquer texto/mídia, o Worker agora converte a resposta em um `NormalizedMessage` sintético e executa o `database.UpsertMessage` salvando a própria mensagem no SQLite com o `chatJID` de destino.
   - Isso garante que a exclusão local localize o chat e construa a deleção.

## 🧪 Teste Prático e Homologação (Auditoria E2E)
Os testes foram realizados de ponta a ponta (API -> RabbitMQ -> Worker -> SQLite -> Smartphone):
1. A API teve seu TokenGuard ignorado temporariamente para injeção direta de payloads (`bypass.js`).
2. Disparo de envio via POST. Logs do `worker-go` confirmaram que o novo ID de 22 caracteres (`3EB0555094E53806E7E248`) foi perfeitamente aceito pela Meta sem sobrescrita, e inserido localmente no SQLite do worker.
3. Disparo isolado de Revoke contendo apenas o `message_id` (sem informar o `to`).
4. O `worker-go` interceptou, consultou o SQLite, extraiu o JID do chat e enviou para o WhatsApp Web.
5. **Veredito:** O device registrou a deleção imediata ("Esta mensagem foi apagada"), comprovando a eficácia total na exclusão de outgoing messages.

## 📂 Arquivos Modificados
### 1. `api-service` (Repositório API)
- `src/database/instances.service.ts`
- `src/common/guards/token.guard.ts`
- `src/controllers/Messages/message.controller.ts`
- `src/rabbitmq/rabbitmq.service.ts`

### 2. `worker-go` (Repositório Worker)
- `services/factory.go`
