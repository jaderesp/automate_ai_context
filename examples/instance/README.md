# Instância de teste local do `worker-go`

Ambiente pronto para testes E2E em aparelho real, com a sessão do WhatsApp já pareada. Sobe o worker da branch que estiver em checkout em `worker-go/`, sem precisar ler QRCode.

## Uso

```bash
cd ai.context/examples/instance
./start.sh                      # compila o worker-go e sobe; termina com "CONECTADO" quando pronto
python3 e2e.py <numero_destino> # texto + imagem + documento pela fila, /chats get e list, revoke do texto
python3 e2e.py <numero_destino> --no-revoke   # mantém as mensagens no aparelho de destino
./stop.sh                       # para o worker sem deslogar o device
```

- `./start.sh --no-build` reutiliza o binário já compilado em `bin/`.
- O resultado de cada execução do `e2e.py` fica em `e2e_result_<numero>.json`.

## Como funciona

| Item | Valor |
|---|---|
| Instância (`PHONE_NUMBER_ID`, fila RabbitMQ, chave realtime) | `999999999999999` |
| Porta HTTP (`/health`) | `3011` |
| Device pareado | `556392308423` (Android), pareado em 2026-10-02 |
| Sessão (whatsmeow device store + histórico) | `db/999999999999999.db` |
| RabbitMQ e Postgres | locais, lidos de `worker-go/.env` (`RABBITMQ_URI`, `POSTGRES_URI`) |
| Exchange | `API-WhatsApp` (routing key = instância) |
| Webhooks | desligados por padrão; para ligar, exporte `WEBHOOK_URL` e `WEBHOOK_EVENTS` antes do `start.sh` |

O `e2e.py` publica direto na fila, no mesmo envelope do `api-service` (`{"pattern": <endpoint>, "data": {...}}`, com `reply_to`/`correlation_id`). O `api-service` não participa.

## Cuidados

- **`db/` contém as chaves da sessão e o histórico de mensagens do número pareado.** Quem tiver esse arquivo opera o WhatsApp dele. A pasta está no `.gitignore` local (junto com `medias/`, `bin/`, logs, `qr.png` e resultados) — nunca versionar nem copiar para fora da máquina.
- **Uma instância por vez:** não rode dois workers com a mesma sessão.
- **A sessão pode cair:** se o device for removido no telefone (WhatsApp → Dispositivos conectados) ou o telefone ficar cerca de 14 dias sem internet, o worker recebe o logout e apaga o `.db`. Nesse caso o `start.sh` grava o QR novo em `qr.png` (regravado a cada troca); leia com o aparelho e a sessão volta a ficar salva.
- **Recursos locais usados:** fila `999999999999999` no RabbitMQ e uma linha em `public.instance_realtime_state` no Postgres local.
- O log (`worker.log`) imprime o conteúdo das mensagens recebidas; é zerado a cada `start.sh`.

## `api-service` local (testes pelo HTTP)

```bash
./start-api.sh      # compila a branch em checkout no api-service e sobe em http://localhost:4200
./stop-api.sh
```

- **Só recursos locais.** Os `.env` do `api-service` apontam para o Postgres remoto do cluster (`5.161.202.138:30100`); o `start-api.sh` sobrescreve `DATABASE_URL`, `REDIS_HOST` e `RABBITMQ_URI` no ambiente do processo (Postgres `postgres-uzapi`, Redis e RabbitMQ locais) e **aborta** se o banco ou a fila não forem `localhost`. Nunca rode `pnpm dev`/`pnpm start` direto para testes: além do banco remoto, o `instance-monitor.service.ts` executa a cada 5 minutos uma rotina que marca instâncias `pending_auth` como `paused`.
- **Cadastro de teste no Postgres local** (criado em 2026-10-05): usuário `e2e-test-user` (`username: e2etest`, `role: user`), `user_billing` `ACTIVE` até 2027-10-05 e a instância `999999999999999` (`deploymentStatus: connected`).
- **Token:** gerado a cada `start-api.sh` em `api_token.txt` (JWT com `userId`, `username`, `instanceId`, `phone_number_id`, assinado com o `JWT_SECRET` do `api-service/.env`). Fora do git.
- **Kubernetes:** o `kubeconfig.yaml` local aponta para `localhost:8080`, que não é um cluster; endpoints de instância (criar, reiniciar, pausar) não funcionam. `/chats` e `/messages` funcionam.

Exemplo:

```bash
T=$(cat api_token.txt)
curl -s -X POST http://localhost:4200/v1/999999999999999/chats \
  -H "Authorization: Bearer $T" -H 'Content-Type: application/json' \
  -d '{"type":"chats","action":"get","chats":{"message_id":"<ID>"}}'
```
