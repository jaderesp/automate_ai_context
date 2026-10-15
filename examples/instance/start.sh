#!/bin/bash
# Sobe a instância de teste local do worker-go (PHONE_NUMBER_ID 999999999999999).
# Compila o worker da branch que estiver em checkout em ../../../worker-go e reutiliza
# a sessão pareada em db/. Se a sessão tiver caído, grava o QR novo em ./qr.png.
#
# Uso: ./start.sh            (compila e sobe)
#      ./start.sh --no-build (reutiliza bin/worker já compilado)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
WORKER_REPO="$(cd "$HERE/../../../worker-go" && pwd)"
ENV_FILE="$WORKER_REPO/.env"
INSTANCE=999999999999999
PORT=3011
LOG="$HERE/worker.log"

if [ -f "$HERE/worker.pid" ] && kill -0 "$(cat "$HERE/worker.pid")" 2>/dev/null; then
  echo "Instância de teste já está rodando (pid $(cat "$HERE/worker.pid")). Use ./stop.sh para parar."
  exit 0
fi

mkdir -p "$HERE/db" "$HERE/medias" "$HERE/bin"

if [ "${1:-}" != "--no-build" ] || [ ! -x "$HERE/bin/worker" ]; then
  echo "Compilando worker-go ($(git -C "$WORKER_REPO" branch --show-current) @ $(git -C "$WORKER_REPO" rev-parse --short HEAD))..."
  (cd "$WORKER_REPO" && CGO_ENABLED=1 go build -o "$HERE/bin/worker" ./cmd/main.go) || { echo "Falha na compilação."; exit 1; }
fi

# RabbitMQ e Postgres locais vêm do .env do worker-go; o restante é fixo para o teste
getv() { grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | sed -E "s/^['\"]//; s/['\"]\$//"; }
export NODE_ENV=production PORT="$PORT" PHONE_NUMBER_ID="$INSTANCE"
export RABBITMQ_URI="$(getv RABBITMQ_URI)" POSTGRES_URI="$(getv POSTGRES_URI)"
export AMQP_EXCHANGE=API-WhatsApp DATABASE_PATH="$HERE/db" MEDIAS_PATH="$HERE/medias"
export PUBLIC_API_URL="http://localhost:$PORT" AUTH_METHOD=QRCode
export WEBHOOK_URL="${WEBHOOK_URL:-http://127.0.0.1:8099}"
export WEBHOOK_EVENTS="${WEBHOOK_EVENTS:-{\"authentication\":false,\"connection\":false,\"group_messages\":false,\"message_status\":false,\"group_events\":false,\"history\":false}}"

: > "$LOG"
(cd "$HERE" && exec nohup ./bin/worker >> "$LOG" 2>&1) &
PID=$!
echo "$PID" > "$HERE/worker.pid"
echo "Worker iniciado (pid $PID, porta $PORT, log $LOG)."

qr_shown=""
for _ in $(seq 1 90); do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "Worker encerrou. Últimas linhas do log:"
    grep -a -v -E 'base64|[█▀▄]' "$LOG" | tail -8
    rm -f "$HERE/worker.pid"
    exit 1
  fi
  if grep -a -q "Conexão estabelecida" "$LOG"; then
    echo "CONECTADO: instância pronta para uso."
    rm -f "$HERE/qr.png"
    exit 0
  fi
  # Sessão caída: extrai o QR mais recente do log para ./qr.png
  last="$(grep -a -o 'QR Code em base64: [^ ]*' "$LOG" | tail -1 | sed 's/.*base64: //; s/^.*,//')"
  if [ -n "$last" ] && [ "$last" != "$qr_shown" ]; then
    echo "$last" | base64 -d > "$HERE/qr.png.tmp" 2>/dev/null && mv "$HERE/qr.png.tmp" "$HERE/qr.png"
    [ -z "$qr_shown" ] && echo "Sessão não pareada: leia o QR em $HERE/qr.png (é regravado a cada troca)."
    qr_shown="$last"
  fi
  sleep 1
done
echo "Ainda não conectou após 90s (worker segue rodando). Veja $LOG ou rode ./start.sh de novo após parear."
exit 2
