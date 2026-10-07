# -*- coding: utf-8 -*-
import json, time, io, sys
from concurrent.futures import ThreadPoolExecutor
BASE = "C:/Users/ncort/compra-del-mes"
src = open(BASE + "/tools/refresh_coto.py", encoding="utf-8").read()
exec(src[:src.index("t = time.time()")])  # define D, rows, one(), etc.
res = json.load(open(BASE + "/tools/coto_new.json", encoding="utf-8"))
pend = [(iid, url) for iid, url in rows if "err" in res.get(iid, {"err": 1})]
print("reintentos:", len(pend))
t = time.time()
for ronda in range(3):
    if not pend:
        break
    with ThreadPoolExecutor(2) as ex:
        out = dict(ex.map(one, pend))
    res.update(out)
    pend = [(iid, url) for iid, url in pend if "err" in out.get(iid, {})]
    print(" ronda", ronda + 1, "quedan", len(pend), round(time.time() - t), "s", flush=True)
    time.sleep(5)
json.dump(res, open(BASE + "/tools/coto_new.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("errores finales:", sum(1 for r in res.values() if "err" in r), "| con precio:", sum(1 for r in res.values() if r.get("precio")))
