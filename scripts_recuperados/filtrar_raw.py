# -*- coding: utf-8 -*-
"""Filtra refresh_raw.json / refresh_coto.json descartando matches dudosos antes de aplicar.
Uso: python filtrar_raw.py dia,jumbo   |   python filtrar_raw.py coto"""
import json, os, re, io, sys, unicodedata, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
def load(n):
    p = os.path.join(BASE, n)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
def norm(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
SIZE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|g|gr|grs|ml|cc|lt|lts|l)\b")
def size(s):
    low = norm(s)
    if re.search(r"\b(x|por)\s*(kg|kilo)\b", low):
        return 1000.0, "g"
    m = SIZE_RE.search(low)
    if not m: return None
    v = float(m.group(1).replace(",", ".")); u = m.group(2)
    if u == "kg": v, u = v * 1000, "g"
    elif u in ("lt", "lts", "l"): v, u = v * 1000, "ml"
    elif u in ("gr", "grs"): u = "g"
    elif u == "cc": u = "ml"
    return v, u
STOP = {"de", "del", "la", "el", "los", "las", "con", "sin", "y", "en", "para", "x", "por", "a", "al", "un", "una", "kg", "uni", "u", "carrefour", "classic", "essential", "expert", "mercado", "huella", "natural"}
CROSS = ["chicle", "galletita", "jugo", "mermelada", "budin", "sopa", "caldo", "condimento", "saborizador", "salsa", "premezcla",
         "pate", "marshmallow", "chips", "snack", "mani ", "polvo", "deshidratad", "saborizada", "gasificada", "yogur", "helado",
         "alfajor", "caramelo", "gomita", "cereal", "barrita", "sabor ", "esencia", "aroma", "jabon", "shampoo", "crema", "pet"]
def toks(s):
    return [t for t in re.findall(r"[a-z]+", norm(s)) if t not in STOP and len(t) > 2]

stores = sys.argv[1].split(",") if len(sys.argv) > 1 else ["dia", "jumbo"]
ing = load("ingredientes.json")
pre = load("ingredientes.pre-base.json")
viejos_ids = {i["id"] for c in pre["categorias"] for i in c["items"]}
cf = {r["id"]: r for r in load("precios_carrefour.json")["items"]}
raw = load("refresh_raw.json")
coto_doc = load("refresh_coto.json")

for st in stores:
    src = coto_doc.get("coto", {}) if st == "coto" else raw.get(st, {})
    old_rows = {r["id"]: r for r in load(f"precios_{st}.json")["items"]}
    keep, drop = {}, []
    for iid, row in src.items():
        if not row or not row.get("precio"):
            continue
        name = row.get("producto", "")
        ref = cf.get(iid, {})
        refname = (ref.get("producto") or "") + " " + (ref.get("presentacion") or "")
        pc = ref.get("precio")
        old = old_rows.get(iid)
        reason = None
        if iid in viejos_ids:
            # item con receta: aceptar salvo salto >40% con producto distinto
            if old and old.get("precio") and abs(row["precio"] - old["precio"]) / old["precio"] > 0.4 and norm(old.get("producto", ""))[:25] != norm(name)[:25]:
                reason = "salto>40% y producto distinto"
        else:
            s_ref, s_new = size(refname), size(name)
            if s_ref and (not s_new or s_ref[1] != s_new[1] or abs(s_ref[0] - s_new[0]) > 0.12 * s_ref[0]):
                reason = f"tamaño {s_new} vs ref {s_ref}"
            elif pc and (row["precio"] > pc * 3 or row["precio"] < pc / 3):
                reason = "precio incoherente vs Carrefour"
            else:
                rt, nt = toks(refname), toks(name)
                if rt and not any(t in nt or any(n.startswith(t[:5]) for n in nt) for t in rt[:2]):
                    reason = "no comparte tipo de producto"
                elif any(c in norm(name) for c in CROSS) and not any(c in norm(refname) for c in CROSS):
                    reason = "otra categoría de producto"
        if reason:
            drop.append(f"{iid}: {name[:45]}  [{reason}]")
        else:
            keep[iid] = row
    print(f"=== {st}: {len(src)} relevados → {len(keep)} aceptados, {len(drop)} descartados")
    for d in drop[:30]:
        print("   -", d)
    if st == "coto":
        coto_doc["coto"] = keep
    else:
        raw[st] = keep

if "coto" in stores:
    shutil.copy(os.path.join(BASE, "refresh_coto.json"), os.path.join(BASE, "refresh_coto.sin-filtrar.json"))
    json.dump(coto_doc, open(os.path.join(BASE, "refresh_coto.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
else:
    shutil.copy(os.path.join(BASE, "refresh_raw.json"), os.path.join(BASE, "refresh_raw.sin-filtrar.json"))
    json.dump(raw, open(os.path.join(BASE, "refresh_raw.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("guardado")
