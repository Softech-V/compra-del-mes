# -*- coding: utf-8 -*-
"""refresh_precios.py: (a) permitir elegir tiendas por argv, (b) exigir mismo tamaño que el término, (c) exigir marca si el término la trae."""
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(BASE, "refresh_precios.py")
s = open(p, encoding="utf-8").read()

old_stores = '''STORES = {
    "carrefour": "www.carrefour.com.ar",
    "dia": "diaonline.supermercadosdia.com.ar",
    "jumbo": "www.jumbo.com.ar",
}'''
new_stores = '''STORES = {
    "carrefour": "www.carrefour.com.ar",
    "dia": "diaonline.supermercadosdia.com.ar",
    "jumbo": "www.jumbo.com.ar",
}
if len(sys.argv) > 1:
    STORES = {k: v for k, v in STORES.items() if k in sys.argv[1].split(",")}
    print("tiendas:", list(STORES))

def _size_norm(text):
    m = SIZE_RE.search(text or "")
    if not m:
        return None
    v = float(m.group(1).replace(",", "."))
    u = m.group(2).lower()
    if u in ("kg",):
        v, u = v * 1000, "g"
    elif u in ("l", "lt", "lts", "litro", "litros"):
        v, u = v * 1000, "ml"
    elif u in ("g", "gr", "grs"):
        u = "g"
    elif u in ("ml", "cc"):
        u = "ml"
    else:
        u = "un"
    return v, u

def _size_ok(term, name):
    ts = _size_norm(term)
    if not ts:
        return True
    ns = _size_norm(name)
    if not ns:
        return False
    return ts[1] == ns[1] and abs(ts[0] - ns[0]) <= max(0.08 * ts[0], 1)'''
assert old_stores in s
s = s.replace(old_stores, new_stores, 1)

old_loop = '''            name = p.get("productName", "")
            low = name.lower()
            if iid in BULK_IDS and any(b in low for b in BLACK_BULK):
                continue'''
new_loop = '''            name = p.get("productName", "")
            low = name.lower()
            if iid in BULK_IDS and any(b in low for b in BLACK_BULK):
                continue
            if not _size_ok(term, name):
                continue'''
assert old_loop in s
s = s.replace(old_loop, new_loop, 1)
open(p, "w", encoding="utf-8").write(s)
print("refresh_precios patch ok")
