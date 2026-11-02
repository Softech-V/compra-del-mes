# -*- coding: utf-8 -*-
"""Imprime las acciones de browser_batch para leer las fichas ML de los índices a..b (inclusive) de ml_todo_<TAG>.json.
Si la ficha (misma URL) ya fue leída en ml_new_<TAG>.jsonl, copia el resultado y la saltea."""
import json, sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
TAG = os.environ.get("ML_TAG", "1110")
a, b, tab = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
BASE = "C:/Users/ncort/compra-del-mes/tools/"
todo = json.load(open(BASE + "ml_todo_" + TAG + ".json", encoding="utf-8"))
JS = ("const t=document.body.innerText;const q=s=>(document.querySelector(s)||{}).innerText||null;"
      "({id:'%s',url:location.href,producto:q('h1.ui-pdp-title'),precio:q('.ui-pdp-price__second-line .andes-money-amount__fraction'),"
      "antes:q('.ui-pdp-price__original-value .andes-money-amount__fraction'),"
      "agotado:/no está disponible por el momento|Publicación pausada|publicación finalizada/i.test(t),captcha:/captcha/i.test(t),"
      "wall:/account-verification|\\/login|registration/.test(location.href)||/ingresá a tu cuenta/i.test(t)})")

def key(url):
    return re.sub(r"https://www\.mercadolibre\.com\.ar/.*?/(p|up)/", r"https://www.mercadolibre.com.ar/\1/", url.split("?")[0])

done_path = BASE + "ml_new_" + TAG + ".jsonl"
done = {}
if os.path.exists(done_path):
    for l in open(done_path, encoding="utf-8"):
        if l.strip():
            d = json.loads(l)
            done[key(d["url"])] = d
acts, skipped = [], []
for i in range(a, b + 1):
    r = todo[i]
    k = key(r["url"])
    if k in done:
        d = dict(done[k]); d["id"] = r["id"]
        with open(done_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
        skipped.append(r["id"])
        continue
    acts.append({"name": "navigate", "input": {"tabId": tab, "url": r["url"]}})
    acts.append({"name": "computer", "input": {"tabId": tab, "action": "wait", "duration": 10}})
    acts.append({"name": "computer", "input": {"tabId": tab, "action": "wait", "duration": 8 if i % 2 == 0 else 9}})
    acts.append({"name": "javascript_tool", "input": {"tabId": tab, "action": "javascript_exec", "text": JS % r["id"]}})
print(json.dumps(acts, ensure_ascii=False))
print("SKIPPED (copiados de una ficha ya leída):", skipped)
