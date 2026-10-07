# -*- coding: utf-8 -*-
"""Con meta_carrefour.json (marca + subcategoría): arma grupos de tamaños (grupos.json) y términos de búsqueda para otros súper."""
import json, os, re, sys, io, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 .,]+", " ", s)
STOP = {"de", "del", "la", "el", "los", "las", "con", "sin", "y", "en", "para", "x", "por", "a", "al", "un", "una", "uni", "u"}
SIZE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|kilo|g|gr|grs|gramos|ml|cc|lt|lts|litro|litros|l|u|un|unid|unidades|rollos|panos|hojas|sobres|capsulas|cm)\b")
COUNT_RE = re.compile(r"\bx\s*(\d+)\b")
def singular(w):
    if len(w) > 4 and w.endswith("es") and not w.endswith("les"):
        return w[:-2] if w.endswith(("ones", "ales", "iles")) else w[:-1]
    if len(w) > 3 and w.endswith("s"):
        return w[:-1]
    return w
def toks_de(name, brand):
    low = norm(name)
    for w in norm(brand).split():
        if len(w) > 2:
            low = low.replace(w, " ")
    low = SIZE_RE.sub(" ", low); low = COUNT_RE.sub(" ", low)
    return [singular(t) for t in re.findall(r"[a-z]+", low) if t not in STOP and len(t) > 1]
SYN = {"lavavajilla": "detergente", "yogurt": "yogur"}
def tipo_de(name, brand):
    t = toks_de(name, brand)
    if not t:
        return "?"
    k = SYN.get(t[0], t[0])
    if k == "panal":
        low = norm(name)
        m = re.search(r"talle\s*([a-z]+)", low) or re.search(r"\b(xxxg|xxg|xg|g|m|p|rn)\b", low)
        if m:
            k += " " + m.group(1)
    return k
def size_str(name):
    low = norm(name)
    if re.search(r"\b(x|por)\s*(kg|kilo)\b", low):
        return "1 kg"
    m = SIZE_RE.search(low)
    if m:
        v, u = m.group(1), m.group(2)
        u = {"gr": "g", "grs": "g", "gramos": "g", "cc": "ml", "lt": "l", "lts": "l", "litro": "l", "litros": "l", "kilo": "kg"}.get(u, u)
        return f"{v} {u}"
    m = COUNT_RE.search(low)
    return f"x {m.group(1)}" if m else ""

meta = json.load(open(os.path.join(BASE, "meta_carrefour.json"), encoding="utf-8"))
ing = json.load(open(os.path.join(BASE, "ingredientes.json"), encoding="utf-8"))
pre = json.load(open(os.path.join(BASE, "ingredientes.pre-base.json"), encoding="utf-8"))
viejos = {i["id"] for c in pre["categorias"] for i in c["items"]}

grupos = {}
key_members = {}
terminos = {}
CF_BRANDS = {"carrefour", "carrefour classic", "carrefour essential", "carrefour expert", "carrefour soft", "carrefour bio", "el mercado", "huella natural", "mercado del mar"}
for c in ing["categorias"]:
    for it in c["items"]:
        m = meta.get(it["id"])
        if not m or not m.get("found"):
            continue
        brand = m.get("brand") or ""
        name = m.get("name") or it["nombre"]
        key = f"{c['nombre']}|{m.get('leaf', '')}|{tipo_de(name, brand)}"
        key_members.setdefault(key, []).append(it["id"])
        # término de búsqueda para Día/Jumbo/Coto: marca (si no es propia) + 2-3 palabras del tipo + tamaño
        if it["id"] not in viejos:
            tk = toks_de(name, brand)[:3]
            b = "" if norm(brand).strip() in CF_BRANDS else brand
            term = " ".join(x for x in [b, " ".join(tk), size_str(name)] if x).strip()
            terminos[it["id"]] = term
for key, ids in key_members.items():
    if len(ids) > 1:
        for i in ids:
            grupos[i] = key
json.dump(grupos, open(os.path.join(BASE, "grupos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n_g = len(set(grupos.values()))
print(f"grupos con 2+ tamaños: {n_g} (cubren {len(grupos)} items)")
# actualizar busqueda de los items nuevos
n_t = 0
for c in ing["categorias"]:
    for it in c["items"]:
        if it["id"] in terminos:
            it["busqueda"] = terminos[it["id"]]; n_t += 1
json.dump(ing, open(os.path.join(BASE, "ingredientes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"términos de búsqueda actualizados: {n_t}")
# muestra
import itertools
for key, ids in itertools.islice(((k, v) for k, v in key_members.items() if len(v) > 1), 12):
    print(" ", key, "->", ids)
for iid in list(terminos)[:12]:
    print("  term:", iid, "->", terminos[iid])
