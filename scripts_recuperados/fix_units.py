# -*- coding: utf-8 -*-
"""Reemplaza parse_env en integrar2.py por una versión más robusta:
- '1 un' no bloquea la búsqueda del pack en el nombre
- 'pack x120' de Coto (número igual a los gramos) se ignora
- 'x N' sin palabra de unidad solo si N<=60 y no coincide con la medida
- productos por conteo (saquitos, sobres, tabletas...) comparan por unidad aunque tengan gramos"""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
p = "integrar2.py"
src = open(p, encoding="utf-8").read()
i0 = src.index("\nUNIT_WORDS = ")
i1 = src.index("STORES = [\n")
helper = r'''
UNIT_WORDS = r"(?:un|uni|unid|unidades|ud|uds|u|tabs?|tabletas?|c[aá]psulas?|sobres?|pastillas?|rollos?|pa[nñ]ales?|toallitas?|bolsitas?|saquitos?|hojas?|servilletas?|pa[nñ]os?|piezas?|comprimidos?|latas?|botellas?|sachets?|bolsas?|cepillos?|maples?)"
COUNT_WORDS = r"(?:tabs?|tabletas?|c[aá]psulas?|sobres?|pastillas?|rollos?|pa[nñ]ales?|toallitas?|bolsitas?|saquitos?|hojas?|servilletas?|pa[nñ]os?|comprimidos?|cepillos?)"
MEAS_WORDS = r"(?:kg|kgs|g|gr|grs|ml|cc|l|lt|lts|litros?|%)"

def _measure_in(s):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:kg|kgs)\b", s)
    if m: return float(m.group(1).replace(",", ".")) * 1000, "g", m, float(m.group(1).replace(",", "."))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:g|gr|grs)\b", s)
    if m: return float(m.group(1).replace(",", ".")), "g", m, float(m.group(1).replace(",", "."))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:l|lt|lts|litros?)\b", s)
    if m: return float(m.group(1).replace(",", ".")) * 1000, "ml", m, float(m.group(1).replace(",", "."))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:ml|cc)\b", s)
    if m: return float(m.group(1).replace(",", ".")), "ml", m, float(m.group(1).replace(",", "."))
    return None

def _units_in(s):
    """(unidades, es_por_conteo). 0 si no hay un pack creíble."""
    if "media docena" in s: return 6, False
    if "docena" in s: return 12, False
    meas = _measure_in(s)
    mnum = int(meas[3]) if meas else None
    m = re.search(r"\b(\d{1,4})\s*(" + UNIT_WORDS + r")\b", s)
    if m and int(m.group(1)) > 1 and int(m.group(1)) != mnum:
        return int(m.group(1)), bool(re.fullmatch(COUNT_WORDS, m.group(2)))
    m = re.search(r"\bx\s?(\d{1,4})(?!\s*" + MEAS_WORDS + r"\b)(?!\s*en\b)\b", s)
    if m:
        n = int(m.group(1))
        if 1 < n <= 60 and n != mnum:
            return n, False
    return 0, False

def parse_env(pres, name):
    """Producto 'por envase': (pack = unidades que trae, meas = {'v','u'} medida total para precio por cantidad)."""
    p = (pres or "").lower().replace("&amp;", "&")
    n = (name or "").lower().replace("&amp;", "&")
    pack, count = _units_in(p)
    if not pack:
        pack, count = _units_in(n)
    meas = None
    if not count:
        for s in (p, n):
            r = _measure_in(s)
            if r:
                v, u, m, _ = r
                if pack > 1 and re.match(r"\s*x\s?\d", s[m.end():]):
                    v = v * pack  # "750 ml x 3": medida por unidad
                meas = {"v": round(v, 2), "u": u}
                break
    if not meas and pack > 1:
        meas = {"v": pack, "u": "un"}
    return pack, meas

'''
src = src[:i0] + helper + src[i1:]
open(p, "w", encoding="utf-8").write(src)
print("parse_env reemplazado")
