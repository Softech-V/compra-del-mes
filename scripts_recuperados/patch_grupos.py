# -*- coding: utf-8 -*-
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(BASE, "armar_grupos.py")
s = open(p, encoding="utf-8").read()
a = 'CF_BRANDS = {"carrefour",'
assert a in s
s = s.replace(a, 'CF_BRANDS = {"generico", "complemento", "sin marca", "s/m", "carrefour",', 1)
old = '''            tk = toks_de(name, brand)[:3]
            b = "" if norm(brand).strip() in CF_BRANDS else brand
            term = " ".join(x for x in [b, " ".join(tk), size_str(name)] if x).strip()'''
new = r'''            tk = [t for t in toks_de(name, brand) if t not in ("kg", "kilo", "unidad", "atado", "paquete", "bandeja")][:3]
            b = "" if norm(brand).strip() in CF_BRANDS else brand
            sz = size_str(name)
            if re.search(r"\b(x|por)\s*(kg|kilo|unidad|atado|paquete|bandeja)\b", norm(name)):
                sz = ""
            term = " ".join(x for x in [b, " ".join(tk), sz] if x).strip()'''
assert old in s
s = s.replace(old, new, 1)
old2 = '''        key = f"{c['nombre']}|{m.get('leaf', '')}|{tipo_de(name, brand)}"
        key_members.setdefault(key, []).append(it["id"])'''
new2 = '''        key = f"{c['nombre']}|{m.get('leaf', '')}|{tipo_de(name, brand)}"
        if c["nombre"] not in ("Carnicería", "Verdulería y frutas") and not key.endswith("|mix"):
            key_members.setdefault(key, []).append(it["id"])'''
assert old2 in s
s = s.replace(old2, new2, 1)
open(p, "w", encoding="utf-8").write(s)
print("armar_grupos patch ok")
