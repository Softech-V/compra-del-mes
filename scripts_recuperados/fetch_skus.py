# -*- coding: utf-8 -*-
"""Agrega sku y seller a cada fila de precios de las cadenas VTEX (carrito por link)."""
import json, os, re, sys, io, time
import requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36"}
HOSTS = {"carrefour": "www.carrefour.com.ar", "dia": "diaonline.supermercadosdia.com.ar", "jumbo": "www.jumbo.com.ar"}

for store, host in HOSTS.items():
    fname = os.path.join(BASE, f"precios_{store}.json")
    data = json.load(open(fname, encoding="utf-8"))
    ok = fail = skip = 0
    for row in data["items"]:
        if row.get("sku"):
            ok += 1
            continue
        url = row.get("url") or ""
        m = re.search(r"https?://[^/]+/(.+?)/p\b", url)
        if not m or host not in url:
            skip += 1
            continue
        try:
            r = requests.get(f"https://{host}/api/catalog_system/pub/products/search/{m.group(1)}/p", headers=H, timeout=15)
            prods = r.json() if r.status_code in (200, 206) else []
            it = prods[0]["items"][0]
            seller = it["sellers"][0]
            row["sku"] = it["itemId"]
            row["seller"] = seller["sellerId"]
            ok += 1
        except Exception:
            fail += 1
        time.sleep(0.25)
    json.dump(data, open(fname, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{store}: {ok} con sku, {fail} sin resolver, {skip} sin url propia")
print("listo")
