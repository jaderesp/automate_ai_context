#!/usr/bin/env bash
# Sobe, para e confere o painel de demandas e o módulo WhatsApp juntos.
# Uso: ./servicos.sh start|stop|restart|status|logs [--fonte planilha|csv]
# Logs e PIDs ficam em ~/.config/uzapi/servicos/ (fora do ai.context).
set -u

BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN="$HOME/.config/uzapi/servicos"
WA_DIR="$BASE/whatsapp"
WA_BIN="$WA_DIR/whatsapp-notify"
WA_PORT=9011
PAINEL="$BASE/demandas/painel_local.py"
PAINEL_PORT=9000
FONTE="planilha"

mkdir -p "$RUN"
chmod 700 "$RUN"

porta_ocupada() { ss -ltn "sport = :$1" 2>/dev/null | grep -q LISTEN; }

pid_vivo() {
    local f="$RUN/$1.pid"
    [[ -f "$f" ]] && kill -0 "$(cat "$f")" 2>/dev/null
}

compilar_whatsapp() {
    if [[ ! -x "$WA_BIN" || "$WA_DIR/main.go" -nt "$WA_BIN" ]]; then
        echo "whatsapp: compilando..."
        (cd "$WA_DIR" && CGO_ENABLED=1 GOPROXY=off go build -o whatsapp-notify .) || {
            echo "whatsapp: falha na compilação"; return 1; }
    fi
}

iniciar() { # nome porta comando...
    local nome=$1 porta=$2; shift 2
    if pid_vivo "$nome"; then
        echo "$nome: já está no ar (PID $(cat "$RUN/$nome.pid"))"; return 0
    fi
    if porta_ocupada "$porta"; then
        echo "$nome: porta $porta já ocupada por outro processo; não iniciado"; return 1
    fi
    nohup "$@" >>"$RUN/$nome.log" 2>&1 &
    echo $! >"$RUN/$nome.pid"
    for _ in $(seq 1 20); do
        porta_ocupada "$porta" && { echo "$nome: no ar (PID $!, porta $porta)"; return 0; }
        kill -0 $! 2>/dev/null || break
        sleep 0.5
    done
    echo "$nome: não subiu; últimas linhas do log:"
    tail -n 10 "$RUN/$nome.log"
    rm -f "$RUN/$nome.pid"
    return 1
}

parar() { # nome
    local nome=$1 f="$RUN/$1.pid"
    if ! pid_vivo "$nome"; then
        echo "$nome: não estava rodando (pelo script)"; rm -f "$f"; return 0
    fi
    local pid; pid=$(cat "$f")
    kill "$pid"
    for _ in $(seq 1 20); do
        kill -0 "$pid" 2>/dev/null || { echo "$nome: parado"; rm -f "$f"; return 0; }
        sleep 0.5
    done
    echo "$nome: não encerrou em 10 s (PID $pid); verifique manualmente"
    return 1
}

situacao() { # nome porta
    local nome=$1 porta=$2
    if pid_vivo "$nome"; then
        echo "$nome: no ar (PID $(cat "$RUN/$nome.pid"), porta $porta)"
    elif porta_ocupada "$porta"; then
        echo "$nome: porta $porta ocupada por processo iniciado fora do script"
    else
        echo "$nome: parado"
    fi
}

start() {
    compilar_whatsapp && (cd "$WA_DIR" && iniciar whatsapp "$WA_PORT" "$WA_BIN")
    iniciar painel "$PAINEL_PORT" python3 "$PAINEL" --fonte "$FONTE"
    echo "Painel: http://localhost:$PAINEL_PORT"
}

stop() {
    parar painel
    parar whatsapp
}

acao="${1:-}"; shift || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --fonte) FONTE="${2:-planilha}"; shift 2 ;;
        *) echo "opção desconhecida: $1"; exit 2 ;;
    esac
done
[[ "$FONTE" == "planilha" || "$FONTE" == "csv" ]] || { echo "--fonte deve ser planilha ou csv"; exit 2; }

case "$acao" in
    start)   start ;;
    stop)    stop ;;
    restart) stop; start ;;
    status)  situacao whatsapp "$WA_PORT"; situacao painel "$PAINEL_PORT" ;;
    logs)    touch "$RUN/whatsapp.log" "$RUN/painel.log"; tail -n 30 -f "$RUN/whatsapp.log" "$RUN/painel.log" ;;
    *) echo "Uso: $0 start|stop|restart|status|logs [--fonte planilha|csv]"; exit 2 ;;
esac
