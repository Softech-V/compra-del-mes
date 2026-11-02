# -*- coding: utf-8 -*-
"""Cruza las compras reales (compras_1110.json) con el catálogo publicado: ¿había mejor precio en otro súper?"""
import re, json, io, sys, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "C:/Users/ncort/compra-del-mes"
h = open(BASE + "/deploy/index.html", encoding="utf-8").read()
D = json.loads(re.search(r"const GROCERY_DATA = (\{.*?\});\s*\n", h, re.S).group(1))
C = json.load(open(BASE + "/tools/compras_1110.json", encoding="utf-8"))
STORES = ["carrefour", "coto", "dia", "jumbo", "ml"]
LABEL = {"carrefour": "Carrefour", "coto": "Coto", "dia": "Día", "jumbo": "Jumbo", "ml": "Mercado Libre"}

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s)

STOP = {"de", "la", "el", "en", "con", "para", "x", "un", "por", "y", "lata", "paq", "pack"}
def toks(s):
    return [t for t in norm(s).split() if t not in STOP and len(t) > 1]

def row_size(row, unit):
    """tamaño del envase en g/ml (o unidades): primero el texto, después el campo size si es coherente"""
    txt = norm(row.get("presentacion", "") + " " + row.get("producto", ""))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(kg|g|gr|grs|ml|cc|l|lt|lts)", txt)
    if m:
        v = float(m.group(1).replace(",", "."))
        u = m.group(2)
        if u in ("kg", "l", "lt", "lts"):
            v *= 1000
        if unit in ("g", "ml") and v >= 10:
            return v
    if re.search(r"(x|por)\s*(kg|kilo)", txt) and unit in ("g", "ml"):
        return 1000.0
    sz = row.get("size")
    if sz and sz > 0:
        if unit in ("g", "ml") and sz >= 10:
            return sz
        if unit not in ("g", "ml"):
            return sz
    return None

def per_base(row, unit):
    sz = row_size(row, unit)
    if not sz or not row.get("precio"):
        return None
    return row["precio"] / sz

def generic_type_tokens(tipo):
    # tokens del tipo, sin marca
    return [t for t in toks(tipo)]

rows = []  # (store, item, row)
for it in D["items"]:
    for st in STORES:
        r = it["precios"].get(st)
        if r and r.get("precio"):
            rows.append((st, it, r))

def find_same_brand(p):
    """filas de cualquier súper con la misma marca y tipo"""
    b = toks(p["marca"])
    tt = generic_type_tokens(p["tipo"])
    out = []
    for st, it, r in rows:
        name = norm(r["producto"] + " " + it["nombre"])
        if b and not all(x in name for x in b):
            continue
        if not all(any(x.startswith(t[:5]) for x in name.split()) for t in tt[:2]):
            continue
        out.append((st, it, r))
    return out

def find_same_type(p):
    tt = generic_type_tokens(p["tipo"])
    out = []
    for st, it, r in rows:
        name = norm(r["producto"] + " " + it["nombre"])
        if all(any(x.startswith(t[:5]) for x in name.split()) for t in tt):
            out.append((st, it, r))
    return out

for store in ["dia", "coto", "ml"]:
    print("=" * 90)
    print(f"COMPRA EN {LABEL[store].upper()}")
    tot_cat = 0
    tot_cat_sin_jamon = 0
    for p in C[store]["items"]:
        qty = p["qty"]
        same = find_same_brand(p)
        own = [x for x in same if x[0] == store]
        # mismo producto en el súper donde compró (precio catálogo 07/10)
        own_txt = ""
        if own:
            st, it, r = min(own, key=lambda x: abs((row_size(x[2], p["unit"]) or 0) - p["size"]))
            own_txt = f"catálogo {LABEL[store]}: {r['producto'][:45]} ${r['precio']:,}".replace(",", ".")
            if store == "coto":
                tot_cat += r["precio"] * qty
                if not p.get("fuera_del_resumen"):
                    tot_cat_sin_jamon += r["precio"] * qty
        # mejor por unidad de medida, misma marca, otros súper
        best = []
        for st, it, r in same:
            pb = per_base(r, p["unit"])
            rs = row_size(r, p["unit"])
            if pb and rs and 0.6 <= rs / p["size"] <= 1.7:
                best.append((pb * p["size"], st, r))
        best.sort(key=lambda x: x[0])
        alt = [x for x in best if x[1] != store][:2]
        pag = p.get("pagado")
        print(f"\n- {p['nombre']}  x{qty}" + (f"  (pagaste ${pag:,.0f} c/u)".replace(",", ".") if pag else ""))
        if own_txt:
            print("   ", own_txt)
        else:
            print("    (no está en el catálogo para", LABEL[store] + ")")
        if alt:
            for v, st, r in alt:
                print(f"    misma marca en {LABEL[st]}: {r['producto'][:50]} ≈ ${v:,.0f} por {p['size']} {p['unit']}".replace(",", "."))
        else:
            # buscar mismo tipo cualquier marca, más barato
            gen = []
            for st, it, r in find_same_type(p):
                pb = per_base(r, p["unit"])
                rs = row_size(r, p["unit"])
                if pb and rs and st != store and 0.5 <= rs / p["size"] <= 2:
                    gen.append((pb * p["size"], st, r))
            gen.sort(key=lambda x: x[0])
            for v, st, r in gen[:2]:
                print(f"    otra marca en {LABEL[st]}: {r['producto'][:50]} ≈ ${v:,.0f} por {p['size']} {p['unit']}".replace(",", "."))
    if store == "coto":
        print(f"\nSuma catálogo Coto de los productos encontrados: ${tot_cat:,.0f} (sin jamón ${tot_cat_sin_jamon:,.0f}); ticket subtotal $240.950".replace(",", "."))
