# -*- coding: utf-8 -*-
"""Precio de leche descremada larga vida 1L en las 4 cadenas (APIs públicas)."""
import json, os, sys, io
import requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36"}

def vtex(host, term):
    try:
        r = requests.get(f"https://{host}/api/catalog_system/pub/products/search/?ft={term}&_from=0&_to=4", headers=H, timeout=15)
        best = None
        for p in r.json():
            try:
                it = p["items"][0]
                offer = it["sellers"][0]["commertialOffer"]
                if not offer.get("IsAvailable", True) or not offer.get("Price"):
                    continue
                row = {"producto": p.get("productName", ""), "precio": round(offer["Price"]), "url": "https://" + host + "/" + p.get("linkText", "") + "/p"}
                if best is None or row["precio"] < best["precio"]:
                    best = row
            except Exception:
                continue
        return best
    except Exception as e:
        print(host, "error:", e)
        return None

term = "leche%20descremada%20larga%20vida%201"
res = {
    "carrefour": vtex("www.carrefour.com.ar", term),
    "dia": vtex("diaonline.supermercadosdia.com.ar", term),
    "jumbo": vtex("www.jumbo.com.ar", term),
}
for k, v in res.items():
    print(k, "->", v)

files = {"carrefour": "precios_carrefour.json", "dia": "precios_dia.json", "jumbo": "precios_jumbo.json"}
for k, fname in files.items():
    if not res.get(k):
        continue
    path = os.path.join(BASE, fname)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["items"] = [i for i in data["items"] if i["id"] != "leche-descremada"] + [{
        "id": "leche-descremada", "producto": res[k]["producto"], "presentacion": "1 litro",
        "precio": res[k]["precio"], "promo": None, "url": res[k]["url"],
    }]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("guardado en", fname)
