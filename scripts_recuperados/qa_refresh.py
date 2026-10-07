# -*- coding: utf-8 -*-
"""QA previo a aplicar: cambios >40% vs precio anterior, tamaños que no coinciden, precios absurdos."""
import json, os, re, io, sys, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
def load(n):
    p = os.path.join(BASE, n)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
def norm(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
SIZE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|g|gr|grs|ml|cc|lt|lts|l)\b")
def size(s):
    m = SIZE_RE.search(norm(s))
    if not m: return None
    v = float(m.group(1).replace(",", ".")); u = m.group(2)
    if u == "kg": v, u = v * 1000, "g"
    elif u in ("lt", "lts", "l"): v, u = v * 1000, "ml"
    elif u in ("gr", "grs"): u = "g"
    elif u == "cc": u = "ml"
    return v, u

raw = load("refresh_raw.json")
coto = (load("refresh_coto.json") or {}).get("coto", {})
fuentes = {"dia": raw.get("dia", {}), "jumbo": raw.get("jumbo", {}), "carrefour": raw.get("carrefour", {}), "coto": coto}
ing = load("ingredientes.json")
nom = {i["id"]: i for c in ing["categorias"] for i in c["items"]}
cf = {r["id"]: r for r in load("precios_carrefour.json")["items"]}
sospechosos = {}
for st, nuevos in fuentes.items():
    if not nuevos: continue
    viejos = {r["id"]: r for r in load(f"precios_{st}.json")["items"]}
    big, mism, absurd = [], [], []
    for iid, row in nuevos.items():
        if not row or not row.get("precio"): continue
        pn = row["precio"]
        old = viejos.get(iid)
        if old and old.get("precio") and abs(pn - old["precio"]) / old["precio"] > 0.4:
            big.append(f"{iid}: ${old['precio']:,} -> ${pn:,} | {old.get('producto','')[:40]} => {row.get('producto','')[:45]}")
        # tamaño vs referencia Carrefour
        ref = cf.get(iid, {}).get("producto", "") + " " + (cf.get(iid, {}).get("presentacion") or "")
        s_ref, s_new = size(ref), size(row.get("producto", ""))
        if s_ref and s_new and (s_ref[1] != s_new[1] or abs(s_ref[0] - s_new[0]) > 0.12 * s_ref[0]):
            mism.append(f"{iid}: ref {s_ref} vs {s_new} | {row.get('producto','')[:50]}")
        # precio absurdo vs carrefour (x3 o /3)
        pc = cf.get(iid, {}).get("precio")
        if pc and (pn > pc * 3 or pn < pc / 3):
            absurd.append(f"{iid}: carrefour ${pc:,} vs {st} ${pn:,} | {row.get('producto','')[:50]}")
    print(f"=== {st}: {len(nuevos)} nuevos | >40%: {len(big)} | tamaño distinto: {len(mism)} | absurdos: {len(absurd)}")
    for x in big[:40]: print("  >40%", x)
    for x in mism[:25]: print("  SIZE", x)
    for x in absurd[:25]: print("  ABS ", x)
    sospechosos[st] = {"big": big, "mism": mism, "absurd": absurd}
json.dump(sospechosos, open(os.path.join(BASE, "qa_sospechosos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
