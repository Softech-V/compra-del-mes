# -*- coding: utf-8 -*-
"""Refresca precios de Carrefour / Día / Jumbo por SKU vía la API pública VTEX.
Lee GROCERY_DATA de deploy/index.html y escribe tools/vtex_new.json = {store: {item_id: {...}}}."""
import re, json, io, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "C:/Users/ncort/compra-del-mes"
h = open(BASE + "/deploy/index.html", encoding="utf-8").read()
D = json.loads(re.search(r"const GROCERY_DATA = (\{.*?\});\s*\n", h, re.S).group(1))
HOSTS = {"carrefour": "https://www.carrefour.com.ar", "dia": "https://diaonline.supermercadosdia.com.ar", "jumbo": "https://www.jumbo.com.ar"}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36", "Accept": "application/json"}

def fetch(host, skus):
    url = host + "/api/catalog_system/pub/products/search?" + "&".join("fq=skuId:" + s for s in skus) + "&_from=0&_to=49"
    for attempt in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40)
            return json.loads(r.read())
        except Exception as e:
            err = e
            time.sleep(2 + attempt * 3)
    print("  ERR", host[8:20], skus[:2], err)
    return []

PROMO_RE = re.compile(r"(\d+\s?x\s?\d+|2d[ao]\s*(?:al|a)\s*\d+\s?%|\d+\s?%\s*(?:en\s+la\s+|la\s+)?2d[ao])", re.I)
out = {}
for st, host in HOSTS.items():
    rows = [(it["id"], it["precios"][st]["sku"]) for it in D["items"] if it["precios"].get(st) and it["precios"][st].get("sku")]
    by_sku = {}
    for iid, sku in rows:
        by_sku.setdefault(str(sku), []).append(iid)
    skus = list(by_sku)
    batches = [skus[i:i + 20] for i in range(0, len(skus), 20)]
    print(st, len(rows), "filas,", len(batches), "lotes")
    res = {}
    t = time.time()
    with ThreadPoolExecutor(4) as ex:
        for data in ex.map(lambda b: fetch(host, b), batches):
            for p in data or []:
                for it in p.get("items", []):
                    sid = str(it.get("itemId"))
                    if sid not in by_sku:
                        continue
                    offs = [s.get("commertialOffer", {}) for s in it.get("sellers", [])]
                    offs = [o for o in offs if o.get("Price")]
                    if not offs:
                        rec = {"precio": None, "avail": False, "nombre": p.get("productName"), "list": None, "promo": None}
                    else:
                        o = min(offs, key=lambda o: o["Price"])
                        teasers = [tz.get("Name") or tz.get("name") or "" for tz in (o.get("Teasers") or []) + (o.get("teasers") or [])]
                        promo = next((x for x in teasers if PROMO_RE.search(x)), None)
                        lp = o.get("ListPrice") or 0
                        if not promo and lp > o["Price"] * 1.02 and lp < o["Price"] * 3:
                            promo = "antes $" + format(int(round(lp)), ",").replace(",", ".")
                        rec = {"precio": o["Price"], "avail": bool(o.get("IsAvailable", True)) and (o.get("AvailableQuantity") or 0) > 0,
                               "nombre": p.get("productName"), "list": lp, "promo": promo, "teasers": teasers[:3]}
                    for iid in by_sku[sid]:
                        res[iid] = rec
    print("  ", len(res), "resueltos en", round(time.time() - t, 1), "s;", sum(1 for r in res.values() if not r["avail"]), "sin stock")
    out[st] = res
json.dump(out, open(BASE + "/tools/vtex_new.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# resumen de cambios
for st in HOSTS:
    old = {it["id"]: it["precios"][st] for it in D["items"] if it["precios"].get(st)}
    n = up = dn = big = 0
    for iid, r in out[st].items():
        o = old[iid].get("precio")
        if r["precio"] and o:
            n += 1
            ch = (r["precio"] - o) / o
            up += ch > 0.005; dn += ch < -0.005; big += abs(ch) > 0.4
    print(f"{st}: comparables {n}, suben {up}, bajan {dn}, saltos>40% {big}")
