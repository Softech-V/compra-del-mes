# -*- coding: utf-8 -*-
"""Aplica tools/ml_new_1110.jsonl (fichas ML leídas el 11/10) sobre las filas ml de GROCERY_DATA en deploy/index.html y compra-del-mes.html.
Mantiene el nombre normalizado viejo; actualiza precio, url y marca agotado. Filas 'pack dividido por unidad' se dividen."""
import re, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "C:/Users/ncort/compra-del-mes"
rows = [json.loads(l) for l in open(BASE + "/tools/ml_new_1110.jsonl", encoding="utf-8") if l.strip()]
DIV = {"atun-lata": 3}
for fn in ["deploy/index.html", "compra-del-mes.html"]:
    path = BASE + "/" + fn
    h = open(path, encoding="utf-8").read()
    m = re.search(r"const GROCERY_DATA = (\{.*?\});\s*\n", h, re.S)
    D = json.loads(m.group(1))
    items = {it["id"]: it for it in D["items"]}
    n = ag = 0
    for r in rows:
        it = items.get(r["id"]); row = it and it["precios"].get("ml")
        if not row: continue
        row.pop("agotado", None); row.pop("revisar", None)
        if r.get("agotado") or not r.get("precio"):
            row["precio"] = None; row["agotado"] = True; ag += 1
        else:
            p = r["precio"] / DIV.get(r["id"], 1)
            row["precio"] = int(round(p)); row["promo"] = None; n += 1
        if r.get("url") and not r["url"].startswith("["):
            row["url"] = r["url"].split("?")[0]
    D["fecha_ml"] = "11/10/2026 (parcial: 65 de 377)"
    h = h[:m.start(1)] + json.dumps(D, ensure_ascii=False) + h[m.end(1):]
    open(path, "w", encoding="utf-8").write(h)
    print(fn, "ML actualizados:", n, "| agotados:", ag)
