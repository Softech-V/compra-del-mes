# -*- coding: utf-8 -*-
"""Refresca precios de Coto leyendo cada ficha de producto con ?format=json (Endeca).
Escribe tools/coto_new.json = {item_id: {precio, list, promo, avail, nombre}}."""
import re, json, io, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "C:/Users/ncort/compra-del-mes"
h = open(BASE + "/deploy/index.html", encoding="utf-8").read()
D = json.loads(re.search(r"const GROCERY_DATA = (\{.*?\});\s*\n", h, re.S).group(1))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36", "Accept": "application/json"}
rows = [(it["id"], it["precios"]["coto"]["url"]) for it in D["items"] if it["precios"].get("coto") and it["precios"]["coto"].get("url")]
print(len(rows), "filas Coto")

def find_rec(x):
    if isinstance(x, dict):
        a = x.get("attributes")
        if isinstance(a, dict) and ("sku.activePrice" in a or "sku.referencePrice" in a):
            return a
        for v in x.values():
            r = find_rec(v)
            if r:
                return r
    elif isinstance(x, list):
        for v in x:
            r = find_rec(v)
            if r:
                return r
    return None

def first(a, k):
    v = a.get(k)
    if isinstance(v, list):
        return v[0] if v else None
    return v

def one(x):
    iid, url = x
    u = url.split("?")[0]
    u = urllib.parse.quote(u.replace("www.coto.com.ar", "www.cotodigital.com.ar"), safe=":/%") + "?format=json"
    d = None
    err = ""
    for a in range(3):
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=45).read().decode("utf-8", "ignore"))
            break
        except Exception as e:
            err = str(e)[:60]
            time.sleep(2 + a * 2)
    if d is None:
        return iid, {"err": err}
    a = find_rec(d)
    if not a:
        return iid, {"precio": None, "avail": False, "gone": True, "nombre": None, "list": None, "promo": None}
    try:
        price = float(first(a, "sku.activePrice") or 0)
    except Exception:
        price = 0
    lp = None
    try:
        dp = json.loads(first(a, "sku.dtoPrice") or "{}")
        lp = dp.get("precioLista")
    except Exception:
        pass
    promo = None
    try:
        descs = json.loads(first(a, "product.dtoDescuentos") or "[]")
        for ds in descs:
            txt = json.dumps(ds, ensure_ascii=False)
            m = re.search(r'"(?:descripcion|nombre|textoDescuento|leyenda)"\s*:\s*"([^"]{3,60})"', txt)
            if m:
                promo = m.group(1)
                break
    except Exception:
        pass
    if not promo and lp and price and lp > price * 1.02:
        promo = "antes $" + format(int(round(lp)), ",").replace(",", ".")
    stock = first(a, "sku.stock") or first(a, "product.stock")
    avail = price > 0 and (stock is None or str(stock) not in ("0", "0.0", "false", "False"))
    return iid, {"precio": price or None, "avail": avail, "nombre": first(a, "product.displayName"), "list": lp, "promo": promo}

t = time.time()
with ThreadPoolExecutor(3) as ex:
    res = dict(ex.map(one, rows))
json.dump(res, open(BASE + "/tools/coto_new.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
old = {it["id"]: it["precios"]["coto"] for it in D["items"] if it["precios"].get("coto")}
n = up = dn = big = 0
for iid, r in res.items():
    o = old[iid].get("precio")
    if r.get("precio") and o:
        n += 1
        ch = (r["precio"] - o) / o
        up += ch > 0.005; dn += ch < -0.005; big += abs(ch) > 0.4
print(f"coto: {len(res)} en {round(time.time()-t)} s; errores {sum(1 for r in res.values() if 'err' in r)}, desaparecidos {sum(1 for r in res.values() if r.get('gone'))}, sin stock {sum(1 for r in res.values() if not r.get('avail') and not r.get('gone') and 'err' not in r)}")
print(f"coto: comparables {n}, suben {up}, bajan {dn}, saltos>40% {big}")
