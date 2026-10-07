# -*- coding: utf-8 -*-
"""QA 07/09: revierte matches malos a la fila previa al refresco y anula matches que ya venían mal."""
import json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
# volver a la fila del 04/09 (el refresco trajo otro producto que no corresponde)
REV = {
    "dia": ["espinaca", "jabon-liquido-bebe"],
    "jumbo": ["carne-milanesa", "banana", "pan-lactal", "leche-chocolatada", "vacio-x-kg", "premezcla-exquisita-cookie", "jabon-de-tocador-palmolive"],
    "coto": ["papel-higienico", "pollo-entero", "cepillo-dientes", "leche-crecimiento", "cerveza-patagonia", "cerveza",
             "nescafe-tradicion-doypack-100-grs", "esponja-rollitos-de-acero-carrefour-10-u", "rasuradora-gillette-prestobarba-3-carbon",
             "pants-huggies-soft-comfort-xg-24-uni"],
}
# quitar el precio: el producto matcheado no es el que corresponde (ni antes ni ahora)
NULL = {
    "dia": ["panceta", "brocoli", "premezcla-bizcochuelo", "dulce-membrillo", "protector-solar"],
    "jumbo": ["panceta", "ricota", "cacao-amargo", "lentejas-secas-remojadas-con-sal-inalpa-3"],
    "coto": ["manzana", "aceite-de-coco-neutro-carrefour-classic-", "aceite-en-aerosol-carrefour-classic-120-"],
}
for st in ["dia", "jumbo", "coto"]:
    p = os.path.join(BASE, f"precios_{st}.json")
    old = {r["id"]: r for r in json.load(open(os.path.join(BASE, f"precios_{st}.pre-refresh-0907.json"), encoding="utf-8"))["items"]}
    data = json.load(open(p, encoding="utf-8"))
    n = m = 0
    for i, r in enumerate(data["items"]):
        if r["id"] in REV.get(st, []) and r["id"] in old:
            data["items"][i] = old[r["id"]]; n += 1
            print(f"  {st}/{r['id']}: vuelve a '{old[r['id']].get('producto','')[:45]}' ${old[r['id']].get('precio')}")
        elif any(r["id"].startswith(x) for x in NULL.get(st, [])) and r.get("precio"):
            print(f"  {st}/{r['id']}: sin precio (era '{r.get('producto','')[:45]}' ${r.get('precio')})")
            r["precio"] = None; m += 1
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{st}: {n} revertidos, {m} anulados")
