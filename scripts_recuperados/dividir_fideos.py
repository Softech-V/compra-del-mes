# -*- coding: utf-8 -*-
"""Divide 'fideos' en 4 tipos de pasta, con precio/sku/imagen por cadena y remapeo de platos."""
import json, os, re, sys, io, time, base64
import requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36"}

TIPOS = [
    ("fideos-largos", "Fideos largos (spaghetti/tallarín)", "fideos spaghetti 500"),
    ("fideos-tirabuzon", "Fideos tirabuzón/fusilli", "fideos tirabuzon 500"),
    ("fideos-coditos", "Fideos coditos/moños (chicos)", "fideos coditos 500"),
    ("fideos-dedalitos", "Fideos dedalitos (sopas y lentejas)", "fideos dedalitos 500"),
]
REMAP = {  # plato -> nuevo tipo
    "fideos-salsa": "fideos-largos", "bolognesa": "fideos-largos",
    "fideos-brocoli": "fideos-tirabuzon",
    "pollo-crema": "fideos-coditos", "fideos-crema": "fideos-coditos",
    "fideos-lentejas": "fideos-dedalitos",
}

# 1) catálogo
ing = json.load(open(os.path.join(BASE, "ingredientes.json"), encoding="utf-8"))
for c in ing["categorias"]:
    c["items"] = [i for i in c["items"] if i["id"] != "fideos"]
    if c["nombre"] == "Almacén":
        for iid, nombre, term in TIPOS:
            if not any(i["id"] == iid for i in c["items"]):
                c["items"].append({"id": iid, "nombre": nombre, "cantidad_mes": "según platos", "unidad_precio": "por paquete 500g", "busqueda": term})
json.dump(ing, open(os.path.join(BASE, "ingredientes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("catálogo actualizado")

# 2) platos
P = json.load(open(os.path.join(BASE, "platos.json"), encoding="utf-8"))
for p in P["platos"]:
    nuevo = REMAP.get(p["id"])
    if nuevo:
        p["ing"] = [[nuevo if i == "fideos" else i, q] for i, q in p["ing"]]
json.dump(P, open(os.path.join(BASE, "platos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("platos remapeados")

# 3) precios por cadena VTEX (con sku e imagen)
HOSTS = {"carrefour": "www.carrefour.com.ar", "dia": "diaonline.supermercadosdia.com.ar", "jumbo": "www.jumbo.com.ar"}
imgs = json.load(open(os.path.join(BASE, "imagenes_data.json"), encoding="utf-8"))
BLOCK = ["integral", "sin tacc", "gluten", "arroz", "vegetales", "espinaca", "huevo n", "nido"]
filas = {k: {} for k in HOSTS}
for iid, nombre, term in TIPOS:
    for skey, host in HOSTS.items():
        try:
            r = requests.get(f"https://{host}/api/catalog_system/pub/products/search/?ft={requests.utils.quote(term)}&_from=0&_to=6", headers=H, timeout=15)
            cands = []
            for prod in r.json():
                name = prod.get("productName", "")
                low = name.lower()
                if any(b in low for b in BLOCK) or "500" not in name.replace("500", "500"):
                    if any(b in low for b in BLOCK):
                        continue
                it = prod["items"][0]
                seller = it["sellers"][0]
                offer = seller["commertialOffer"]
                if not offer.get("IsAvailable", True) or not offer.get("Price"):
                    continue
                cands.append({"name": name, "precio": round(offer["Price"]), "sku": it["itemId"],
                              "seller": seller["sellerId"], "link": prod.get("linkText", ""),
                              "img": (it.get("images") or [{}])[0].get("imageUrl")})
            if not cands:
                continue
            best = min(cands, key=lambda c: c["precio"])
            filas[skey][iid] = {"id": iid, "producto": best["name"], "presentacion": "paquete 500 g",
                                "precio": best["precio"], "promo": None,
                                "url": f"https://{host}/{best['link']}/p", "sku": best["sku"], "seller": best["seller"]}
            if iid not in imgs and best["img"]:
                m = re.match(r"(https://[a-z]+\.vteximg\.com\.br/arquivos/ids/)(\d+)(/.*)", best["img"])
                for tu in ([m.group(1)+m.group(2)+"-140-140"+m.group(3)] if m else []) + [best["img"]]:
                    try:
                        rr = requests.get(tu, headers=H, timeout=15)
                        if rr.status_code == 200 and rr.headers.get("content-type", "").startswith("image") and len(rr.content) < 220000:
                            imgs[iid] = "data:image/jpeg;base64," + base64.b64encode(rr.content).decode()
                            break
                    except Exception:
                        continue
        except Exception as e:
            print("  fallo", skey, iid, e)
        time.sleep(0.3)
    print(iid, "->", {k: (filas[k].get(iid) or {}).get("precio") for k in HOSTS})
json.dump(imgs, open(os.path.join(BASE, "imagenes_data.json"), "w", encoding="utf-8"), ensure_ascii=False)

# 4) volcar a archivos de precios + Coto seed (Lucchetti $1.750 de sus tickets) + ML renombrado
COTO_SEED = {
    "fideos-largos": "Fideos Spaghetti N° 7 LUCCHETTI 500g",
    "fideos-tirabuzon": "Fideos Tirabuzón LUCCHETTI 500g",
    "fideos-coditos": "Coditos LUCCHETTI Paquete 500 Gr",
    "fideos-dedalitos": "Dedalitos LUCCHETTI Paquete 500 Gr",
}
files = {"carrefour": "precios_carrefour.json", "dia": "precios_dia.json", "jumbo": "precios_jumbo.json",
         "coto": "precios_coto.json", "ml": "precios_ml.json"}
for skey, fname in files.items():
    path = os.path.join(BASE, fname)
    data = json.load(open(path, encoding="utf-8"))
    rows = {i["id"]: i for i in data["items"]}
    fila_vieja = rows.pop("fideos", None)
    if skey in HOSTS:
        rows.update(filas[skey])
    elif skey == "coto":
        for iid, prod in COTO_SEED.items():
            rows[iid] = {"id": iid, "producto": prod + " (precio de tus tickets)", "presentacion": "paquete 500 g",
                         "precio": 1750, "promo": None, "url": "https://www.coto.com.ar/sitios/cdigi/browse?Ntt=" + requests.utils.quote(prod[:25])}
    elif skey == "ml" and fila_vieja:
        fila_vieja["id"] = "fideos-largos"
        rows["fideos-largos"] = fila_vieja
    data["items"] = list(rows.values())
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(skey, "ok")
print("listo")
