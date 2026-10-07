# -*- coding: utf-8 -*-
"""Revierte matches malos detectados en el QA del 04/09 a la fila previa al refresco."""
import json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
REV = {
    "dia": ["espinaca", "jabon-liquido-bebe"],
    "jumbo": ["banana", "pan-lactal"],
    "coto": ["tapas-tarta", "cerveza", "pollo-entero", "leche-chocolatada", "te-saquitos", "gaseosa-sprite-zero", "cepillo-dientes", "leche-crecimiento"],
}
for st, ids in REV.items():
    p = os.path.join(BASE, f"precios_{st}.json")
    old = {r["id"]: r for r in json.load(open(os.path.join(BASE, f"precios_{st}.pre-refresh-0904.json"), encoding="utf-8"))["items"]}
    data = json.load(open(p, encoding="utf-8"))
    n = 0
    for i, r in enumerate(data["items"]):
        if r["id"] in ids and r["id"] in old:
            data["items"][i] = old[r["id"]]; n += 1
            print(f"  {st}/{r['id']}: vuelve a '{old[r['id']].get('producto','')[:45]}' ${old[r['id']].get('precio')}")
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{st}: {n} revertidos")
