# -*- coding: utf-8 -*-
"""Cruza el catálogo de Tienda Molinos (molinos_raw.tsv, precio unitario con descuento, venta por caja)
con los items del catálogo y escribe precios_molinos.json.
Regla: 1) items cuyo nombre contiene marca + tipo del producto Molinos (base amplia);
       2) mapa manual para los items genéricos viejos (fideos-salsa, arroz, aceite-oliva...)."""
import csv, json, re, io, sys, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s)

rows = list(csv.DictReader(open("molinos_raw.tsv", encoding="utf-8"), delimiter="\t"))
rows = [r for r in rows if r["stock"] != "outOfStock" and not r["name"].startswith("Caja Mix")]
ing = json.load(open("ingredientes.json", encoding="utf-8"))
items = [(c["nombre"], i) for c in ing["categorias"] for i in c["items"]]

# tipo de producto (token obligatorio) y tamaño por producto Molinos, derivados del título
def parse(r):
    t = norm(r["titles"]); n = norm(r["name"])
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(ml|g|gr|grs|kg|u)\b", t) or re.search(r"x(\d+)\s*(ml|g|gr|grs|kg|u)\b", n)
    size = None
    if m:
        v = float(m.group(1).replace(",", ".")); u = m.group(2)
        size = (v * 1000 if u == "kg" else v, "ml" if u == "ml" else ("un" if u == "u" else "g"))
    brand = norm(r["titles"].split(" / ")[0])
    return brand, size

def size_txt(size):
    if not size: return ""
    v, u = size
    if u == "g" and v >= 1000: return f"{v/1000:g} kg"
    if u == "ml" and v >= 1000: return f"{v/1000:g} L"
    return f"{v:g} {u}"

# tokens que definen el tipo (el nombre del item debe contener marca y alguno de estos)
TYPE = {
    "tallarin": ["tallarin"], "mostachol": ["mostachol"], "tirabuzon": ["tirabuzon"], "spaghetti": ["spaghetti", "espagueti"],
    "fettuccine": ["fettuccine", "fettuccini", "fetuccini"], "casereccia": ["casereccia"], "rigatti": ["rigatti"], "penne": ["penne"],
    "fusilli": ["fusilli"], "linguine": ["linguine"], "conchiglioni": ["conchiglioni"], "lasagna": ["lasagna", "lasana"],
    "arroz doble": ["arroz doble", "doble carolina"], "arroz integral": ["arroz integral"], "risotto": ["risotto"], "arroz preparado": ["arroz preparado"],
    "quinoa": ["quinoa"], "aceite de oliva": ["aceite de oliva", "oliva"], "girasol": ["girasol"], "fritolim": ["fritolim", "aerosol"],
    "aceto": ["aceto"], "jugo de limon": ["jugo de limon"], "salsa lista": ["salsa", "filetto", "pomarola"], "passata": ["passata"],
    "pan rallado": ["pan rallado"], "rebozador": ["rebozador"], "premezcla": ["premezcla", "chipa", "pizza", "torta frita"],
    "bizcochuelo": ["bizcochuelo"], "brownies": ["brownie"], "cookies": ["cookie"], "chocolatada": ["chocolatad", "polvo chocolatado"],
    "mate cocido": ["mate cocido"], "yerba": ["yerba", "cruz de malta", "nobleza gaucha"], "oblea": ["oblea"], "yogubar": ["yogubar"], "alfajor": ["alfajor", "chocoarroz"],
}
def tipo(r):
    t = norm(r["titles"]); n = norm(r["name"])
    for k, toks in TYPE.items():
        if any(x in t or x in n for x in toks): return k
    return None

# mapa manual: item genérico -> producto Molinos (por code)
MANUAL = {
    "fideos-salsa": "33631", "fideos-bolognesa": "33631", "fideos-tirabuzon": "33812", "fideos-brocoli": "33812",
    "arroz": "43143", "arroz-risotto": "43143", "arroz-integral": "43315", "aceite-oliva": "23183", "pan-rallado": "43316",
    "rebozador": "43319", "premezcla-bizcochuelo": "43296", "lasagna": "10032", "mate-cocido": "50880", "salsa-lista": "33532",
    "pure-tomate": "10031", "aceite-aerosol": "26533", "aceto": "22803", "jugo-limon": "50734",
}
bycode = {r["code"]: r for r in rows}
out = []; used = {}
def add(iid, r, why):
    brand, size = parse(r)
    st = size_txt(size)
    out.append({
        "id": iid, "producto": r["titles"].replace(" / ", " ") if r["titles"] else r["name"],
        "presentacion": (st + " " if st else "") + f"(caja x{r['units']})",
        "precio": round(float(r["price"])), "promo": f"-{round((1-float(r['price'])/float(r['prev']))*100)}% caja x{r['units']}" if r.get("prev") else None,
        "url": "https://www.tiendamolinos.com" + r["url"], "caja": int(float(r["units"])),
    })
    used.setdefault(r["code"], []).append((iid, why))

seen = set()
for cat, it in items:
    iid = it["id"]
    if iid in MANUAL and MANUAL[iid] in bycode:
        add(iid, bycode[MANUAL[iid]], "manual"); seen.add(iid); continue
    nm = norm(it["nombre"])
    best = None
    for r in rows:
        brand, size = parse(r)
        b = brand.split()[0] if brand else ""
        if not b or b not in nm: continue
        k = tipo(r)
        if not k or not any(x in nm for x in TYPE[k]): continue
        # tamaño: si ambos tienen número, debe coincidir
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(ml|g|gr|grs|kg|l)\b", nm)
        if m and size:
            v = float(m.group(1).replace(",", ".")); u = m.group(2)
            v = v * 1000 if u in ("kg", "l") else v
            if abs(v - size[0]) > 1: continue
        best = r; break
    if best: add(iid, best, "nombre"); seen.add(iid)

json.dump({"fecha": "07/09/2026", "fuente": "Tienda Molinos (sesión con beneficio de empresa; venta por caja cerrada, precio por unidad)", "items": out},
          open("precios_molinos.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"items con precio Molinos: {len(out)} | productos Molinos usados: {len(used)} de {len(rows)}")
for code, lst in used.items():
    r = bycode[code]; print(f"  {r['name'][:38]:38} ${round(float(r['price'])):>6} x{r['units']:>2} -> " + ", ".join(i for i, _ in lst)[:110])
print("--- productos Molinos sin item en el catálogo ---")
for r in rows:
    if r["code"] not in used: print("  ", r["name"])
