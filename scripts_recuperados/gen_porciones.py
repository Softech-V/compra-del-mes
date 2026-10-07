# -*- coding: utf-8 -*-
"""Genera el desglose de porciones por adulto y por niño para cada plato."""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))

P = json.load(open(os.path.join(BASE, "platos.json"), encoding="utf-8"))
ING = json.load(open(os.path.join(BASE, "ingredientes.json"), encoding="utf-8"))
NOMBRE = {}
UNIDAD = {}
for c in ING["categorias"]:
    for i in c["items"]:
        NOMBRE[i["id"]] = i["nombre"]

# unidad por item: inferir de integrar2 NEEDS no disponible aquí; heurística por id
UN_ITEMS = {"huevos", "tapas-tarta", "tapas-empanada", "palta", "banana", "limon", "pan-hamburguesa", "prepizza"}

def unidad_de(iid, qty):
    if iid in UN_ITEMS or (qty <= 12 and qty == int(qty) and iid not in ("arroz",)):
        # cantidades chicas enteras suelen ser unidades
        if iid in UN_ITEMS:
            return "un"
    return "g/ml"

def fmt_g(x):
    # redondeo a 5 g
    r = round(x / 5) * 5
    if r >= 1000:
        return f"{r/1000:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " kg"
    return f"{int(r)} g"

def fmt_un(x):
    if abs(x - round(x)) < 0.05:
        return str(int(round(x)))
    return f"{x:.1f}".replace(".", ",")

SKIP = {"desayunos"}  # plato de desayunos/meriendas, no es plato principal

for p in P["platos"]:
    if p["id"] in SKIP:
        continue
    print(f'{p.get("emoji","")} **{p["nombre"]}**  _(total olla: para 2 grandes + 2 chicos)_')
    for iid, q in p["ing"]:
        nom = NOMBRE.get(iid, iid)
        if iid in UN_ITEMS:
            print(f'- {nom}: {fmt_un(q)} un → **{fmt_un(q/3)}** por adulto · **{fmt_un(q/6)}** por niño')
        else:
            print(f'- {nom}: {fmt_g(q)} → **{fmt_g(q/3)}** por adulto · **{fmt_g(q/6)}** por niño')
    print()
