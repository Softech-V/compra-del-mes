# -*- coding: utf-8 -*-
"""Para cada item con sku de Carrefour: precio fresco + marca + subcategoría (para agrupar tamaños y armar términos de búsqueda)."""
import json, os, sys, io, time
import requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36"}
HOST = "www.carrefour.com.ar"

pcf = json.load(open(os.path.join(BASE, "precios_carrefour.json"), encoding="utf-8"))
out_p = os.path.join(BASE, "meta_carrefour.json")
meta = json.load(open(out_p, encoding="utf-8")) if os.path.exists(out_p) else {}
rows = [r for r in pcf["items"] if r.get("sku")]
print(len(rows), "items con sku", flush=True)
ok = fail = 0
for n, r in enumerate(rows, 1):
    iid = r["id"]
    if iid in meta and meta[iid].get("ts", 0) > time.time() - 6 * 3600:
        continue
    try:
        resp = requests.get(f"https://{HOST}/api/catalog_system/pub/products/search/?fq=skuId:{r['sku']}", headers=H, timeout=20)
        prods = resp.json() if resp.status_code in (200, 206) else []
    except Exception as e:
        prods = []
    if not prods:
        meta[iid] = {"ts": time.time(), "found": False}
        fail += 1
    else:
        p = prods[0]
        it = next((x for x in p["items"] if str(x["itemId"]) == str(r["sku"])), p["items"][0])
        seller = it["sellers"][0]
        offer = seller["commertialOffer"]
        price = offer.get("Price") or 0
        listp = offer.get("ListPrice") or 0
        promo = f"antes ${round(listp):,}".replace(",", ".") if price and price * 1.05 < listp < price * 3 else None
        cats = p.get("categories") or []
        leaf = cats[0] if cats else ""
        meta[iid] = {"ts": time.time(), "found": True, "brand": p.get("brand"), "leaf": leaf,
                     "leaf_id": (p.get("categoriesIds") or [""])[0], "name": p.get("productName"),
                     "price": round(price) if price else None, "available": bool(offer.get("IsAvailable", True)) and price > 0,
                     "promo": promo, "link": p.get("linkText"), "seller": seller["sellerId"]}
        ok += 1
    if n % 100 == 0:
        print(f"  {n}/{len(rows)} ok={ok} fail={fail}", flush=True)
        json.dump(meta, open(out_p, "w", encoding="utf-8"), ensure_ascii=False)
    time.sleep(0.25)
json.dump(meta, open(out_p, "w", encoding="utf-8"), ensure_ascii=False)
print(f"LISTO ok={ok} fail={fail}", flush=True)
