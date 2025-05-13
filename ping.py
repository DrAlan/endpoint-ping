#!/usr/bin/env python3
"""
Читає endpoints.csv і по черзі виконує HTTP-запити.
  • method  — GET або POST
  • url     — повна адреса
  • headers — "Key: val; Another-Key: val2"
  • cookies — "name1=val1; name2=val2"
"""

import csv, os, sys, datetime, requests

CONFIG = os.getenv("CONFIG_FILE", "endpoints.csv")   # можна перевизначити у workflow
TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))       # секунд

def parse_pairs(raw: str, sep=";", kv_sep=":"):
    """Перетворює 'K: v; X: y' або 'k=v; z=w' → dict"""
    if not raw:
        return {}
    pairs = [p.strip() for p in raw.split(sep) if p.strip()]
    out = {}
    for p in pairs:
        if kv_sep in p:
            k, v = p.split(kv_sep, 1)
        elif "=" in p:                   # fallback для cookies у форматі name=val
            k, v = p.split("=", 1)
        else:
            continue
        out[k.strip()] = v.strip()
    return out

def call(row: dict):
    mth = row["method"].strip().upper()
    url = row["url"].strip()
    hdr = parse_pairs(row.get("headers", ""), sep=";", kv_sep=":")
    cks = parse_pairs(row.get("cookies", ""), sep=";", kv_sep="=")

    try:
        if mth == "GET":
            r = requests.get(url, headers=hdr, cookies=cks, timeout=TIMEOUT)
        elif mth == "POST":
            r = requests.post(url, headers=hdr, cookies=cks, timeout=TIMEOUT)
        else:
            print(f"⚠️ Unsupported method {mth} → {url}", file=sys.stderr)
            return
        stamp = datetime.datetime.utcnow().isoformat(timespec="seconds")
        print(f"{stamp}  {mth} {url}  → {r.status_code}")
        r.raise_for_status()
    except Exception as e:
        print(f"❌ {mth} {url}: {e}", file=sys.stderr)

def main():
    if not os.path.isfile(CONFIG):
        sys.exit(f"Config '{CONFIG}' not found")
    with open(CONFIG, newline='', encoding="utf-8") as f:
        for row in csv.DictReader(f):
            call(row)

if __name__ == "__main__":
    main()
