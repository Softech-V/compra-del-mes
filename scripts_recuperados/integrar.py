# -*- coding: utf-8 -*-
"""Cruza ingredientes + precios de los 5 comercios y genera el JSON final del dashboard."""
import json, math, re, sys, io, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))

def load(name):
    with open(os.path.join(BASE, name), encoding="utf-8") as f:
        return json.load(f)

ing = load("ingredientes.json")
sources = {
    "carrefour": load("precios_carrefour.json"),
    "coto": load("precios_coto.json"),
    "dia": load("precios_dia.json"),
    "jumbo": load("precios_jumbo.json"),
    "ml": load("precios_ml.json"),
}

# need: cantidad mensual en unidades base. kind: bulk = fraccionable (frescos), pack = se compra por unidad entera
NEEDS = {
    "carne-milanesa": {"g": 4000, "kind": "bulk"},
    "bifes":          {"g": 1500, "kind": "bulk"},
    "carne-picada":   {"g": 1000, "kind": "bulk"},
    "carne-sopa":     {"g": 500,  "kind": "bulk"},
    "pechuga":        {"g": 3000, "kind": "bulk"},
    "patitas":        {"g": 800,  "kind": "pack"},
    "jamon":          {"g": 1000, "kind": "bulk"},
    "queso-cremoso":  {"g": 1500, "kind": "bulk"},
    "queso-rallado":  {"g": 500,  "kind": "pack"},
    "leche":          {"ml": 20000, "kind": "pack"},
    "huevos":         {"un": 60,  "kind": "pack"},
    "crema":          {"ml": 800, "kind": "pack"},
    "manteca":        {"g": 400,  "kind": "pack"},
    "papa":           {"g": 6000, "kind": "bulk"},
    "cebolla":        {"g": 1500, "kind": "bulk"},
    "tomate":         {"g": 3000, "kind": "bulk"},
    "lechuga":        {"g": 1000, "kind": "bulk"},
    "palta":          {"g": 1200, "un": 6, "kind": "pack"},
    "zanahoria":      {"g": 1000, "kind": "bulk"},
    "espinaca":       {"g": 1500, "un": 3, "kind": "pack"},
    "brocoli":        {"g": 1200, "un": 2, "kind": "pack"},
    "coliflor":       {"g": 1600, "un": 2, "kind": "pack"},
    "zapallito":      {"g": 1000, "kind": "bulk"},
    "berenjena":      {"g": 1500, "kind": "bulk"},
    "calabaza":       {"g": 2000, "un": 2, "kind": "bulk"},
    "champignones":   {"g": 300,  "kind": "pack"},
    "banana":         {"g": 3000, "kind": "bulk"},
    "manzana":        {"g": 2000, "kind": "bulk"},
    "frutilla":       {"g": 1000, "kind": "bulk"},
    "uvas":           {"g": 1000, "kind": "bulk"},
    "fideos":         {"g": 4000, "kind": "pack"},
    "arroz":          {"g": 2000, "kind": "pack"},
    "arroz-risotto":  {"g": 500,  "kind": "pack"},
    "lentejas":       {"g": 400,  "kind": "pack"},
    "polenta":        {"g": 500,  "kind": "pack"},
    "pure-tomate":    {"g": 3120, "kind": "pack"},
    "pan-rallado":    {"g": 2000, "kind": "pack"},
    "tapas-tarta":    {"un": 8,   "kind": "pack"},
    "tapas-empanadas":{"un": 48,  "kind": "pack"},
    "lasagna":        {"g": 800,  "kind": "pack"},
    "aceite":         {"ml": 4500, "kind": "pack"},
    "avena":          {"g": 500,  "kind": "pack"},
    "choclo-lata":    {"g": 900,  "kind": "pack"},
    "duraznos":       {"g": 1640, "kind": "pack"},
    "pan-lactal":     {"g": 1840, "kind": "pack"},
    "mermelada":      {"g": 780,  "kind": "pack"},
    "nesquik":        {"g": 360,  "kind": "pack"},
    "cafe":           {"g": 500,  "kind": "pack"},
    "galletitas":     {"g": 1200, "kind": "pack"},
    "rapiditas":      {"un": 20,  "kind": "pack"},
}

def parse_size(pres, prefer):
    """Devuelve (cantidad, unidad_base) a partir del texto de presentación."""
    if not pres:
        return None
    p = pres.lower()
    def mass():
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*kg", p)
        if m: return float(m.group(1).replace(",", ".")) * 1000, "g"
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:g|gr|grs)\b", p)
        if m: return float(m.group(1).replace(",", ".")), "g"
        if "por kg" in p or "x kg" in p: return 1000.0, "g"
        return None
    def vol():
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:l|lt|lts|litros?)\b", p)
        if m: return float(m.group(1).replace(",", ".")) * 1000, "ml"
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:ml|cc)\b", p)
        if m: return float(m.group(1).replace(",", ".")), "ml"
        return None
    def units():
        if "media docena" in p: return 6.0, "un"
        if "docena" in p: return 12.0, "un"
        m = re.search(r"x\s?(\d+)\b", p)
        if m: return float(m.group(1)), "un"
        m = re.search(r"(\d+)\s*(?:un|u|uni|ud|unidades)\b", p)
        if m: return float(m.group(1)), "un"
        if "unidad" in p or "atado" in p: return 1.0, "un"
        return None
    order = {"g": [mass, units, vol], "ml": [vol, mass, units], "un": [units, mass, vol]}[prefer]
    for fn in order:
        r = fn()
        if r: return r
    return None

STORES = [
    {"key": "carrefour", "label": "Carrefour", "short": "Carrefour"},
    {"key": "coto", "label": "Coto", "short": "Coto"},
    {"key": "dia", "label": "Día", "short": "Día"},
    {"key": "jumbo", "label": "Jumbo / Vea / Disco", "short": "Jumbo"},
    {"key": "ml", "label": "Mercado Libre", "short": "M. Libre"},
]

by_store = {}
for key, src in sources.items():
    by_store[key] = {it["id"]: it for it in src["items"]}

items_out, warnings = [], []
for cat in ing["categorias"]:
    for it in cat["items"]:
        iid = it["id"]
        need = NEEDS.get(iid)
        if not need:
            warnings.append(f"SIN NEED: {iid}")
            continue
        precios = {}
        for st in STORES:
            row = by_store[st["key"]].get(iid)
            if not row or row.get("precio") is None:
                precios[st["key"]] = None
                continue
            price = float(row["precio"])
            pres = row.get("presentacion") or ""
            # unidad preferida: la primera que exista en need
            prefer = "g" if "g" in need else ("ml" if "ml" in need else "un")
            size = parse_size(pres, prefer)
            mes = None
            if size:
                qty, unit = size
                target = need.get(unit)
                if target is None and unit == "un" and "un" in need:
                    target = need["un"]
                if target is not None and qty > 0:
                    if need["kind"] == "bulk":
                        mes = price / qty * target
                    else:
                        mes = math.ceil(target / qty - 1e-9) * price
            if mes is None:
                warnings.append(f"NO PARSE [{st['key']}] {iid}: '{pres}' -> uso precio x1")
                mes = price
            precios[st["key"]] = {
                "producto": row["producto"].replace("&amp;", "&"),
                "presentacion": pres.replace("&amp;", "&"),
                "precio": round(price),
                "mes": round(mes),
                "url": row.get("url"),
            }
        items_out.append({
            "id": iid,
            "nombre": it["nombre"],
            "cat": cat["nombre"],
            "cantidad": it["cantidad_mes"],
            "precios": precios,
        })

data = {"fecha": "24/08/2026", "stores": STORES, "items": items_out}
out_path = os.path.join(BASE, "data_final.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

print(f"{len(items_out)} items integrados")
for w in warnings:
    print("AVISO:", w)

# resumen de control
for st in STORES:
    tot = sum(i["precios"][st["key"]]["mes"] for i in items_out if i["precios"][st["key"]])
    n = sum(1 for i in items_out if i["precios"][st["key"]])
    print(f"{st['label']}: {n} items, total mes ${tot:,.0f}")
mix = sum(min(p["mes"] for p in i["precios"].values() if p) for i in items_out if any(i["precios"].values()))
print(f"Mix más barato: ${mix:,.0f}")

# inyectar en el HTML
html_path = os.path.join(BASE, "compra-del-mes.html")
with open(html_path, encoding="utf-8") as f:
    html = f.read()
marker = "const GROCERY_DATA = null; /* __DATA__ */"
payload = "const GROCERY_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";"
if marker in html:
    html = html.replace(marker, payload)
elif "const GROCERY_DATA = " in html:
    html = re.sub(r"const GROCERY_DATA = .*?;\n", payload + "\n", html, count=1, flags=re.S)
else:
    raise SystemExit("marcador no encontrado en el HTML")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print("HTML actualizado")
