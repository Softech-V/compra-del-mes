# -*- coding: utf-8 -*-
"""Aplica ml_new_0907.jsonl sobre precios_ml.json (actualiza por id; los ids no tocados quedan igual)."""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
d = json.load(open("precios_ml.json", encoding="utf-8"))
by = {r["id"]: i for i, r in enumerate(d["items"])}
n = m = 0
for line in open("ml_new_0907.jsonl", encoding="utf-8"):
    line = line.strip()
    if not line: continue
    r = json.loads(line)
    row = {"id": r["id"], "producto": r["producto"], "presentacion": r.get("presentacion") or "", "precio": r.get("precio"), "promo": r.get("promo"), "url": r.get("url")}
    if r["id"] in by:
        old = d["items"][by[r["id"]]]
        d["items"][by[r["id"]]] = row; n += 1
        if old.get("precio") and row["precio"]:
            ch = (row["precio"] - old["precio"]) / old["precio"] * 100
            if abs(ch) > 40: print(f"  >40%: {r['id']}: ${old['precio']} ({old.get('presentacion')}) -> ${row['precio']} ({row['presentacion']})")
    else:
        d["items"].append(row); by[r["id"]] = len(d["items"]) - 1; m += 1
d["fecha"] = "07/09/2026"
json.dump(d, open("precios_ml.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"ML: {n} actualizados, {m} nuevos, total {len(d['items'])}")
