# -*- coding: utf-8 -*-
"""Regla simple: si el envase trae N unidades (pack>1), la medida de comparación es 'N un',
salvo el patrón '750 ml x 3' (medida por unidad seguida de x N) que suma volumen/peso total."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
p = "integrar2.py"
src = open(p, encoding="utf-8").read()
old = '''    meas = None
    if not count:
        for s in (p, n):
            r = _measure_in(s)
            if r:
                v, u, m, _ = r
                if pack > 1 and re.match(r"\\s*x\\s?\\d", s[m.end():]):
                    v = v * pack  # "750 ml x 3": medida por unidad
                meas = {"v": round(v, 2), "u": u}
                break
    if not meas and pack > 1:
        meas = {"v": pack, "u": "un"}
    return pack, meas
'''
new = '''    meas = None
    if pack > 1:
        for s in (p, n):
            r = _measure_in(s)
            if r and re.match(r"\\s*x\\s?\\d", s[r[2].end():]):
                meas = {"v": round(r[0] * pack, 2), "u": r[1]}  # "750 ml x 3": medida por unidad
                break
        if not meas:
            meas = {"v": pack, "u": "un"}
    else:
        for s in (p, n):
            r = _measure_in(s)
            if r:
                meas = {"v": round(r[0], 2), "u": r[1]}
                break
    return pack, meas
'''
assert src.count(old) == 1, src.count(old)
src = src.replace(old, new)
open(p, "w", encoding="utf-8").write(src)
print("parse_env: pack manda")
