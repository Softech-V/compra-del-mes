# -*- coding: utf-8 -*-
import json, io, sys, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
ids = ["palta", "panceta", "pan-lactal", "nesquik", "azucar-rubio", "huevos"]
for st in ["carrefour", "coto", "dia", "jumbo", "ml"]:
    d = json.load(open(os.path.join(BASE, f"precios_{st}.json"), encoding="utf-8"))
    have = {i["id"] for i in d["items"]}
    print(st, {i: (i in have) for i in ids})
src = open(os.path.join(BASE, "integrar2.py"), encoding="utf-8").read()
m = re.search(r"PLATO_GRUPOS\s*=\s*\[(.*?)\];", src, re.S)
print("---grupos---")
print(m.group(1)[:1500] if m else "no PLATO_GRUPOS en integrar2")
print("---needs---")
for k in ['"pan-lactal"', '"panceta"', '"palta"', '"nesquik"', '"azucar-rubio"', '"galletitas-chocolinas"']:
    i = src.find(k)
    print(k, src[i:i+90].replace("\n", " ") if i >= 0 else "NO encontrado")
