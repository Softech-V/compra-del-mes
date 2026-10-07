# -*- coding: utf-8 -*-
"""Obtiene los SKU de cada producto del plan (vía slug exacto de su URL) y arma
los links de carrito VTEX: /checkout/cart/add?sku=..&qty=..&seller=..&sc=1"""
import json, os, re, sys, io, time
import requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36"}
HOSTS = {"carrefour": "www.carrefour.com.ar", "dia": "diaonline.supermercadosdia.com.ar"}

plan = json.load(open(os.path.join(BASE, "plan_carritos.json"), encoding="utf-8"))

# sustituciones de los 4 matches malos: buscar el producto REAL por término
FIXES = {
    ("carrefour", "manteca"): ("manteca 200", ["manteca"], ["galletita", "cookie"]),
    ("dia", "patitas"): ("patitas de pollo", ["patitas"], ["pata de pollo x", "muslo"]),
    ("dia", "gaseosa-coca-lata"): ("coca cola lata", ["coca"], ["pepsi", "zero"]),
    ("dia", "cerveza-patagonia"): ("cerveza patagonia", ["patagonia"], []),
    ("dia", "queso-cremoso"): ("queso cremoso", ["cremoso"], ["light", "untable"]),
}

def api(host, path):
    try:
        r = requests.get(f"https://{host}{path}", headers=H, timeout=15)
        if r.status_code in (200, 206):
            return r.json()
    except Exception:
        pass
    return None

def sku_de_slug(host, url):
    m = re.search(r"https?://[^/]+/(.+)/p\b", url or "")
    if not m:
        return None
    slug = m.group(1)
    data = api(host, f"/api/catalog_system/pub/products/search/{slug}/p")
    if not data:
        return None
    try:
        it = data[0]["items"][0]
        seller = it["sellers"][0]
        return {"sku": it["itemId"], "seller": seller["sellerId"],
                "nombre": data[0]["productName"], "precio": round(seller["commertialOffer"]["Price"]),
                "disponible": seller["commertialOffer"].get("IsAvailable", True)}
    except Exception:
        return None

def buscar(host, term, must, block):
    data = api(host, f"/api/catalog_system/pub/products/search/?ft={requests.utils.quote(term)}&_from=0&_to=8") or []
    out = []
    for p in data:
        try:
            name = p["productName"]
            low = name.lower()
            if must and not any(w in low for w in must):
                continue
            if block and any(w in low for w in block):
                continue
            it = p["items"][0]
            seller = it["sellers"][0]
            offer = seller["commertialOffer"]
            if not offer.get("IsAvailable", True) or not offer.get("Price"):
                continue
            out.append({"sku": it["itemId"], "seller": seller["sellerId"],
                        "nombre": name, "precio": round(offer["Price"])})
        except Exception:
            continue
    return out

resultado = {}
for store in ["carrefour", "dia"]:
    host = HOSTS[store]
    filas = []
    for item in plan[store]:
        iid, qty = item["id"], item["qty"]
        key = (store, iid)
        if key in FIXES:
            term, must, block = FIXES[key]
            cands = buscar(host, term, must, block)
            print(f"[FIX {store}/{iid}] término '{term}':")
            for c in cands[:4]:
                print(f"    ${c['precio']:>7,} sku={c['sku']} {c['nombre'][:60]}")
            fila = dict(cands[0], id=iid, qty=qty) if cands else None
            if not fila:
                print(f"    -> SIN CANDIDATO, se omite")
                continue
        else:
            info = sku_de_slug(host, item["url"])
            if not info:
                print(f"[{store}/{iid}] sin SKU desde slug ({item['url'][:60]}), pruebo búsqueda…")
                cands = buscar(host, item["producto"][:40], [], [])
                info = cands[0] if cands else None
            if not info or not info.get("disponible", True):
                print(f"[{store}/{iid}] NO DISPONIBLE u omitido")
                continue
            fila = dict(info, id=iid, qty=qty)
        filas.append(fila)
        time.sleep(0.3)
    resultado[store] = filas
    total = sum(f["precio"] * f["qty"] for f in filas)
    print(f"\n== {store}: {len(filas)} items, total estimado ${total:,.0f} ==\n")

json.dump(resultado, open(os.path.join(BASE, "carritos_sku.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

for store, filas in resultado.items():
    host = HOSTS[store]
    partes = "&".join(f"sku={f['sku']}&qty={f['qty']}&seller={f['seller']}" for f in filas)
    link = f"https://{host}/checkout/cart/add?{partes}&sc=1"
    print(f"\nLINK {store} ({len(link)} caracteres):\n{link}\n")
