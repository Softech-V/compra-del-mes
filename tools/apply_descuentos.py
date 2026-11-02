# -*- coding: utf-8 -*-
"""Reemplaza la lista `descuentos` de GROCERY_DATA en deploy/index.html y compra-del-mes.html
con el JSON indicado. Uso: python tools/apply_descuentos.py tools/descuentos_nov2026.json 02/11/2026"""
import json, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "C:/Users/ncort/compra-del-mes"
src, fecha = sys.argv[1], sys.argv[2]
desc = json.load(open(BASE + "/" + src, encoding="utf-8"))
print(len(desc), "entradas,", len({d["programa"] for d in desc}), "programas")
for fn in ["deploy/index.html", "compra-del-mes.html"]:
    p = BASE + "/" + fn
    h = open(p, encoding="utf-8").read()
    m = re.search(r"const GROCERY_DATA = (\{.*?\});\s*\n", h, re.S)
    D = json.loads(m.group(1))
    D["descuentos"] = desc
    D["fecha_descuentos"] = fecha
    h = h[:m.start(1)] + json.dumps(D, ensure_ascii=False) + h[m.end(1):]
    open(p, "w", encoding="utf-8").write(h)
    print(fn, "| fecha precios", D["fecha"], "| descuentos", len(D["descuentos"]), "| items", len(D["items"]))
