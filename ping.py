#!/usr/bin/env python3
import csv, os, sys, random, json, datetime, requests

CONFIG  = os.getenv("CONFIG_FILE", "endpoints.csv")
TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))

def pick_variant(raw: str) -> str:
    """Повертає випадковий варіант (розділювач '|')."""
    if not raw:
        return ""
    return random.choice([v.strip() for v in raw.split('|') if v.strip()])

def parse_pairs(raw: str, sep=";", kv_sep=":"):
    """'K: v; X: y' або 'k=v; z=w' → dict."""
    pairs = [p.strip() for p in raw.split(sep) if p.strip()]
    out = {}
    for p in pairs:
        if kv_sep in p:
            k, v = p.split(kv_sep, 1)
        elif "=" in p:          # для cookies fallback
            k, v = p.split("=", 1)
        else:
            continue
        out[k.strip()] = v.strip()
    return out

def json_from(raw: str):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parse error: {e}  ← {raw}", file=sys.stderr)
        return None

def call(row: dict):
    method = row["method"].strip().upper()
    url    = row["url"].strip()

    headers = parse_pairs(pick_variant(row.get("headers", "")))
    cookies = parse_pairs(pick_variant(row.get("cookies", "")), kv_sep="=")
    body    = json_from(pick_variant(row.get("body", "")))

    try:
        r = requests.request(
            method, url,
            headers=headers, cookies=cookies,
            json=body if method in ("POST", "PUT", "PATCH") else None,
            timeout=TIMEOUT
        )
        stamp = datetime.datetime.utcnow().isoformat(timespec="seconds")
        print(f"{stamp}  {method} {url} → {r.status_code}")
        r.raise_for_status()
    except Exception as e:
        print(f"❌ {method} {url}: {e}", file=sys.stderr)

def main():
    if not os.path.isfile(CONFIG):
        sys.exit(f"Config '{CONFIG}' not found")
    with open(CONFIG, newline='', encoding="utf-8") as f:
        for row in csv.DictReader(f):
            call(row)

if __name__ == "__main__":
    main()
