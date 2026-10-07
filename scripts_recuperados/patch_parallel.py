# -*- coding: utf-8 -*-
"""Paraleliza enrich_carrefour.py, refresh_precios.py y scrape_coto.py con pools de hilos."""
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))

# ---- enrich_carrefour.py
p = os.path.join(BASE, "enrich_carrefour.py")
s = open(p, encoding="utf-8").read()
old = s[s.index("ok = fail = 0"):s.index('print(f"LISTO ok={ok} fail={fail}", flush=True)')]
new = '''ok = fail = 0
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
lock = threading.Lock()
pend = [r for r in rows if not (r["id"] in meta and meta[r["id"]].get("ts", 0) > time.time() - 6 * 3600)]
print(len(pend), "pendientes", flush=True)
def work(r):
    try:
        resp = requests.get(f"https://{HOST}/api/catalog_system/pub/products/search/?fq=skuId:{r['sku']}", headers=H, timeout=25)
        prods = resp.json() if resp.status_code in (200, 206) else []
    except Exception:
        prods = []
    if not prods:
        return r["id"], {"ts": time.time(), "found": False}
    p = prods[0]
    it = next((x for x in p["items"] if str(x["itemId"]) == str(r["sku"])), p["items"][0])
    seller = it["sellers"][0]
    offer = seller["commertialOffer"]
    price = offer.get("Price") or 0
    listp = offer.get("ListPrice") or 0
    promo = f"antes ${round(listp):,}".replace(",", ".") if price and price * 1.05 < listp < price * 3 else None
    cats = p.get("categories") or []
    return r["id"], {"ts": time.time(), "found": True, "brand": p.get("brand"), "leaf": cats[0] if cats else "",
                     "leaf_id": (p.get("categoriesIds") or [""])[0], "name": p.get("productName"),
                     "price": round(price) if price else None, "available": bool(offer.get("IsAvailable", True)) and price > 0,
                     "promo": promo, "link": p.get("linkText"), "seller": seller["sellerId"]}
n = 0
with ThreadPoolExecutor(max_workers=6) as ex:
    for fut in as_completed([ex.submit(work, r) for r in pend]):
        iid, m = fut.result()
        with lock:
            meta[iid] = m
            n += 1
            if m.get("found"): ok += 1
            else: fail += 1
            if n % 100 == 0:
                print(f"  {n}/{len(pend)} ok={ok} fail={fail}", flush=True)
                json.dump(meta, open(out_p, "w", encoding="utf-8"), ensure_ascii=False)
json.dump(meta, open(out_p, "w", encoding="utf-8"), ensure_ascii=False)
'''
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("enrich paralelo ok")

# ---- refresh_precios.py
p = os.path.join(BASE, "refresh_precios.py")
s = open(p, encoding="utf-8").read()
old = s[s.index('resultados = {k: {} for k in STORES}'):s.index('with open(os.path.join(BASE, "refresh_raw.json")')]
new = '''resultados = {k: {} for k in STORES}
from concurrent.futures import ThreadPoolExecutor
def _one(host, it):
    try:
        url = f"https://{host}/api/catalog_system/pub/products/search/?ft={requests.utils.quote(it['term'])}&_from=0&_to=5"
        r = requests.get(url, headers=H, timeout=20)
        prods = r.json() if r.status_code in (200, 206) else []
    except Exception:
        prods = []
    best = pick(prods, it["term"], it["id"]) if prods else None
    if not best:
        return it["id"], None
    return it["id"], {"producto": best["name"], "presentacion": presentacion(best["name"], it["id"]),
                      "precio": best["price"], "promo": best["promo"], "url": best["url"].replace("HOST", host)}
for skey, host in STORES.items():
    print(f"--- {skey} ---", flush=True)
    with ThreadPoolExecutor(max_workers=5) as ex:
        for n, (iid, row) in enumerate(ex.map(lambda it: _one(host, it), items), 1):
            if row:
                resultados[skey][iid] = row
            if n % 200 == 0:
                print(f"  {skey} {n}/{len(items)} con precio={len(resultados[skey])}", flush=True)
    print(f"{skey}: {len(resultados[skey])}/{len(items)} con precio", flush=True)

'''
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("refresh paralelo ok")

# ---- scrape_coto.py: pool de 3 hilos en el loop principal
p = os.path.join(BASE, "scrape_coto.py")
s = open(p, encoding="utf-8").read()
old = s[s.index("    result, debug, missing = {}, {}, []"):s.index('    with open(SCRATCH + r"\\refresh_coto.json"')]
new = '''    result, debug, missing = {}, {}, []
    from concurrent.futures import ThreadPoolExecutor
    def _one(args):
        iid, term, prefer_kg, avoid_meat = args
        doc = fetch(term)
        recs = extract_records(doc)
        best, pool = pick(recs, term, prefer_kg, avoid_meat, reject=REJECT.get(iid, ()), require=REQUIRE.get(iid, ())) if recs else (None, [])
        return iid, term, recs, best, pool
    with ThreadPoolExecutor(max_workers=3) as ex:
        for i, (iid, term, recs, best, pool) in enumerate(ex.map(_one, items), 1):
            if best:
                result[iid] = {
                    "producto": re.sub(r"\\s+", " ", best["name"]).strip(),
                    "presentacion": presentacion(best["name"], best["unidad"]),
                    "precio": int(round(best["price"])),
                    "promo": best["promo"],
                    "url": best["url"],
                }
            else:
                missing.append(iid)
            if i % 100 == 0:
                print(f"[{i}/{len(items)}] resueltos={len(result)}", flush=True)
            debug[iid] = {"term": term, "n_records": len(recs),
                          "candidatos": [{"n": c["name"], "p": c["price"], "promo": c["promo"]} for c in pool]}

'''
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("coto paralelo ok")
