# -*- coding: utf-8 -*-
"""Para cada producto comprado el 11/10 busca el mismo producto (marca + tipo + tamaño) en Coto, Carrefour, Día y Jumbo
vía sus buscadores públicos, y arma tools/precios_compra_1110.json + una tabla."""
import re, json, io, sys, time, urllib.request, urllib.parse, unicodedata
from concurrent.futures import ThreadPoolExecutor
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "C:/Users/ncort/compra-del-mes"
C = json.load(open(BASE + "/tools/compras_1110.json", encoding="utf-8"))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36", "Accept": "application/json"}
HOSTS = {"carrefour": "https://www.carrefour.com.ar", "dia": "https://diaonline.supermercadosdia.com.ar", "jumbo": "https://www.jumbo.com.ar"}
LABEL = {"carrefour": "Carrefour", "coto": "Coto", "dia": "Día", "jumbo": "Jumbo", "ml": "ML"}

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s)

def fetch(url):
    err = None
    for a in range(3):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode("utf-8", "ignore"))
        except Exception as e:
            err = e
            time.sleep(1.5)
    return None

def size_of(name, unit):
    n = norm(name)
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(kg|g|gr|grs|grm|ml|cc|l|lt|lts|un|u|ud|unid|unidades|panos|paños)\b", n)
    if not m:
        return None
    v = float(m.group(1).replace(",", "."))
    u = m.group(2)
    if u in ("kg", "l", "lt", "lts"):
        v *= 1000
    return v

def vtex_search(host, term):
    d = fetch(host + "/api/catalog_system/pub/products/search?ft=" + urllib.parse.quote(term) + "&_from=0&_to=30") or []
    out = []
    for p in d:
        for it in p.get("items", []):
            offs = [s for s in it.get("sellers", []) if s.get("commertialOffer", {}).get("Price")]
            if not offs:
                continue
            s = min(offs, key=lambda s: s["commertialOffer"]["Price"])
            o = s["commertialOffer"]
            out.append({"producto": p["productName"], "precio": o["Price"], "avail": bool(o.get("IsAvailable", True)) and (o.get("AvailableQuantity") or 0) > 0,
                        "sku": str(it["itemId"]), "seller": s["sellerId"], "url": host + "/" + p["linkText"] + "/p", "brand": p.get("brand", ""), "list": o.get("ListPrice")})
    return out

def coto_search(term):
    d = fetch("https://www.cotodigital.com.ar/sitios/cdigi/browse?Ntt=" + urllib.parse.quote(term) + "&format=json")
    out = []
    def walk(x):
        if isinstance(x, dict):
            a = x.get("attributes")
            if isinstance(a, dict) and "sku.activePrice" in a:
                name = (a.get("product.displayName") or [""])[0]
                price = float((a.get("sku.activePrice") or ["0"])[0] or 0)
                pid = (a.get("product.repositoryId") or [""])[0]; sid = (a.get("sku.repositoryId") or [""])[0]
                slug = re.sub(r"[^a-z0-9]+", "-", norm(name)).strip("-")
                url = f"https://www.cotodigital.com.ar/sitios/cdigi/productos/{slug}/_/A-{pid.replace('prod','')}-{sid.replace('sku','')}-200" if pid and sid else ""
                out.append({"producto": name, "precio": price, "avail": price > 0, "url": url, "brand": ""})
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(d)
    return out

def best_match(cands, p):
    b = [t for t in norm(p["marca"]).split() if len(t) > 1]
    tt = [t for t in norm(p["tipo"]).split() if len(t) > 2]
    best = None
    for c in cands:
        if not c.get("avail") or not c["precio"]:
            continue
        n = norm(c["producto"] + " " + (c.get("brand") or ""))
        if p["marca"] not in ("s/m", "DIA", "Coto") and not all(x in n for x in b):
            continue
        if not any(n.find(t[:5]) >= 0 for t in tt):
            continue
        sz = size_of(c["producto"], p["unit"])
        ok_size = sz is None or 0.75 <= sz / p["size"] <= 1.33
        if not ok_size:
            continue
        key = (0 if sz else 1, c["precio"])
        if best is None or key < best[0]:
            best = (key, c, sz)
    return best

def work(args):
    store_bought, p = args
    res = {}
    term = f"{p['tipo']} {p['marca']}" if p["marca"] not in ("s/m", "DIA", "Coto") else p["tipo"]
    for st in ["coto", "carrefour", "dia", "jumbo"]:
        cands = coto_search(term) if st == "coto" else vtex_search(HOSTS[st], term)
        bm = best_match(cands, p)
        if bm:
            key, c, sz = bm
            res[st] = {"producto": c["producto"], "precio": int(round(c["precio"])), "size": sz, "url": c["url"], "sku": c.get("sku"), "seller": c.get("seller"), "list": c.get("list")}
        time.sleep(0.3)
    return store_bought, p["nombre"], res

jobs = [(st, p) for st in ["dia", "coto", "ml"] for p in C[st]["items"]]
with ThreadPoolExecutor(3) as ex:
    results = list(ex.map(work, jobs))
json.dump(results, open(BASE + "/tools/precios_compra_1110.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def unitp(r, p):
    sz = r.get("size") or p["size"]
    return r["precio"] / sz * p["size"]

coto_sum = coto_sum_sj = 0
for store, name, res in results:
    p = next(x for x in C[store]["items"] if x["nombre"] == name)
    cells = []
    for st in ["coto", "carrefour", "dia", "jumbo"]:
        r = res.get(st)
        cells.append(f"{LABEL[st]} ${unitp(r, p):,.0f}".replace(",", ".") if r else f"{LABEL[st]} —")
    pag = p.get("pagado")
    print(f"[{LABEL[store]}] {name[:52]} x{p['qty']}" + (f" | pagaste ${pag:,.0f}".replace(",", ".") if pag else "") + " || " + " | ".join(cells))
    if store == "coto" and res.get("coto"):
        coto_sum += res["coto"]["precio"] * p["qty"]
        if not p.get("fuera_del_resumen"):
            coto_sum_sj += res["coto"]["precio"] * p["qty"]
print(f"\nSuma precios Coto de lista hoy (productos encontrados): ${coto_sum:,.0f} con jamón / ${coto_sum_sj:,.0f} sin jamón; ticket subtotal $240.950".replace(",", "."))
