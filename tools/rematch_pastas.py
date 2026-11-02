# -*- coding: utf-8 -*-
"""Busca en cada súper fideos secos 500 g de marcas preferidas (Matarazzo, Lucchetti, Don Vicente) para las
tarjetas genéricas de pastas y escribe tools/pastas_new.json {item_id: {store: row}}."""
import re, json, io, sys, time, urllib.request, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "C:/Users/ncort/compra-del-mes"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36", "Accept": "application/json"}
HOSTS = {"carrefour": "https://www.carrefour.com.ar", "dia": "https://diaonline.supermercadosdia.com.ar", "jumbo": "https://www.jumbo.com.ar"}
BRANDS = ["matarazzo", "lucchetti", "don vicente"]
# item_id -> (términos de búsqueda por forma, regex que debe cumplir el nombre, regex que NO debe cumplir)
TARGETS = {
    "fideos-largos": (["spaghetti", "tallarin", "tallarín"], r"spaghetti|spagueti|tallar", r"integral|prote|gluten|arroz|huevo|nido"),
    "fideos-tirabuzon": (["tirabuzon", "tirabuzón", "fusilli"], r"tirabuz|fusilli", r"integral|prote|gluten|arroz|huevo|legumbre"),
    "fideos-coditos": (["codito", "coditos", "mostachol", "moños", "monitos"], r"codito|mostachol|mo[ñn]o|rigat|penne", r"integral|prote|gluten|arroz|huevo"),
    "fideos-dedalitos": (["dedalitos", "dedalito"], r"dedal", r"integral|prote|gluten|arroz"),
    "fideos-soperos": (["municiones", "estrellitas", "cabello de angel", "letras"], r"munici|estrell|cabello|letra|ave maria", r"integral|prote|gluten|arroz"),
}

def size_of(name):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(kg|g|gr|grs)\b", name.lower())
    if not m:
        return None
    v = float(m.group(1).replace(",", "."))
    return v * 1000 if m.group(2) == "kg" else v

def fetch(url):
    for a in range(3):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode("utf-8", "ignore"))
        except Exception as e:
            err = e
            time.sleep(2)
    print("  ERR", url[:90], str(err)[:50])
    return None

def vtex_search(host, term):
    url = host + "/api/catalog_system/pub/products/search?ft=" + urllib.parse.quote(term) + "&_from=0&_to=24"
    data = fetch(url) or []
    out = []
    for p in data:
        for it in p.get("items", []):
            offs = [s for s in it.get("sellers", []) if s.get("commertialOffer", {}).get("Price")]
            if not offs:
                continue
            s = min(offs, key=lambda s: s["commertialOffer"]["Price"])
            o = s["commertialOffer"]
            if not o.get("IsAvailable", True) or (o.get("AvailableQuantity") or 0) <= 0:
                continue
            out.append({"producto": p["productName"], "precio": o["Price"], "sku": str(it["itemId"]), "seller": s["sellerId"],
                        "url": host + "/" + p["linkText"] + "/p", "brand": p.get("brand", ""), "list": o.get("ListPrice")})
    return out

def coto_search(term):
    url = "https://www.cotodigital.com.ar/sitios/cdigi/browse?Ntt=" + urllib.parse.quote(term) + "&format=json"
    d = fetch(url)
    out = []
    def walk(x):
        if isinstance(x, dict):
            a = x.get("attributes")
            if isinstance(a, dict) and "sku.activePrice" in a:
                name = (a.get("product.displayName") or [""])[0]
                price = float((a.get("sku.activePrice") or ["0"])[0] or 0)
                rec = x.get("detailsAction", {}).get("recordState") or ""
                out.append({"producto": name, "precio": price, "rec": rec, "a": a})
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(d)
    res = []
    for r in out:
        pid = (r["a"].get("product.repositoryId") or [""])[0]
        sid = (r["a"].get("sku.repositoryId") or [""])[0]
        slug = re.sub(r"[^a-z0-9]+", "-", r["producto"].lower()).strip("-")
        url = f"https://www.cotodigital.com.ar/sitios/cdigi/productos/{slug}/_/A-{pid.replace('prod', '')}-{sid.replace('sku', '')}-200" if pid and sid else ""
        res.append({"producto": r["producto"], "precio": r["precio"], "url": url, "brand": ""})
    return res

def pick(cands, must, mustnot):
    best = None
    for c in cands:
        n = c["producto"].lower()
        if not re.search(must, n) or re.search(mustnot, n):
            continue
        b = next((b for b in BRANDS if b in n or b in (c.get("brand") or "").lower()), None)
        if not b:
            continue
        sz = size_of(n)
        if sz and not (450 <= sz <= 550):
            continue
        rank = BRANDS.index(b)
        key = (rank, c["precio"])
        if best is None or key < best[0]:
            best = (key, c, b, sz or 500)
    return best

out = {}
for iid, (terms, must, mustnot) in TARGETS.items():
    out[iid] = {}
    print("##", iid)
    for st in ["carrefour", "dia", "jumbo", "coto"]:
        cands = []
        for t in terms:
            for b in BRANDS:
                q = f"fideos {t} {b}"
                cands += coto_search(q) if st == "coto" else vtex_search(HOSTS[st], q)
                time.sleep(0.4)
        seen = set(); uniq = []
        for c in cands:
            k = c["producto"] + str(c["precio"])
            if k in seen: continue
            seen.add(k); uniq.append(c)
        b = pick(uniq, must, mustnot)
        if b:
            key, c, brand, sz = b
            row = {"producto": c["producto"], "presentacion": f"{int(sz)} g", "precio": int(round(c["precio"])), "promo": None, "size": float(sz), "url": c["url"]}
            if "sku" in c:
                row["sku"] = c["sku"]; row["seller"] = c["seller"]
            out[iid][st] = row
            print(f"  {st}: {c['producto'][:55]} ${row['precio']}")
        else:
            print(f"  {st}: sin marca preferida ({len(uniq)} candidatos)")
json.dump(out, open(BASE + "/tools/pastas_new.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
