# -*- coding: utf-8 -*-
"""Agrega Avocado toast + galletitas clásicas; precios solo Carrefour."""
import json, os, re, sys, io, time, base64
import requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36"}
HOST = "www.carrefour.com.ar"

# 1) plato nuevo
P = json.load(open(os.path.join(BASE, "platos.json"), encoding="utf-8"))
if not any(p["id"] == "avocado-toast" for p in P["platos"]):
    P["platos"].append({
        "id": "avocado-toast", "nombre": "Avocado toast con huevo y panceta", "emoji": "🥑",
        "ing": [["pan-lactal", 240], ["palta", 400], ["huevos", 4], ["panceta", 150]],
    })
    json.dump(P, open(os.path.join(BASE, "platos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("plato avocado-toast agregado")

# 2) galletitas clásicas al catálogo
NUEVOS = [
    ("galletitas-oreo", "Galletitas Oreo", "galletitas oreo"),
    ("galletitas-sonrisas", "Galletitas Sonrisas", "galletitas sonrisas"),
    ("galletitas-pepitos", "Galletitas Pepitos", "galletitas pepitos"),
]
ing = json.load(open(os.path.join(BASE, "ingredientes.json"), encoding="utf-8"))
for c in ing["categorias"]:
    if c["nombre"] == "Desayuno y merienda":
        for iid, nombre, term in NUEVOS:
            if not any(i["id"] == iid for i in c["items"]):
                c["items"].append({"id": iid, "nombre": nombre, "cantidad_mes": "a elección",
                                   "unidad_precio": "por paquete", "busqueda": term})
json.dump(ing, open(os.path.join(BASE, "ingredientes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("galletitas agregadas al catálogo")

# 3) precios SOLO Carrefour: nuevos + faltantes (panceta, azucar-rubio)
BUSCAR = NUEVOS + [
    ("panceta", None, "panceta ahumada"),
    ("azucar-rubio", None, "azucar mascabo"),
]
REQ = {  # token obligatorio en el nombre
    "galletitas-oreo": "oreo", "galletitas-sonrisas": "sonrisas", "galletitas-pepitos": "pepitos",
    "panceta": "panceta", "azucar-rubio": "mascabo",
}
BLOCK = ["alfajor", "helado", "bañad", "banad", "tostada", "cereal", "bocadito", "turron",
         "queso", "snack mix", "cafe", "galletitas de arroz", "oblea"]
imgs = json.load(open(os.path.join(BASE, "imagenes_data.json"), encoding="utf-8"))
path_cf = os.path.join(BASE, "precios_carrefour.json")
data_cf = json.load(open(path_cf, encoding="utf-8"))
rows = {i["id"]: i for i in data_cf["items"]}

for iid, _n, term in BUSCAR:
    try:
        r = requests.get(f"https://{HOST}/api/catalog_system/pub/products/search/?ft={requests.utils.quote(term)}&_from=0&_to=8", headers=H, timeout=15)
        cands = []
        for prod in r.json():
            name = prod.get("productName", "")
            low = name.lower()
            if REQ[iid] not in low or any(b in low for b in BLOCK):
                continue
            it = prod["items"][0]
            seller = it["sellers"][0]
            offer = seller["commertialOffer"]
            price = offer.get("Price")
            if not offer.get("IsAvailable", True) or not price:
                continue
            listp = offer.get("ListPrice") or 0
            promo = None
            if price * 1.05 < listp < price * 3:
                promo = f"antes ${round(listp):,}".replace(",", ".")
            m = re.search(r"(\d+[.,]?\d*)\s*(kg|gr?s?\.?|g)\b", low)
            pres = None
            if m:
                q = float(m.group(1).replace(",", "."))
                if m.group(2).startswith("k"):
                    q *= 1000
                pres = f"{int(q)} g"
            cands.append({"name": name, "precio": round(price), "sku": it["itemId"],
                          "seller": seller["sellerId"], "link": prod.get("linkText", ""),
                          "pres": pres, "promo": promo,
                          "img": (it.get("images") or [{}])[0].get("imageUrl")})
        if not cands:
            print(f"  {iid}: SIN resultados en Carrefour")
            continue
        best = min(cands, key=lambda c: c["precio"])
        rows[iid] = {"id": iid, "producto": best["name"],
                     "presentacion": best["pres"] or "1 un",
                     "precio": best["precio"], "promo": best["promo"],
                     "url": f"https://{HOST}/{best['link']}/p",
                     "sku": best["sku"], "seller": best["seller"]}
        print(f"  {iid}: {best['name']} ${best['precio']:,} ({best['pres']})".replace(",", "."))
        if iid not in imgs and best["img"]:
            m = re.match(r"(https://[a-z]+\.vteximg\.com\.br/arquivos/ids/)(\d+)(/.*)", best["img"])
            for tu in ([m.group(1) + m.group(2) + "-140-140" + m.group(3)] if m else []) + [best["img"]]:
                try:
                    rr = requests.get(tu, headers=H, timeout=15)
                    if rr.status_code == 200 and rr.headers.get("content-type", "").startswith("image") and len(rr.content) < 220000:
                        imgs[iid] = "data:image/jpeg;base64," + base64.b64encode(rr.content).decode()
                        print(f"    imagen ok ({len(rr.content)//1024} KB)")
                        break
                except Exception:
                    continue
    except Exception as e:
        print("  fallo", iid, e)
    time.sleep(0.4)

data_cf["items"] = list(rows.values())
json.dump(data_cf, open(path_cf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(imgs, open(os.path.join(BASE, "imagenes_data.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("listo")
