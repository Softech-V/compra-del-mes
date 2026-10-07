# -*- coding: utf-8 -*-
"""Aplica refresh_raw.json (Carrefour/Día/Jumbo) + refresh_coto.json sobre precios_*.json.
Mantiene la fila vieja si el relevo nuevo no encontró el producto. No toca Mercado Libre."""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))

def load(name, default=None):
    p = os.path.join(BASE, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)

raw = load("refresh_raw.json", {})
coto = (load("refresh_coto.json", {}) or {}).get("coto", {})
fuentes = {"carrefour": raw.get("carrefour", {}), "dia": raw.get("dia", {}),
           "jumbo": raw.get("jumbo", {}), "coto": coto}
files = {"carrefour": "precios_carrefour.json", "dia": "precios_dia.json",
         "jumbo": "precios_jumbo.json", "coto": "precios_coto.json"}

cambios_grandes = []
for skey, fname in files.items():
    nuevos = fuentes.get(skey) or {}
    path = os.path.join(BASE, fname)
    data = load(fname)
    viejos = {i["id"]: i for i in data["items"]}
    reemplazados = agregados = mantenidos = 0
    for iid, row in nuevos.items():
        if not row or row.get("precio") in (None, 0):
            continue
        nuevo = {"id": iid, "producto": row.get("producto", ""), "presentacion": row.get("presentacion", "unidad"),
                 "precio": round(float(row["precio"])), "promo": row.get("promo"), "url": row.get("url")}
        if iid in viejos and viejos[iid].get("precio"):
            va = viejos[iid]["precio"]
            if va and abs(nuevo["precio"] - va) / va > 0.4:
                cambios_grandes.append(f"{skey}/{iid}: ${va:,} -> ${nuevo['precio']:,} ({row.get('producto','')[:50]})")
            reemplazados += 1
        else:
            agregados += 1
        viejos[iid] = nuevo
    mantenidos = sum(1 for i in viejos.values() if i["id"] not in nuevos and i.get("precio"))
    data["items"] = list(viejos.values())
    data["fecha"] = "27/08/2026"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"{skey}: {reemplazados} actualizados, {agregados} nuevos con precio, {mantenidos} mantenidos del relevo anterior")

print("\n--- CAMBIOS >40% (revisar posibles matches malos) ---")
for c in cambios_grandes:
    print(" ", c)
print(f"total sospechosos: {len(cambios_grandes)}")
