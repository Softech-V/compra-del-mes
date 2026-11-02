# -*- coding: utf-8 -*-
"""Reintenta en Coto las filas que el refresh marcó 'gone' (la web devolvió una página sin atributos) y
aplica el resultado directo a deploy/index.html y compra-del-mes.html sin tocar historial.prev."""
import json, re, time, io, sys
from concurrent.futures import ThreadPoolExecutor
BASE = "C:/Users/ncort/compra-del-mes"
src = open(BASE + "/tools/refresh_coto.py", encoding="utf-8").read()
exec(src[:src.index("t = time.time()")])  # define D, rows, one(), etc.
res = json.load(open(BASE + "/tools/coto_new.json", encoding="utf-8"))
pend = [(iid, url) for iid, url in rows if res.get(iid, {}).get("gone")]
print("gone a reintentar:", len(pend), flush=True)
t = time.time()
for ronda in range(3):
    if not pend:
        break
    with ThreadPoolExecutor(2) as ex:
        out = dict(ex.map(one, pend))
    res.update(out)
    pend = [(iid, url) for iid, url in pend if out.get(iid, {}).get("gone") or "err" in out.get(iid, {})]
    print(" ronda", ronda + 1, "quedan", len(pend), round(time.time() - t), "s", flush=True)
    time.sleep(5)
json.dump(res, open(BASE + "/tools/coto_new.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
rec = {iid: r for iid, r in res.items() if r.get("precio") and r.get("avail")}
for fn in ["deploy/index.html", "compra-del-mes.html"]:
    path = BASE + "/" + fn
    h = open(path, encoding="utf-8").read()
    m = re.search(r"const GROCERY_DATA = (\{.*?\});\s*\n", h, re.S)
    DD = json.loads(m.group(1))
    n = 0
    for it in DD["items"]:
        row = it["precios"].get("coto")
        if not row or not row.get("agotado"):
            continue
        r = rec.get(it["id"])
        if not r:
            continue
        row.pop("agotado", None); row.pop("revisar", None)
        row["precio"] = int(round(float(r["precio"]))); row["promo"] = r.get("promo")
        if r.get("nombre"): row["producto"] = r["nombre"]
        n += 1
    h = h[:m.start(1)] + json.dumps(DD, ensure_ascii=False) + h[m.end(1):]
    open(path, "w", encoding="utf-8").write(h)
    con = sum(1 for it in DD["items"] if it["precios"].get("coto") and it["precios"]["coto"].get("precio"))
    print(fn, "recuperados:", n, "| coto con precio:", con)
print("siguen gone:", sum(1 for r in res.values() if r.get("gone")), "| errores:", sum(1 for r in res.values() if "err" in r))
