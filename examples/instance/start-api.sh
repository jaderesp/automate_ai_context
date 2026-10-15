#!/bin/bash
# Sobe o api-service local (porta 4200) usando SOMENTE recursos locais: Postgres, Redis e
# RabbitMQ desta máquina. Os arquivos .env do api-service apontam para o Postgres remoto do
# cluster; aqui as variáveis são sobrescritas no ambiente do processo, sem editar os .env.
#
# Uso: ./start-api.sh            (compila a branch em checkout no api-service e sobe)
#      ./start-api.sh --no-build (reutiliza api-service/dist já compilado)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
API_REPO="$(cd "$HERE/../../../api-service" && pwd)"
WORKER_ENV="$HERE/../../../worker-go/.env"
INSTANCE=999999999999999
API_PORT=4200
LOG="$HERE/api.log"
PIDFILE="$HERE/api.pid"

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "api-service local já está rodando (pid $(cat "$PIDFILE")). Use ./stop-api.sh para parar."
  exit 0
fi

getv() { grep -E "^$2=" "$1" | head -1 | cut -d= -f2- | sed -E "s/[[:space:]]+#.*\$//; s/^['\"]//; s/['\"]\$//"; }

export NODE_ENV=development PORT="$API_PORT" PUBLIC_API_URL="http://localhost:$API_PORT"
export DATABASE_URL="$(getv "$WORKER_ENV" POSTGRES_URI)"
export RABBITMQ_URI="$(getv "$WORKER_ENV" RABBITMQ_URI)"
export REDIS_HOST=localhost REDIS_PORT=6379
export JWT_SECRET="$(getv "$API_REPO/.env" JWT_SECRET)"
export INSTANCE_AUTH_TIMEOUT_MINUTES=10 MEDIA_BASE_PATH="$HERE/medias"

# Trava: nunca subir apontando para banco ou fila fora desta máquina
for v in DATABASE_URL RABBITMQ_URI; do
  host="$(echo "${!v}" | sed -E 's#^[a-z]+://([^@/]*@)?([^:/?]+).*#\2#')"
  if [ "$host" != "localhost" ] && [ "$host" != "127.0.0.1" ]; then
    echo "ABORTADO: $v aponta para '$host', que não é local."
    exit 1
  fi
done

if [ "${1:-}" != "--no-build" ] || [ ! -f "$API_REPO/dist/main.js" ]; then
  echo "Compilando api-service ($(git -C "$API_REPO" branch --show-current) @ $(git -C "$API_REPO" rev-parse --short HEAD))..."
  (cd "$API_REPO" && ./node_modules/.bin/nest build) || { echo "Falha na compilação."; exit 1; }
fi

: > "$LOG"
(cd "$API_REPO" && exec nohup node dist/main >> "$LOG" 2>&1) &
PID=$!
echo "$PID" > "$PIDFILE"
echo "api-service iniciado (pid $PID, porta $API_PORT, log $LOG)."

for _ in $(seq 1 60); do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "api-service encerrou. Últimas linhas do log:"
    tail -15 "$LOG"
    rm -f "$PIDFILE"
    exit 1
  fi
  if grep -q "listening on" "$LOG"; then
    # Token da instância de teste (mesmo payload validado pelo TokenGuard)
    INSTANCE_ID="$(docker exec postgres-uzapi psql -U edupoli -d uzapi -At -c \
      "select id from instances where phone_number_id='$INSTANCE'" 2>/dev/null)"
    (cd "$API_REPO" && INSTANCE_ID="$INSTANCE_ID" PHONE_ID="$INSTANCE" node -e '
      const { JwtService } = require("@nestjs/jwt");
      process.stdout.write(new JwtService({}).sign(
        { userId: "e2e-test-user", username: "e2etest", instanceId: process.env.INSTANCE_ID, phone_number_id: process.env.PHONE_ID },
        { secret: process.env.JWT_SECRET }));
    ') > "$HERE/api_token.txt" && chmod 600 "$HERE/api_token.txt"
    echo "PRONTO: http://localhost:$API_PORT — token em $HERE/api_token.txt"
    exit 0
  fi
  sleep 1
done
echo "api-service não ficou pronto em 60s (segue rodando). Veja $LOG."
exit 2
