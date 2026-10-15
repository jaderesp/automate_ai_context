"""E2E da instância de teste: envia texto, imagem e documento pela fila (mesmo envelope do
api-service), consulta /chats (get e list) e, opcionalmente, faz revoke do texto.

Uso: python3 e2e.py <numero_destino> [--no-revoke]
"""
import json, os, re, sys, time, uuid
from datetime import datetime, timezone

import pika

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, "..", "..", "..", "worker-go", ".env")
QUEUE = "999999999999999"
EXCHANGE = "API-WhatsApp"
TO = sys.argv[1]
OUT = os.path.join(HERE, "e2e_result_%s.json" % TO)


def env(name):
    for line in open(ENV):
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip("'\"")
    raise SystemExit(f"{name} ausente no .env")


conn = pika.BlockingConnection(pika.URLParameters(env("RABBITMQ_URI")))
ch = conn.channel()
reply_q = ch.queue_declare(queue="", exclusive=True, auto_delete=True).method.queue


def rpc(data, timeout=90):
    """Publica como o api-service (pattern + data) e espera a resposta do worker."""
    corr = uuid.uuid4().hex
    data = {**data, "phone_number_id": QUEUE}
    body = json.dumps({"pattern": data["endpoint"], "data": data})
    ch.basic_publish(
        exchange=EXCHANGE,
        routing_key=QUEUE,
        body=body,
        properties=pika.BasicProperties(
            correlation_id=corr, reply_to=reply_q, delivery_mode=2, headers={"x-delay": 0}
        ),
    )
    deadline = time.time() + timeout
    while time.time() < deadline:
        method, props, resp = ch.basic_get(reply_q, auto_ack=True)
        if method and props.correlation_id == corr:
            return json.loads(resp)
        time.sleep(0.3)
    return {"status": "timeout"}


def shorten(obj):
    """Encurta campos binários longos (thumbnails) para caber na documentação."""
    if isinstance(obj, dict):
        return {k: shorten(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [shorten(v) for v in obj]
    if isinstance(obj, str) and len(obj) > 120 and re.fullmatch(r"[A-Za-z0-9+/=]+", obj):
        return obj[:24] + f"...<base64 {len(obj)} chars>"
    return obj


started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
stamp = datetime.now().strftime("%H:%M:%S")
result = {"started_utc": started, "to": TO, "cases": {}}

SENDS = {
    "text": {
        "endpoint": "messages", "type": "text", "to": TO,
        "text": {"body": f"[E2E {stamp}] texto enviado pela API", "preview_url": False},
    },
    "image": {
        "endpoint": "messages", "type": "image", "to": TO,
        "image": {"link": "https://www.gstatic.com/webp/gallery/1.jpg",
                  "caption": f"[E2E {stamp}] imagem pela API"},
    },
    "document": {
        "endpoint": "messages", "type": "document", "to": TO,
        "document": {"link": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                     "filename": "dem72-teste.pdf",
                     "caption": f"[E2E {stamp}] documento pela API"},
    },
}

for name, payload in SENDS.items():
    sent = rpc(payload)
    case = {"request": payload, "send_response": sent}
    msg_id = (sent.get("data") or {}).get("ID") if sent.get("status") == "success" else None
    case["message_id"] = msg_id
    if msg_id:
        got = rpc({"endpoint": "chats", "action": "get", "chats": {"message_id": msg_id}}, timeout=30)
        case["chats_get"] = shorten(got)
    result["cases"][name] = case
    print(f"{name}: send={sent.get('status')} id={msg_id} get={case.get('chats_get', {}).get('status')}")
    time.sleep(2)

# Filtro de datas do list (compara Info.Timestamp como string RFC3339)
listed = rpc({"endpoint": "chats", "action": "list",
              "chats": {"sendForMe": True, "startDate": started, "page": 1, "pageSize": 20}}, timeout=30)
ids = [m["Info"]["ID"] for m in ((listed.get("data") or {}).get("messages") or [])]
result["chats_list"] = {"status": listed.get("status"), "totalCount": (listed.get("data") or {}).get("totalCount"), "ids": ids}
print(f"list: status={listed.get('status')} ids={ids}")

# Regressão DEM-66: revoke só com message_id (sem 'to'), usando a mensagem de texto
text_id = result["cases"]["text"].get("message_id")
if text_id and "--no-revoke" not in sys.argv:
    rev = rpc({"endpoint": "messages", "type": "revoke", "revoke": {"message_id": text_id}}, timeout=30)
    result["revoke_text"] = rev
    print(f"revoke: status={rev.get('status')}")

json.dump(result, open(OUT, "w"), ensure_ascii=False, indent=2)
conn.close()
print("resultado salvo em", OUT)
