#!/usr/bin/env python3
"""
Ping-скрипт для GitHub Actions.

• Читає endpoints.csv (шлях через $CONFIG_FILE або за замовч. у корені).
• Для кожного рядка вибирає випадкові headers / cookies / JSON-body (роздільник "|").
• Підтримує GET, HEAD, DELETE, POST, PUT, PATCH.
• Логує:
    – повний вміст CSV (для дебагу);
    – '>>> Processing METHOD URL' перед кожним викликом;
    – 'timestamp  METHOD URL → status' після відповіді.
"""

import csv, os, sys, random, json, datetime, requests, textwrap

CONFIG  = os.getenv("CONFIG_FILE", "endpoints.csv")
TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))
REQUIRED_COLS = {"method", "url"}

# ────────────────────────────────────────────────────────────── helpers ──
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
        elif "=" in p:
            k, v = p.split("=", 1)            # fallback для cookies
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

# ────────────────────────────────────────────────────────────── main ────
def call(row: dict, row_num: int):
    # пропускаємо неповні записи
    if any(not row.get(col) for col in REQUIRED_COLS):
        print(f"⏭️  Row {row_num}: пропущено — бракує method/url")
        return

    method = (row.get("method") or "GET").strip().upper()
    url    = row["url"].strip()

    headers = parse_pairs(pick_variant(row.get("headers", "")))
    cookies = parse_pairs(pick_variant(row.get("cookies", "")), kv_sep="=")
    body    = json_from(pick_variant(row.get("body", "")))

    print(f">>> Processing {method} {url}")

    try:
        r = requests.request(
            method, url,
            headers=headers, cookies=cookies,
            json=body if method in ("POST", "PUT", "PATCH") else None,
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        stamp = datetime.datetime.utcnow().isoformat(timespec="seconds")
        print(f"{stamp}  {method} {url} → {r.status_code}")
        # вважаємо критичним лише 5xx
        if r.status_code >= 500:
            r.raise_for_status()
    except Exception as e:
        print(f"❌ {method} {url}: {e}", file=sys.stderr)

def main() -> None:
    if not os.path.isfile(CONFIG):
        sys.exit(f"Config '{CONFIG}' not found")

    # друкуємо повний файл для дебагу
    print("────────── ⬇️  endpoints.csv (start) ⬇️ ──────────")
    with open(CONFIG, encoding="utf-8") as f:
        print(textwrap.indent(f.read().rstrip(), "│ "))
    print("────────── ⬆️  endpoints.csv (end)   ⬆️ ──────────")

    # читаємо й обробляємо
    with open(CONFIG, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        for row_num, row in enumerate(reader, start=2):   # 1 — header
            call(row, row_num)

if __name__ == "__main__":
    main()
