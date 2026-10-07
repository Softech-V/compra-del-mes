# -*- coding: utf-8 -*-
"""Base amplia de productos desde Carrefour: 1 producto por tipo y tamaño por subcategoría."""
import json, os, re, sys, io, time, base64, unicodedata
import requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36"}
HOST = "www.carrefour.com.ar"
TEST = len(sys.argv) > 1 and sys.argv[1] == "test"
CAP_GRUPOS = 10   # máx. tipos×tamaño por subcategoría
PER_PAGE = 50

LEAVES = {
 "Almacén": [163,164,165,166,167,169,170,171,173,174,175,177,179,180,181,182,702,184,185,186,187,188,189,
             191,192,193,194,196,197,198,200,201,202,203,204,207,215,216,217,707,658,329],
 "Desayuno y merienda": [209,210,211,212,213,224,225,226,227,228,230,231,232,234,235,239,240,241,243,244,
                         245,247,248,249,251,252,253,341,342,343,206],
 "Bebidas": [256,258,259,278,279,280,281,282,284,285,287,288,289,290,291],
 "Heladera": [294,295,296,297,298,300,301,302,304,305,306,307,308,309,311,312,313,314,315,316,317,319,320,
              345,346,348,349,350,353,355,356,357,358,703],
 "Carnicería": [322,323,324,326,327,328],
 "Verdulería y frutas": [331,332,333,334],
 "Limpieza y hogar": [361,362,363,364,365,368,369,370,371,376,378,380,381,382,383,384,385,386,388,389,
                      391,392,393,397,399,400,401],
 "Perfumería e higiene": [404,405,406,407,409,410,413,414,415,416,419,420,423,424,425,426,428,429,430,
                          431,432,433,434,436,437,439,440,441,443],
 "Bebé": [452,453,459,460,461,663,664,463,464],
}
if TEST:
    LEAVES = {"Limpieza y hogar": [378], "Heladera": [294], "Verdulería y frutas": [332]}

tree = json.load(open(os.path.join(BASE, "cf_tree.json"), encoding="utf-8"))
LEAF_NAME = {}
def walk(n):
    LEAF_NAME[n["id"]] = n["name"]
    for k in n.get("children") or []:
        walk(k)
for n in tree:
    walk(n)

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 .,]+", " ", s)

STOP = {"de", "del", "la", "el", "los", "las", "con", "sin", "y", "en", "para", "x", "por", "a", "al", "un", "una"}
GENERIC = {"fideo", "galletita", "queso", "leche", "yogur", "yogurt", "gaseosa", "jugo", "aceite", "vino", "cerveza",
           "agua", "pan", "arroz", "harina", "salsa", "crema", "carne", "pollo", "cerdo", "jabon", "papel", "bolsa",
           "toallita", "cereal", "alfajor", "chocolate", "caramelo", "te", "cafe", "azucar", "dulce", "mermelada",
           "aceituna", "atun", "sal", "caldo", "sopa", "pure", "premezcla", "snack", "papa", "helado", "hamburguesa",
           "medallon", "nugget", "pizza", "tapa", "postre", "manteca", "margarina", "huevo", "salchicha", "fiambre",
           "jamon", "limpiador", "desodorante", "shampoo", "acondicionador", "pasta", "cepillo", "protector",
           "panal", "bife", "bizcocho", "budin", "tostada", "grisin", "barrita", "granola", "mate", "yerba",
           "edulcorante", "miel", "vegetal", "verdura", "fruta", "polvo", "lavandina", "suavizante",
           "detergente", "esponja", "rollo", "servilleta", "insecticida", "repelente", "enjuague",
           "hilo", "toalla", "tampon", "gel", "locion", "oleo", "colonia", "espuma", "maquina", "hoja"}
VARIANT = ["lavanda", "limon", "citrus", "floral", "frutilla", "vainilla", "banana", "durazno", "light", "diet",
           "zero", "sin azucar", "sin tacc", "sin gluten", "integral", "mini", "sensitive", "extra", "ultra",
           "max", "plus", "aloe", "coco", "manzana", "uva", "pera", "menta", "cereza", "arandano", "frutos rojos",
           "bebe", "kids", "infantil", "reducido", "descremad", "semi", "saborizad", "rellen", "banad", "ahumad",
           "picante", "especiad", "hierbas", "ajo", "queso", "jamon", "cebolla", "pomelo", "naranja", "tropical",
           "multifruta", "mango", "kiwi", "anana", "chocolate", "dulce de leche", "caramelo"]
SIZE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|kilo|g|gr|grs|gramos|ml|cc|lt|lts|litro|litros|l|u|un|unid|unidades|rollos|panos|hojas|sobres|capsulas|cm)\b")
COUNT_RE = re.compile(r"\bx\s*(\d+)\b")

def singular(w):
    if len(w) > 4 and w.endswith("es") and not w.endswith("les"):
        return w[:-2] if w.endswith(("ones", "ales", "iles")) else w[:-1]
    if len(w) > 3 and w.endswith("s"):
        return w[:-1]
    return w

def parse_size(low):
    m = SIZE_RE.search(low)
    if m:
        v = float(m.group(1).replace(",", "."))
        u = m.group(2)
        if u in ("kg", "kilo"):
            v, u = v * 1000, "g"
        elif u in ("g", "gr", "grs", "gramos"):
            u = "g"
        elif u in ("lt", "lts", "l", "litro", "litros"):
            v, u = v * 1000, "ml"
        elif u in ("ml", "cc"):
            u = "ml"
        elif u in ("u", "un", "unid", "unidades"):
            u = "un"
        elif u == "panos":
            u = "paños"
        return v, u
    m = COUNT_RE.search(low)
    if m:
        return float(m.group(1)), "un"
    return None, None

def bucket(v, u):
    if v is None or v <= 0:
        return "sd"
    mag = 10 ** (len(str(int(v))) - 2) if v >= 10 else 1
    return f"{u}{int(round(v / mag) * mag)}"

def tipo_de(name, brand):
    low = norm(name)
    b = norm(brand or "")
    for w in b.split():
        if len(w) > 2:
            low = low.replace(w, " ")
    low = SIZE_RE.sub(" ", low)
    low = COUNT_RE.sub(" ", low)
    toks = [singular(t) for t in re.findall(r"[a-z]+", low) if t not in STOP and len(t) > 1]
    if not toks:
        return "?"
    if toks[0] in GENERIC and len(toks) > 1:
        return toks[0] + " " + toks[1]
    return toks[0]

def penalty(name):
    low = norm(name)
    return sum(1 for v in VARIANT if v in low)

def slug(s):
    s = norm(s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:40]

# catálogo y precios existentes
ing = json.load(open(os.path.join(BASE, "ingredientes.json"), encoding="utf-8"))
cat_items = {c["nombre"]: c["items"] for c in ing["categorias"]}
existing_ids = {i["id"] for c in ing["categorias"] for i in c["items"]}
pcf_path = os.path.join(BASE, "precios_carrefour.json")
pcf = json.load(open(pcf_path, encoding="utf-8"))
rows = {r["id"]: r for r in pcf["items"]}
existing_skus = {str(r.get("sku")) for r in rows.values() if r.get("sku")}
existing_keys = set()
for r in rows.values():
    v, u = parse_size(norm(r.get("producto", "") + " " + (r.get("presentacion") or "")))
    existing_keys.add((tipo_de(r.get("producto", ""), ""), bucket(v, u)))
imgs = json.load(open(os.path.join(BASE, "imagenes_data.json"), encoding="utf-8"))

added = []
for catname, leaves in LEAVES.items():
    for leaf in leaves:
        try:
            r = requests.get(f"https://{HOST}/api/catalog_system/pub/products/search/?fq=C:{leaf}&_from=0&_to={PER_PAGE-1}&O=OrderByTopSaleDESC", headers=H, timeout=20)
            prods = r.json() if r.status_code in (200, 206) else []
        except Exception as e:
            print(f"  fallo leaf {leaf}: {e}")
            prods = []
        groups = {}
        order = []
        for prod in prods:
            name = (prod.get("productName") or "").strip()
            if not name:
                continue
            it = prod["items"][0]
            seller = it["sellers"][0]
            offer = seller["commertialOffer"]
            price = offer.get("Price")
            if not price or not offer.get("IsAvailable", True) or price > 200000:
                continue
            low = norm(name)
            if any(b in low for b in ("combo", "canasta", "gift", "regalo")):
                continue
            v, u = parse_size(low)
            key = (tipo_de(name, prod.get("brand")), bucket(v, u))
            listp = offer.get("ListPrice") or 0
            promo = f"antes ${round(listp):,}".replace(",", ".") if price * 1.05 < listp < price * 3 else None
            cand = {"name": name, "precio": round(price), "sku": str(it["itemId"]), "seller": seller["sellerId"],
                    "link": prod.get("linkText", ""), "img": (it.get("images") or [{}])[0].get("imageUrl"),
                    "pres": (f"{v:g} {u}" if v else "1 un"), "promo": promo, "pen": penalty(name), "key": key}
            if key not in groups:
                groups[key] = cand
                order.append(key)
            else:
                g = groups[key]
                if (cand["pen"], cand["precio"]) < (g["pen"], g["precio"]):
                    groups[key] = cand
        n_leaf = 0
        for key in order[:CAP_GRUPOS]:
            c = groups[key]
            if c["sku"] in existing_skus or key in existing_keys:
                continue
            iid = slug(c["name"]) or f"cf-{c['sku']}"
            base_id = iid
            k = 2
            while iid in existing_ids:
                iid = f"{base_id}-{k}"
                k += 1
            existing_ids.add(iid)
            existing_keys.add(key)
            existing_skus.add(c["sku"])
            cat_items.setdefault(catname, []).append({"id": iid, "nombre": c["name"][:70], "cantidad_mes": "a elección",
                                                     "unidad_precio": "por envase", "busqueda": c["name"][:60]})
            rows[iid] = {"id": iid, "producto": c["name"], "presentacion": c["pres"], "precio": c["precio"],
                         "promo": c["promo"], "url": f"https://{HOST}/{c['link']}/p", "sku": c["sku"], "seller": c["seller"]}
            if c["img"] and not TEST:
                m = re.match(r"(https://[a-z]+\.vteximg\.com\.br/arquivos/ids/)(\d+)(/.*)", c["img"])
                for tu in ([m.group(1) + m.group(2) + "-100-100" + m.group(3)] if m else []) + [c["img"]]:
                    try:
                        rr = requests.get(tu, headers=H, timeout=15)
                        if rr.status_code == 200 and rr.headers.get("content-type", "").startswith("image") and len(rr.content) < 60000:
                            imgs[iid] = "data:image/jpeg;base64," + base64.b64encode(rr.content).decode()
                            break
                    except Exception:
                        continue
            added.append((catname, LEAF_NAME.get(leaf, leaf), c["name"], c["precio"], c["pres"]))
            n_leaf += 1
        print(f"{catname} / {LEAF_NAME.get(leaf, leaf)}: {len(prods)} productos → {len(groups)} tipos → +{n_leaf}")
        time.sleep(0.3)

if not TEST:
    for c in ing["categorias"]:
        c["items"] = cat_items[c["nombre"]]
    json.dump(ing, open(os.path.join(BASE, "ingredientes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    pcf["items"] = list(rows.values())
    json.dump(pcf, open(pcf_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(imgs, open(os.path.join(BASE, "imagenes_data.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump(added, open(os.path.join(BASE, "base_carrefour_added.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"TOTAL agregados: {len(added)}")
for a in added[:80]:
    print("  ", a)
