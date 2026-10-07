# -*- coding: utf-8 -*-
import io, sys, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(BASE, "base_carrefour.py")
s = open(p, encoding="utf-8").read()

# --- parse_size: reemplazar todo el bloque entre 'def parse_size' y 'def bucket'
i = s.index("def parse_size(low):")
j = s.index("def bucket(")
new_ps = r'''def parse_size(low):
    if re.search(r"\b(x|por)\s*(kg|kilo)\b", low):
        return 1000.0, "g"
    if re.search(r"\b(x|por)\s*(atado|paquete|unidad|un|bandeja|docena|maple)\b", low):
        return (12.0 if "docena" in low else 30.0 if "maple" in low else 1.0), "un"
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

'''
s = s[:i] + new_ps + s[j:]

# --- tipo_de: reemplazar bloque entre 'def tipo_de' y 'def penalty'
i = s.index("def tipo_de(name, brand):")
j = s.index("def penalty(")
new_t = r'''def tipo_de(name, brand):
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
    SYN = {"lavavajilla": "detergente", "lavavajillas": "detergente", "yogurt": "yogur"}
    t = SYN.get(toks[0], toks[0])
    if t == "panal":
        m = re.search(r"talle\s*([a-z]+)", low) or re.search(r"\b(xxxg|xxg|xg|g|m|p|rn)\b", low)
        if m:
            t += " " + m.group(1)
    return t

'''
s = s[:i] + new_t + s[j:]
open(p, "w", encoding="utf-8").write(s)

# prueba rápida
src = s.split("# catálogo y precios existentes")[0].replace("os.path.dirname(os.path.abspath(__file__))", repr(BASE))
ns = {}
exec(compile(src, "bc", "exec"), ns)
for n, b in [("Zapallo japones cabutian x kg", ""), ("Puerro x atado", ""), ("Pañales Pampers Confort Sec talle G x 36", "Pampers"),
             ("Huevos blancos x docena", ""), ("Lavavajilla Carrefour Essential 750 ml", "Carrefour"), ("Detergente Magistral 750 ml", "Magistral")]:
    low = ns["norm"](n)
    print(n, "->", ns["parse_size"](low), "|", ns["tipo_de"](n, b))
print("patch ok")
