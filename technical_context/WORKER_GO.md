# Contexto Técnico - Worker Go (`worker-go`)

## Visão Geral
Este é o microserviço que realiza a "magia". Baseado em Golang, interage via WebSocket (XMPP) com a rede oficial da Meta/WhatsApp simulando um dispositivo WhatsApp Web utilizando a biblioteca `whatsmeow`.

## Tecnologias e Stack
- **Linguagem**: Go 1.25.0+.
- **Dependência Core**: Fork customizado do `whatsmeow` (`github.com/edupoli/whatsmeow` configurado via `replace` no `go.mod`).
- **Banco de Dados**:
  - `go-sqlite3` (CGO necessário) para Device Store e histórico atômico da sessão.
  - `jackc/pgx/v5` para espelhar estados e realtime metrics no PostgreSQL compartilhado com Manager/API.
- **Mensageria**: RabbitMQ (`amqp091-go`).

## Detalhes de Implementação Importantes
1. **Regras Severas do Whatsmeow Fork**:
   - Não atualize a biblioteca principal via repositório de origem (`go.mau.fi`). A lógica depende do Fork da conta `@edupoli`. Qualquer update deve ser via script `./update-whatsmeow-replace.sh`.
2. **Isolamento de Estado (1-to-1 Pod/Número)**:
   - Um Pod executa apenas UMA conexão WhatsApp. 
   - A fila do RabbitMQ lida por este Worker tem nome e bind atrelados ao identificador (ex: `PHONE_NUMBER_ID`).
3. **Banco de Dados Duplo**:
   - **Local (.db)**: Localizado na pasta persistente estipulada via `DATABASE_PATH`. Esse arquivo SQLite detém a criptografia das chaves do WhatsApp Web daquele cliente. Perder este arquivo obriga leitura de QRCode/PairCode novamente.
   - **Postgres (Shared)**: O pool de conexões com o Postgres tem um limite baixo proposital (`MaxConns=2`), dado o enorme volume potencial de pods criados no cluster de K8s. O Postgres é notificado (via `NOTIFY` Trigger pós `UPSERT`) de status para fluir sockets web no painel em tempo real.
4. **Resolução Dinâmica (Factory)**:
   - Em `services/factory.go`, eventos oriundos do RabbitMQ são mapeados de acordo com `endpoint` (messages, groups, status) e `action` para funções Go dedicadas.
5. **Ciclagem e Reinício**:
   - Funções em `webhook.EventHandler` propositalmente dão `os.Exit(1)` para desligar quando erros irrecuperáveis do WhatsApp acontecem (como o usuário desligar via aplicativo do smartphone). A estratégia de orquestração do K8s (Deployment Replica=1) reestabelece a "janela limpa".
