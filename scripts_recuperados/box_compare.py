# -*- coding: utf-8 -*-
"""Compara cada Box Molinos contra comprar sus componentes sueltos (mejor súper del catálogo, y Molinos por unidad)."""
import json, re, io, sys, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
h = open("compra-del-mes.html", encoding="utf-8").read()
D = json.loads(re.search(r"const GROCERY_DATA = (\{.*?\});\s*\n", h, re.S).group(1))
items = D["items"]
def norm(s): return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
def find(q):
    toks = norm(q).split()
    c = [it for it in items if all(t in norm(it["nombre"]) for t in toks)]
    return c[0] if c else None
def per_measure(it, exclude=("molinos",)):
    """mejor precio por g/ml (o por envase) entre las tiendas, y el precio Molinos por unidad."""
    best = None; mol = None
    for k, p in it["precios"].items():
        if not p or not p.get("precio"): continue
        if it["unit"] in ("g", "ml"):
            v = p["precio"] / p["size"]
        else:
            v = p["precio"]
        if k == "molinos": mol = v
        elif best is None or v < best: best = v
    return best, mol
BOXES = {
    "Llená tu Alacena ($19.436)": [("arroz parboil", 2, 500), ("fideos tirabuzón", 1, 500), ("fideos coditos", 1, 500), ("fideos coditos", 1, 500), ("tallarines", 2, 500), ("harina 0000", 1, 900), ("aceite de girasol", 1, 900), ("yerba", 2, 500)],
    "Fanáticos de Lucchetti ($15.204)": [("arroz largo fino", 1, 500), ("fideos coditos", 1, 500), ("fideos coditos", 1, 500), ("fideos coditos", 1, 500), ("tallarines", 1, 500), ("premezcla pizza lucchetti", 1, 850), ("premezcla pizza lucchetti", 1, 850), ("pan rallado", 1, 1000)],
    "Especialidades ($23.108)": [("aceite de oliva", 1, 500), ("fideos tirabuzón", 2, 500), ("tallarines", 2, 500), ("risotto champi", 1, 240), ("risotto champi", 1, 240), ("yerba", 1, 500)],
    "Condimentá tu Mesa ($27.297)": [("aceite de oliva", 2, 250), ("aceto", 1, 500), ("aceto", 1, 250), ("salsa de soja", 1, 500), ("aceite en aerosol", 1, 120), ("jugo de limón", 1, 500), ("aceite de girasol", 1, 900)],
    "Libre de Gluten ($20.984)": [("arroz parboil", 1, 500), ("risotto champi", 1, 240), ("risotto champi", 1, 240), ("arroz preparado gallo", 1, 240), ("fideos tirabuzón", 2, 500), ("alfajor", 1, 6), ("galletitas", 1, 100)],
    "Merendar ($17.991)": [("cookies", 1, 300), ("brownies", 1, 425), ("café instantáneo", 1, 100), ("bizcochos", 1, 100), ("bizcochos", 1, 100), ("pochoclo", 1, 50)],
}
for box, comps in BOXES.items():
    sup = mol = 0; miss = []; molmiss = []
    for q, n, size in comps:
        it = find(q)
        if not it: miss.append(q); continue
        best, m = per_measure(it)
        if it["unit"] in ("g", "ml"):
            if best: sup += best * size * n
            if m: mol += m * size * n
            else: molmiss.append(q)
        else:
            if best: sup += best * n
            if m: mol += m * n
            else: molmiss.append(q)
        if not best: miss.append(q)
    print(f"{box}: comprando suelto en el súper más barato ≈ ${sup:,.0f}" + (f" (sin precio para: {', '.join(miss)})" if miss else "") + f" | a precio unitario Molinos ≈ ${mol:,.0f}" + (f" (Molinos no vende suelto: {', '.join(sorted(set(molmiss)))})" if molmiss else ""))
