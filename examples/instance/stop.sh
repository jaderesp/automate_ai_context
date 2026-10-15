#!/bin/bash
# Para a instância de teste local sem deslogar o device (a sessão em db/ é preservada).
HERE="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$HERE/worker.pid"

if [ ! -f "$PIDFILE" ] || ! kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "Instância de teste não está rodando."
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
  echo "Worker (pid $PID) não encerrou em 10s."
  exit 1
fi
rm -f "$PIDFILE" "$HERE/qr.png"
echo "Instância de teste parada."
