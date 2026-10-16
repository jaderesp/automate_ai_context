# whatsapp-notify

Conexão WhatsApp mínima para o painel de demandas (`whatsmeow`, mesmas versões do `worker-go`).

- **QR code:** lido no painel (botão **WhatsApp**). A sessão fica em `~/.config/uzapi/whatsapp/session.db` (permissão 600, fora do git).
- **Envio:** só texto, só para o grupo configurado no painel, só pelo botão **Notificar QA** (o clique em Enviar é a autorização do desenvolvedor).
- **Feedbacks:** escuta só o grupo configurado e grava em `~/.config/uzapi/whatsapp/feedback.jsonl` apenas as mensagens que citam task ("DEM-80", "#80", "task 80"). As demais mensagens são ignoradas.
- **Rede:** atende só em `127.0.0.1:9011`. Sem número conectado, todas as ações de WhatsApp respondem 409.

## Uso
```
cd ai.context/whatsapp
CGO_ENABLED=1 GOPROXY=off go build -o whatsapp-notify .   # compila com o cache local do worker-go
./whatsapp-notify
```
Rotas: `/status`, `/pair`, `/qr.png`, `/logout`, `/groups`, `/group`, `/participants` (membros do grupo configurado, para menção), `/send` (`{"text", "mentions": [jid...]}`; menções só de membros do grupo), `/feedback`.

Ou, junto com o painel: `ai.context/servicos.sh start` (ver `stop`, `restart`, `status`, `logs`; logs em `~/.config/uzapi/servicos/`).
Depois, no painel (`painel_local.py`), botão **WhatsApp** → Conectar → ler o QR → escolher o grupo.

## Cuidados
- Número em uso: `556392308423`, liberado pelo desenvolvedor em 15/10/2026 (opção B). O módulo é um aparelho conectado próprio (`:25`), separado da sessão do worker-go de testes (`:24`, `examples/instance/db/`); "Desconectar" no painel remove só o `:25`. Nunca deslinkar o `:24`. Cliente não oficial: risco de bloqueio do número.
- Avisar o grupo que o número da automação registra mensagens que citam tasks (LGPD).

## Rotas locais
`GET /status`, `POST /pair`, `GET /qr.png`, `POST /logout`, `GET /groups`, `POST /group {jid,name}`, `POST /send {text}`, `GET /feedback?since=RFC3339`.
