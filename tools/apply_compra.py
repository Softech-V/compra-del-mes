# -*- coding: utf-8 -*-
"""1) Reemplaza las filas de pastas genéricas por marcas preferidas (pastas_new.json).
2) Agrega al catálogo los productos comprados el 11/10 que no estaban (precios_compra_1110.json), con def 0
   (no entran al plan solos; aparecen en Productos para elegirlos)."""
import re, json, io, sys, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "C:/Users/ncort/compra-del-mes"
C = json.load(open(BASE + "/tools/compras_1110.json", encoding="utf-8"))
P = json.load(open(BASE + "/tools/precios_compra_1110.json", encoding="utf-8"))
PASTAS = json.load(open(BASE + "/tools/pastas_new.json", encoding="utf-8"))

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s)
def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", norm(s))).strip("-")[:48]

CAT = {"fideos": "Almacén", "tapas": "Heladera", "queso": "Heladera", "crema": "Heladera", "papel": "Limpieza y hogar", "rollo": "Limpieza y hogar",
       "galletitas": "Desayuno y merienda", "arroz": "Almacén", "manteca": "Heladera", "leche": "Desayuno y merienda", "limpiador": "Limpieza y hogar",
       "tomate": "Almacén", "jamon": "Heladera", "nuggets": "Heladera", "ravioles": "Heladera", "agua": "Bebidas", "antigrasa": "Limpieza y hogar",
       "limpiavidrios": "Limpieza y hogar", "suavizante": "Limpieza y hogar", "desinfectante": "Limpieza y hogar", "salsa": "Almacén",
       "lavandina": "Limpieza y hogar", "aceite": "Almacén", "mermelada": "Desayuno y merienda", "pan": "Desayuno y merienda",
       "pastillas": "Limpieza y hogar", "sal": "Limpieza y hogar", "cacao": "Desayuno y merienda", "jabon": "Limpieza y hogar"}
CANAL = {"Heladera": "heladera"}

for fn in ["deploy/index.html", "compra-del-mes.html"]:
    path = BASE + "/" + fn
    h = open(path, encoding="utf-8").read()
    m = re.search(r"const GROCERY_DATA = (\{.*?\});\s*\n", h, re.S)
    D = json.loads(m.group(1))
    items = {it["id"]: it for it in D["items"]}
    # 1) pastas
    n1 = 0
    for iid, rows in PASTAS.items():
        it = items.get(iid)
        if not it:
            continue
        for st, row in rows.items():
            old = it["precios"].get(st) or {}
            new = dict(old)
            new.update(row)
            new["agotado"] = False; new.pop("revisar", None); new.pop("agotado", None)
            it["precios"][st] = new
            n1 += 1
    # 2) productos comprados que faltan
    allnames = [(it, norm(" ".join(r["producto"] for r in it["precios"].values() if r) + " " + it["nombre"])) for it in D["items"]]
    added = 0
    for store, name, res in P:
        p = next(x for x in C[store]["items"] if x["nombre"] == name)
        if not res:
            continue
        b = [t for t in norm(p["marca"]).split() if len(t) > 1 and p["marca"] not in ("s/m", "DIA", "Coto")]
        tt = [t for t in norm(p["tipo"]).split() if len(t) > 2]
        exists = None
        for it, nm in allnames:
            if b and not all(x in nm for x in b):
                continue
            if not all(nm.find(t[:5]) >= 0 for t in tt):
                continue
            # tamaño parecido en alguna fila
            exists = it
            break
        if exists:
            # completar filas que falten en el item existente
            for st, r in res.items():
                if not exists["precios"].get(st) or not exists["precios"][st].get("precio"):
                    exists["precios"][st] = {"producto": r["producto"], "presentacion": f"{int(r['size'] or p['size'])} {p['unit']}", "precio": r["precio"], "promo": None,
                                             "size": float(r["size"] or p["size"]), "url": r["url"], **({"sku": r["sku"], "seller": r["seller"]} if r.get("sku") else {})}
            continue
        iid = slug(p["nombre"])
        if iid in items:
            continue
        cat = next((v for k, v in CAT.items() if norm(p["tipo"]).startswith(k)), "Almacén")
        unit = p["unit"] if p["unit"] in ("g", "ml") else "un"
        it = {"id": iid, "nombre": p["nombre"], "cat": cat, "cantidad": "a elección", "need": 0, "unit": unit, "kind": "pack",
              "standalone": {"paso": f"{p['size']} {p['unit']}" if unit != "un" else "envase", "base": p["size"] if unit != "un" else 1, "def": 0},
              "precios": {k: None for k in ["carrefour", "coto", "dia", "jumbo", "ml", "molinos"]}}
        if cat in CANAL:
            it["canal"] = CANAL[cat]
        for st, r in res.items():
            it["precios"][st] = {"producto": r["producto"], "presentacion": f"{int(r['size'] or p['size'])} {p['unit']}", "precio": r["precio"], "promo": None,
                                 "size": float(r["size"] or p["size"]), "url": r["url"], **({"sku": r["sku"], "seller": r["seller"]} if r.get("sku") else {})}
        D["items"].append(it); items[iid] = it; added += 1
        print("  +", cat, "|", p["nombre"][:50], "|", {k: v["precio"] for k, v in it["precios"].items() if v})
    h = h[:m.start(1)] + json.dumps(D, ensure_ascii=False) + h[m.end(1):]
    open(path, "w", encoding="utf-8").write(h)
    print(fn, "filas de pasta actualizadas:", n1, "| items agregados:", added, "| total items:", len(D["items"]))
