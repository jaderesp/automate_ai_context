#!/usr/bin/env python3
"""Lê e atualiza a planilha do backlog pelo Apps Script publicado.

Regras: ai.context/demandas/regras/FONTE_BACKLOG.md (toda gravação precisa de
autorização do desenvolvedor, a cada vez; ler não precisa).

Configuração (fora do git): ~/.config/uzapi/planilha.json
    {"url": "https://script.google.com/macros/s/.../exec", "token": "..."}

Uso:
    planilha_sync.py pull               # planilha → csv/10092026.csv (mostra o que mudou)
    planilha_sync.py get 80
    planilha_sync.py history            # mudanças desde a última leitura marcada
    planilha_sync.py history --mark     # idem, e marca como lidas
    planilha_sync.py history --since 2026-10-15T00:00:00Z
    planilha_sync.py update 80 --status "Concluído" --versao 0.095-dev06 \
        --obs "texto acrescentado às observações"
"""
import argparse
import csv
import io
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request

CONFIG = os.path.expanduser("~/.config/uzapi/planilha.json")
STATE = os.path.expanduser("~/.config/uzapi/planilha_state.json")
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "csv", "10092026.csv")
WATCHED = ("Status", "Observações", "Testado Em", "Versão", "Título", "Prioridade")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def call(payload):
    with open(CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)
    payload = dict(payload, token=cfg["token"])
    req = urllib.request.Request(
        cfg["url"],
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # O Apps Script responde 302 para script.googleusercontent.com; o resultado
    # tem de ser buscado com um GET limpo (o redirecionamento automático do
    # urllib reaproveita cabeçalhos e o Google responde 404).
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        if err.code not in (301, 302, 303, 307, 308):
            raise
        location = err.headers["Location"]
    with urllib.request.urlopen(location, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_retry(payload, tentativas=3):
    """Só para leituras: o endereço de resultado do Google às vezes responde 404
    ou vazio. Nunca usar em update (repetir acrescentaria a observação duas vezes)."""
    for n in range(tentativas):
        try:
            return call(payload)
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as err:
            if n == tentativas - 1:
                raise RuntimeError(f"falha na chamada: {err}") from err
            time.sleep(3)


def _read_csv(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {(r.get("ID") or "").strip(): r for r in csv.DictReader(f) if (r.get("ID") or "").strip()}


def pull(csv_path=CSV_PATH):
    """Baixa a aba principal da planilha e regrava o CSV local (escrita atômica).
    Devolve o que mudou em relação ao CSV anterior."""
    result = call_retry({"action": "export"})
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "export falhou"))
    header, rows = result["header"], result["rows"]

    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    novo = buf.getvalue()

    antigo = ""
    if os.path.exists(csv_path):
        with open(csv_path, encoding="utf-8-sig", newline="") as f:
            antigo = f.read()
    antes = _read_csv(csv_path)

    novas, mudancas = [], []
    for r in rows:
        d = dict(zip(header, r))
        tid = (d.get("ID") or "").strip()
        if not tid:
            continue
        # As linhas da planilha já vêm numeradas: task nova = ID novo ou título
        # preenchido numa linha que estava vazia.
        if tid not in antes or (not (antes[tid].get("Título") or "").strip() and (d.get("Título") or "").strip()):
            if not (d.get("Título") or "").strip():
                continue
            novas.append({"id": tid, "titulo": d.get("Título", ""), "prioridade": d.get("Prioridade", ""),
                          "responsavel": d.get("Responsável", "")})
            continue
        for col in WATCHED:
            a = (antes[tid].get(col) or "").strip().replace("\r\n", "\n")
            b = (d.get(col) or "").strip().replace("\r\n", "\n")
            if a != b:
                mudancas.append({"id": tid, "coluna": col, "antes": a, "depois": b})

    changed = novo.replace("\r\n", "\n") != antigo.replace("\r\n", "\n")
    if changed:
        pasta = os.path.dirname(os.path.abspath(csv_path))
        fd, tmp = tempfile.mkstemp(dir=pasta, prefix=".planilha-", suffix=".csv")
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(novo)
        os.chmod(tmp, 0o644)
        os.replace(tmp, csv_path)
    return {"changed": changed, "aba": result.get("aba"), "total": len(rows),
            "novas": novas, "mudancas": mudancas}


def history(a):
    since = a.since
    if not since and os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            since = json.load(f).get("since")
    payload = {"action": "history"}
    if since:
        payload["since"] = since
    result = call_retry(payload)
    if not result.get("ok"):
        sys.exit(json.dumps(result, ensure_ascii=False))
    items = result.get("history", [])
    print(json.dumps({"since": since, "total": len(items), "history": items},
                     ensure_ascii=False, indent=2))
    if a.mark and items:
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump({"since": items[-1]["data"]}, f)
        os.chmod(STATE, 0o600)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="action", required=True)
    sub.add_parser("pull")
    g = sub.add_parser("get")
    g.add_argument("id")
    u = sub.add_parser("update")
    u.add_argument("id")
    u.add_argument("--status")
    u.add_argument("--versao")
    u.add_argument("--obs")
    h = sub.add_parser("history")
    h.add_argument("--since")
    h.add_argument("--mark", action="store_true")
    a = p.parse_args()

    try:
        if a.action == "pull":
            print(json.dumps(pull(), ensure_ascii=False, indent=2))
            return
        if a.action == "history":
            history(a)
            return
        if a.action == "get":
            result = call_retry({"action": "get", "id": a.id})
        else:
            payload = {"action": "update", "id": a.id}
            if a.status is not None:
                payload["status"] = a.status
            if a.versao is not None:
                payload["versao"] = a.versao
            if a.obs:
                payload["observacao"] = a.obs
            if len(payload) == 2:
                sys.exit("nada para atualizar")
            # Sem repetição: em caso de falha, conferir com `get` antes de tentar de novo.
            result = call(payload)
    except RuntimeError as err:
        sys.exit(str(err))

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
