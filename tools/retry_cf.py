# -*- coding: utf-8 -*-
import json, urllib.request, time, re, io, sys
from concurrent.futures import ThreadPoolExecutor
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "C:/Users/ncort/compra-del-mes"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36", "Accept": "application/json"}
miss = json.load(open(BASE + "/tools/cf_missing.json"))
PROMO_RE = re.compile(r"(\d+\s?x\s?\d+|2d[ao]\s*(?:al|a)\s*\d+\s?%)", re.I)

def one(x):
    iid, sku = x
    d = None
    err = ""
    for a in range(3):
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(f"https://www.carrefour.com.ar/api/catalog_system/pub/products/search?fq=skuId:{sku}", headers=UA), timeout=40).read())
            break
        except Exception as e:
            err = str(e)[:60]
            time.sleep(2)
    if d is None:
        return iid, {"err": err}
    for p in d:
        for it in p["items"]:
            if str(it["itemId"]) == str(sku):
                offs = [s["commertialOffer"] for s in it["sellers"] if s["commertialOffer"].get("Price")]
                if not offs:
                    return iid, {"precio": None, "avail": False, "nombre": p["productName"], "list": None, "promo": None}
                o = min(offs, key=lambda o: o["Price"])
                lp = o.get("ListPrice") or 0
                teasers = [t.get("Name") or t.get("name") or "" for t in (o.get("Teasers") or [])]
                promo = next((t for t in teasers if PROMO_RE.search(t)), None)
                if not promo and lp > o["Price"] * 1.02 and lp < o["Price"] * 3:
                    promo = "antes $" + format(int(round(lp)), ",").replace(",", ".")
                return iid, {"precio": o["Price"], "avail": bool(o.get("IsAvailable", True)) and (o.get("AvailableQuantity") or 0) > 0, "nombre": p["productName"], "list": lp, "promo": promo}
    return iid, {"precio": None, "avail": False, "nombre": None, "list": None, "promo": None, "gone": True}

with ThreadPoolExecutor(3) as ex:
    res = dict(ex.map(one, miss))
new = json.load(open(BASE + "/tools/vtex_new.json", encoding="utf-8"))
ok = 0
for k, v in res.items():
    if "err" in v:
        print("ERR", k, v["err"])
        continue
    new["carrefour"][k] = v
    ok += 1
json.dump(new, open(BASE + "/tools/vtex_new.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("reintentados ok:", ok, "| desaparecidos:", sum(1 for v in res.values() if v.get("gone")), "| sin stock:", sum(1 for v in res.values() if not v.get("avail") and not v.get("gone") and "err" not in v))
