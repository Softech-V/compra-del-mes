# -*- coding: utf-8 -*-
"""Aplica tools/vtex_new.json y tools/coto_new.json sobre GROCERY_DATA de deploy/index.html.
Guarda backup en backups/, actualiza fecha y historial.prev. No toca ML ni Molinos."""
import re, json, io, sys, os, shutil, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "C:/Users/ncort/compra-del-mes"
HTML = BASE + "/deploy/index.html"
HOY = "07/10/2026"
# filas cuyo SKU apunta a otro tipo de producto (detectado por nombre VTEX actual): sin precio hasta re-matchear
NULL = {
    "dia": ["leche-crecimiento", "patitas", "panales", "panales-xg", "condimento-alicante-arroz-sobre-25-g", "ricota", "arroz-risotto"],
    "jumbo": ["leche-chocolatada", "premezcla-exquisita-cookies-choco-con-ch", "ribs-de-cerdo-x-kg", "cerveza-mecklenburger-pilsener-500-ml"],
    "carrefour": [],
    "coto": [],
}
h = open(HTML, encoding="utf-8").read()
m = re.search(r"const GROCERY_DATA = (\{.*?\});\s*\n", h, re.S)
D = json.loads(m.group(1))
os.makedirs(BASE + "/backups", exist_ok=True)
bk = BASE + "/backups/index." + D["fecha"].replace("/", "-") + ".html"
if not os.path.exists(bk):
    shutil.copy(HTML, bk)
items = {it["id"]: it for it in D["items"]}

# snapshot previo para los deltas de la página
prev = {"fecha": D["fecha"], "precios": {}}
for it in D["items"]:
    prev["precios"][it["id"]] = {k: (v.get("precio") if v else None) for k, v in it["precios"].items()}

new = json.load(open(BASE + "/tools/vtex_new.json", encoding="utf-8"))
if os.path.exists(BASE + "/tools/coto_new.json"):
    new["coto"] = json.load(open(BASE + "/tools/coto_new.json", encoding="utf-8"))

stats = {}
for st, res in new.items():
    s = {"ok": 0, "agotado": 0, "revisar": 0, "err": 0, "null": 0, "sin_fila": 0}
    for iid, r in res.items():
        it = items.get(iid)
        row = it["precios"].get(st) if it else None
        if not row:
            s["sin_fila"] += 1
            continue
        row.pop("agotado", None); row.pop("revisar", None)
        if "err" in r:
            s["err"] += 1
            continue
        old = row.get("precio")
        if r.get("nombre"):
            row["producto"] = r["nombre"]
        if r.get("gone") or not r.get("precio") or not r.get("avail"):
            row["precio"] = None
            row["agotado"] = True
            s["agotado"] += 1
            continue
        p = float(r["precio"])
        if old and (p > old * 3 or p < old / 3):
            row["precio"] = None
            row["revisar"] = True
            s["revisar"] += 1
            continue
        row["precio"] = int(round(p))
        row["promo"] = r.get("promo")
        s["ok"] += 1
    for iid in NULL.get(st, []):
        it = items.get(iid)
        if it and it["precios"].get(st) and it["precios"][st].get("precio") is not None:
            it["precios"][st]["precio"] = None
            it["precios"][st]["revisar"] = True
            s["null"] += 1
    stats[st] = s
    print(st, s)

D["fecha"] = HOY
D["historial"]["prev"] = prev
js = json.dumps(D, ensure_ascii=False)
h2 = h[:m.start(1)] + js + h[m.end(1):]
open(HTML, "w", encoding="utf-8").write(h2)
open(BASE + "/compra-del-mes.html", "w", encoding="utf-8").write(h2)
con = {st: sum(1 for it in D["items"] if it["precios"].get(st) and it["precios"][st].get("precio")) for st in ["carrefour", "coto", "dia", "jumbo", "ml", "molinos"]}
print("con precio por tienda:", con)
print("escrito", HTML, len(h2) // 1024, "KB")
