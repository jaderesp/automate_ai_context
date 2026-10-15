#!/bin/bash
# Para o api-service local iniciado pelo start-api.sh.
HERE="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$HERE/api.pid"

if [ ! -f "$PIDFILE" ] || ! kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "api-service local não está rodando."
  rm -f "$PIDFILE"
  exit 0
fi

PID="$(cat "$PIDFILE")"
kill -TERM "$PID"
for _ in $(seq 1 20); do
  kill -0 "$PID" 2>/dev/null || break
  sleep 0.5
done
if kill -0 "$PID" 2>/dev/null; then
  echo "api-service (pid $PID) não encerrou em 10s."
  exit 1
fi
rm -f "$PIDFILE"
echo "api-service local parado."
