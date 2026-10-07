# -*- coding: utf-8 -*-
"""07/09: productos por envase -> agrega 'pack' (unidades que trae) y 'meas' (medida total g/ml/un)
para mostrar precio por unidad/kg/L real y comparar tamaños por precio por cantidad."""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
p = "integrar2.py"
src = open(p, encoding="utf-8").read()
if "def parse_env(" in src:
    print("integrar2.py ya tenía parse_env"); sys.exit(0)

helper = r'''
UNIT_WORDS = r"(?:un|uni|unid|unidades|u|tabs?|tabletas?|c[aá]psulas?|sobres?|pastillas?|rollos?|pa[nñ]ales?|toallitas?|bolsitas?|saquitos?|hojas?|servilletas?|pa[nñ]os?|piezas?|comprimidos?|latas?|botellas?|sachets?|bolsas?|cepillos?|maples?)"
MEAS_WORDS = r"(?:kg|kgs|g|gr|grs|ml|cc|l|lt|lts|litros?|%)"

def _units_in(s):
    if "media docena" in s: return 6
    if "docena" in s: return 12
    m = re.search(r"\bx\s?(\d{1,4})(?!\s*" + MEAS_WORDS + r"\b)(?!\s*en\b)\s*" + UNIT_WORDS + r"?\b", s)
    if m: return int(m.group(1))
    m = re.search(r"\b(\d{1,4})\s*" + UNIT_WORDS + r"\b", s)
    if m: return int(m.group(1))
    return 0

def _measure_in(s):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:kg|kgs)\b", s)
    if m: return float(m.group(1).replace(",", ".")) * 1000, "g", m
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:g|gr|grs)\b", s)
    if m: return float(m.group(1).replace(",", ".")), "g", m
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:l|lt|lts|litros?)\b", s)
    if m: return float(m.group(1).replace(",", ".")) * 1000, "ml", m
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:ml|cc)\b", s)
    if m: return float(m.group(1).replace(",", ".")), "ml", m
    return None

def parse_env(pres, name):
    """Producto 'por envase': (pack = unidades que trae, meas = {'v','u'} medida total del envase)."""
    p = (pres or "").lower().replace("&amp;", "&")
    n = (name or "").lower().replace("&amp;", "&")
    pack = _units_in(p) or _units_in(n)
    meas = None
    for s in (p, n):
        r = _measure_in(s)
        if r:
            v, u, m = r
            # "750 ml x 3" -> la medida es por unidad, multiplicar por el pack
            if pack > 1 and re.match(r"\s*x\s?\d", s[m.end():]):
                v = v * pack
            meas = {"v": round(v, 2), "u": u}
            break
    if not meas and pack > 1:
        meas = {"v": pack, "u": "un"}
    return pack, meas

'''
anchor = "STORES = [\n"
assert anchor in src
src = src.replace(anchor, helper + anchor, 1)

old = '''                if row.get("sku"):
                    precios[st["key"]]["sku"] = row["sku"]
                    precios[st["key"]]["seller"] = row.get("seller", "1")
                continue
'''
new = '''                if row.get("sku"):
                    precios[st["key"]]["sku"] = row["sku"]
                    precios[st["key"]]["seller"] = row.get("seller", "1")
                _pk, _ms = parse_env(pres, row.get("producto") or "")
                if _pk > 1:
                    precios[st["key"]]["pack"] = _pk
                if _ms:
                    precios[st["key"]]["meas"] = _ms
                continue
'''
assert src.count(old) == 1, src.count(old)
src = src.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(src)
print("integrar2.py parcheado: parse_env + pack/meas en productos por envase")
