# -*- coding: utf-8 -*-
"""Suma al catálogo los productos de Tienda Molinos (Alimentos) que no tenían equivalente, y las 6 Box
(sin vinos) como productos. Escribe molinos_manual_map.json {item_id: code} para match_molinos.py."""
import csv, json, re, io, sys, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")[:48]

rows = list(csv.DictReader(open("molinos_raw.tsv", encoding="utf-8"), delimiter="\t"))
ing = json.load(open("ingredientes.json", encoding="utf-8"))
cats = {c["nombre"]: c for c in ing["categorias"]}
existing = {i["id"] for c in ing["categorias"] for i in c["items"]}
used = {r["id"] for r in json.load(open("precios_molinos.json", encoding="utf-8"))["items"]}
# códigos ya cruzados con un item existente
matched_codes = set()
mm = json.load(open("precios_molinos.json", encoding="utf-8"))["items"]
for r in mm:
    m = re.search(r"/p/(\d+)", r["url"])
    if m: matched_codes.add(m.group(1))

DESAYUNO = re.compile(r"yerba|mate cocido|cruz de malta|nobleza gaucha|oblea|alfajor|chocoarroz|yogubar|chocolatad|cookies|brownie|bizcochuelo", re.I)
manual = {}
added = 0
for r in rows:
    if r["stock"] == "outOfStock" or r["name"].startswith("Caja Mix") or r["code"] in matched_codes:
        continue
    t = [x.strip() for x in r["titles"].split(" / ")] if r["titles"] else [r["name"]]
    brand = t[0].title() if t else ""
    size = ""
    m = re.search(r"(\d+(?:[.,]\d+)?\s*(?:ml|g|gr|grs|kg|u\b|unidades))", " ".join(t[1:]), re.I) or re.search(r"x(\d+(?:[.,]\d+)?\s*(?:ml|g|kg|u\b))", r["name"], re.I)
    if m: size = m.group(1).replace("grs", "g").replace("gr", "g").replace("unidades", "un")
    desc = " ".join(x for x in t[1:] if not re.match(r"^(unidad|\d)", x, re.I))[:60]
    nombre = f"{t[1] if len(t) > 1 else r['name']} {brand}" + (f" {desc.split(' ', 1)[1] if ' ' in desc and len(t) > 2 else ''}" if len(t) > 2 else "")
    nombre = re.sub(r"\s+", " ", f"{t[1] if len(t) > 1 else ''} {brand} {t[2] if len(t) > 2 else ''} {size}").strip()
    iid = slug(nombre)
    if iid in existing: continue
    cat = "Desayuno y merienda" if DESAYUNO.search(r["titles"] + " " + r["name"]) else "Almacén"
    cats[cat]["items"].append({"id": iid, "nombre": nombre, "cantidad_mes": "a elección", "unidad_precio": "por unidad", "busqueda": nombre.lower(), "molinos": True})
    existing.add(iid); manual[iid] = r["code"]; added += 1
    print(f"  + [{cat[:8]}] {nombre}")

BOXES = [
    ("52026", "Box Molinos Llená tu Alacena (11 productos)", 19436, 24295),
    ("52029", "Box Molinos Fanáticos de Lucchetti (8 productos)", 15204, 19005),
    ("52031", "Box Molinos Especialidades (8 productos)", 23108, 42015),
    ("52027", "Box Molinos Condimentá tu Mesa (8 productos)", 27297, 45495),
    ("52030", "Box Molinos Libre de Gluten (8 productos)", 20984, 34974),
    ("53026", "Box Molinos Merendar (6 productos)", 17991, 23989),
]
if "Box Molinos" not in cats:
    ing["categorias"].append({"nombre": "Box Molinos", "items": []}); cats["Box Molinos"] = ing["categorias"][-1]
for code, nombre, price, prev in BOXES:
    iid = slug(nombre)
    if iid not in existing:
        cats["Box Molinos"]["items"].append({"id": iid, "nombre": nombre, "cantidad_mes": "a elección", "unidad_precio": "por caja", "busqueda": nombre.lower(), "molinos": True})
        existing.add(iid); added += 1
    manual[iid] = code
json.dump(ing, open("ingredientes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
old = {}
try: old = json.load(open("molinos_manual_map.json", encoding="utf-8"))
except Exception: pass
old.update(manual)
json.dump(old, open("molinos_manual_map.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("items agregados:", added, "| mapa manual:", len(old))
