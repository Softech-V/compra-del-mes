# -*- coding: utf-8 -*-
"""Vuelca meta_carrefour.json (precio fresco por sku) en refresh_raw.json['carrefour'] y hace que aplicar_refresh conserve sku/seller."""
import json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
meta = json.load(open(os.path.join(BASE, "meta_carrefour.json"), encoding="utf-8"))
pcf = json.load(open(os.path.join(BASE, "precios_carrefour.json"), encoding="utf-8"))
old = {r["id"]: r for r in pcf["items"]}
raw_p = os.path.join(BASE, "refresh_raw.json")
raw = json.load(open(raw_p, encoding="utf-8")) if os.path.exists(raw_p) else {}
cf = {}
no_disp = []
for iid, m in meta.items():
    if not m.get("found"):
        continue
    if not m.get("available") or not m.get("price"):
        no_disp.append(iid); continue
    o = old.get(iid, {})
    cf[iid] = {"producto": m.get("name") or o.get("producto", ""), "presentacion": o.get("presentacion", "1 un"),
               "precio": m["price"], "promo": m.get("promo"),
               "url": f"https://www.carrefour.com.ar/{m.get('link')}/p" if m.get("link") else o.get("url"),
               "sku": o.get("sku"), "seller": m.get("seller") or o.get("seller", "1")}
raw["carrefour"] = cf
json.dump(raw, open(raw_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"carrefour: {len(cf)} precios frescos; sin stock ahora: {len(no_disp)}")
for i in no_disp[:15]:
    print("   sin stock:", old.get(i, {}).get("producto", i))

# parche aplicar_refresh: conservar sku/seller
p = os.path.join(BASE, "aplicar_refresh.py")
s = open(p, encoding="utf-8").read()
old_line = '''                 "precio": round(float(row["precio"])), "promo": row.get("promo"), "url": row.get("url")}'''
new_line = '''                 "precio": round(float(row["precio"])), "promo": row.get("promo"), "url": row.get("url")}
        for k in ("sku", "seller"):
            v = row.get(k) or (viejos.get(iid) or {}).get(k)
            if v:
                nuevo[k] = v'''
if old_line in s and "for k in (\"sku\", \"seller\")" not in s:
    s = s.replace(old_line, new_line, 1)
    open(p, "w", encoding="utf-8").write(s)
    print("aplicar_refresh: conserva sku/seller")
