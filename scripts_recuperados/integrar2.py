# -*- coding: utf-8 -*-
"""v2: genera data_v2 para el planificador (platos + productos + envíos + descuentos)."""
import json, math, re, sys, io, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))

def load(name, default=None):
    path = os.path.join(BASE, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)

ing = load("ingredientes.json")
platos = load("platos.json")
envios = load("envios.json", {"envios": {}})
descuentos = load("descuentos.json", {"descuentos": []})
sources = {k: load(f"precios_{k}.json") for k in ["carrefour", "coto", "dia", "jumbo", "ml"]}

FECHA = "25/08/2026"

# need: unidad primaria = primera clave g/ml/un. kind bulk = fraccionable.
NEEDS = {
    "carne-milanesa": {"g": 4000, "kind": "bulk"}, "bifes": {"g": 1500, "kind": "bulk"},
    "carne-picada": {"g": 1000, "kind": "bulk"}, "carne-sopa": {"g": 500, "kind": "bulk"},
    "pechuga": {"g": 3000, "kind": "bulk"}, "patitas": {"g": 800, "kind": "pack"},
    "jamon": {"g": 1000, "kind": "bulk"}, "queso-cremoso": {"g": 1500, "kind": "bulk"},
    "queso-rallado": {"g": 500, "kind": "pack"}, "leche": {"ml": 20000, "kind": "pack"},
    "huevos": {"un": 60, "kind": "pack"}, "crema": {"ml": 800, "kind": "pack"},
    "manteca": {"g": 400, "kind": "pack"}, "papa": {"g": 6000, "kind": "bulk"},
    "cebolla": {"g": 1500, "kind": "bulk"}, "tomate": {"g": 3000, "kind": "bulk"},
    "lechuga": {"g": 1000, "kind": "bulk"}, "palta": {"g": 1200, "un": 6, "kind": "pack"},
    "zanahoria": {"g": 1000, "kind": "bulk"}, "espinaca": {"g": 1500, "un": 3, "kind": "pack"},
    "brocoli": {"g": 1200, "un": 2, "kind": "pack"}, "coliflor": {"g": 1600, "un": 2, "kind": "pack"},
    "zapallito": {"g": 1000, "kind": "bulk"}, "berenjena": {"g": 1500, "kind": "bulk"},
    "calabaza": {"g": 2000, "un": 2, "kind": "bulk"}, "champignones": {"g": 300, "kind": "pack"},
    "banana": {"g": 3000, "kind": "bulk"}, "manzana": {"g": 2000, "kind": "bulk"},
    "frutilla": {"g": 1000, "kind": "bulk"}, "uvas": {"g": 1000, "kind": "bulk"},
    "fideos": {"g": 4000, "kind": "pack"}, "arroz": {"g": 2000, "kind": "pack"},
    "arroz-risotto": {"g": 500, "kind": "pack"}, "lentejas": {"g": 400, "kind": "pack"},
    "polenta": {"g": 500, "kind": "pack"}, "pure-tomate": {"g": 3120, "kind": "pack"},
    "pan-rallado": {"g": 2000, "kind": "pack"}, "tapas-tarta": {"un": 8, "kind": "pack"},
    "tapas-empanadas": {"un": 48, "kind": "pack"}, "lasagna": {"g": 800, "kind": "pack"},
    "aceite": {"ml": 4500, "kind": "pack"}, "aceite-oliva": {"ml": 500, "kind": "pack"},
    "avena": {"g": 500, "kind": "pack"}, "choclo-lata": {"g": 900, "kind": "pack"},
    "duraznos": {"g": 1640, "kind": "pack"}, "pan-lactal": {"g": 1840, "kind": "pack"},
    "mermelada": {"g": 780, "kind": "pack"}, "nesquik": {"g": 360, "kind": "pack"},
    "cafe": {"g": 500, "kind": "pack"}, "galletitas": {"g": 1200, "kind": "pack"},
    "rapiditas": {"un": 20, "kind": "pack"},
    "ariel": {"ml": 6000, "kind": "pack"}, "suavizante": {"ml": 6000, "kind": "pack"},
    "cif": {"g": 500, "ml": 500, "kind": "pack"}, "yerba": {"g": 2000, "kind": "pack"},
    "papel-higienico": {"un": 16, "kind": "pack"}, "rollo-cocina": {"un": 360, "kind": "pack"},
}
# equivalencia un -> unidad primaria (para tiendas que venden por unidad/atado)
EQUIV_UN = {"palta": 200, "espinaca": 500, "brocoli": 600, "coliflor": 800, "calabaza": 1000}

# productos "sueltos" con stepper propio: base = cuánto de la unidad primaria representa 1 paso
STANDALONE = {
    "ariel": {"paso": "botella 3L", "base": 3000, "def": 2},
    "suavizante": {"paso": "botella 3L", "base": 3000, "def": 2},
    "cif": {"paso": "unidad (~500g)", "base": 500, "def": 1},
    "yerba": {"paso": "paquete 500g", "base": 500, "def": 4},
    "papel-higienico": {"paso": "pack x4", "base": 4, "def": 4},
    "rollo-cocina": {"paso": "rollo (~60 paños)", "base": 60, "def": 6},
    "aceite-oliva": {"paso": "botella 500ml", "base": 500, "def": 1},
}
PLATO_DEF = {"mila-carne": 4, "mila-pollo": 3, "bifes": 2, "tarta-espinaca": 1, "tarta-jyq": 1,
    "tarta-choclo": 1, "empanadas-jyq": 3, "fideos-brocoli": 2, "fideos-salsa": 2, "fideos-lentejas": 1,
    "pollo-crema": 1, "ensalada-pollo": 2, "lasagna": 1, "risotto": 1, "patitas": 2, "pastel-papas": 1,
    "mila-berenjena": 1, "polenta": 1, "sopa": 2, "pechuga-pure": 1, "revuelto": 1, "arroz-huevo": 1,
    "quesadillas": 1, "desayunos": 4}

def parse_size(pres, prefer):
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
        m = re.search(r"(\d+)\s*pa[ñn]os", p)
        if m: return float(m.group(1)), "un"
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
by_store = {k: {it["id"]: it for it in v["items"]} for k, v in sources.items()}

items_out, warnings = [], []
for cat in ing["categorias"]:
    for it in cat["items"]:
        iid = it["id"]
        need = NEEDS.get(iid)
        if not need:
            warnings.append(f"SIN NEED: {iid}")
            continue
        prefer = "g" if "g" in need else ("ml" if "ml" in need else "un")
        base_need = need[prefer]
        precios = {}
        for st in STORES:
            row = by_store[st["key"]].get(iid)
            if not row or row.get("precio") is None:
                precios[st["key"]] = None
                continue
            price = round(float(row["precio"]))
            pres = row.get("presentacion") or ""
            size = parse_size(pres, prefer)
            size_base = None
            if size:
                qty, unit = size
                if unit == prefer:
                    size_base = qty
                elif {unit, prefer} == {"g", "ml"} and iid in ("cif",):
                    size_base = qty  # crema: 1 g ~ 1 ml
                elif unit == "un" and prefer in ("g", "ml"):
                    eq = EQUIV_UN.get(iid)
                    if eq: size_base = qty * eq
                    elif "un" in need and need["un"]:
                        size_base = qty * (base_need / need["un"])
                elif unit in ("g", "ml") and prefer == "un" and "un" not in need:
                    pass
            if size_base is None:
                warnings.append(f"NO PARSE [{st['key']}] {iid}: '{pres}' -> asumo 1 envase = necesidad base")
                size_base = base_need
            precios[st["key"]] = {
                "producto": row["producto"].replace("&amp;", "&") if row.get("producto") else "",
                "presentacion": pres.replace("&amp;", "&"),
                "precio": price,
                "promo": row.get("promo"),
                "size": round(size_base, 2),
                "url": row.get("url"),
            }
        entry = {
            "id": iid, "nombre": it["nombre"], "cat": cat["nombre"], "cantidad": it["cantidad_mes"],
            "need": base_need, "unit": prefer, "kind": need["kind"], "precios": precios,
        }
        if iid in STANDALONE:
            entry["standalone"] = STANDALONE[iid]
        items_out.append(entry)

platos_out = []
for p in platos["platos"]:
    platos_out.append({
        "id": p["id"], "nombre": p["nombre"], "emoji": p.get("emoji", ""),
        "def": PLATO_DEF.get(p["id"], 1),
        "ing": [[i, q] for i, q in p["ing"] if q > 0],
    })

data = {
    "fecha": FECHA,
    "stores": STORES,
    "items": items_out,
    "platos": platos_out,
    "envios": envios.get("envios", {}),
    "descuentos": descuentos.get("descuentos", []),
}
with open(os.path.join(BASE, "data_v2.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

print(f"{len(items_out)} items, {len(platos_out)} platos, {len(data['descuentos'])} descuentos, envíos: {list(data['envios'].keys())}")
for w in warnings:
    print("AVISO:", w)

# validación: costo del plan por defecto por comercio
def cost(itemid, qty):
    it = next(i for i in items_out if i["id"] == itemid)
    out = {}
    for st in STORES:
        p = it["precios"][st["key"]]
        if not p: out[st["key"]] = None; continue
        if it["kind"] == "bulk":
            out[st["key"]] = p["precio"] / p["size"] * qty
        else:
            out[st["key"]] = math.ceil(qty / p["size"] - 1e-9) * p["precio"]
    return out

demanda = {}
for p in platos_out:
    for iid, q in p["ing"]:
        demanda[iid] = demanda.get(iid, 0) + q * p["def"]
for iid, sa in STANDALONE.items():
    demanda[iid] = demanda.get(iid, 0) + sa["base"] * sa["def"]

tot = {st["key"]: 0 for st in STORES}
mix = 0
for iid, q in demanda.items():
    c = cost(iid, q)
    vals = [v for v in c.values() if v is not None]
    if vals: mix += min(vals)
    for k, v in c.items():
        if v is not None: tot[k] += v
print("Plan por defecto — mix más barato:", round(mix))
for st in STORES:
    print(f"  {st['label']}: ${tot[st['key']]:,.0f}")

# inyectar en el HTML v2
html_path = os.path.join(BASE, "compra-del-mes.html")
with open(html_path, encoding="utf-8") as f:
    html = f.read()
payload = "const GROCERY_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";"
html, n = re.subn(r"const GROCERY_DATA = .*?;\n", payload + "\n", html, count=1, flags=re.S)
if n == 0:
    raise SystemExit("marcador GROCERY_DATA no encontrado")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print("HTML actualizado")
