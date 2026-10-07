# -*- coding: utf-8 -*-
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(BASE, "armar_grupos.py")
s = open(p, encoding="utf-8").read()
old = '''    k = SYN.get(t[0], t[0])
    if k == "panal":'''
new = '''    k = SYN.get(t[0], t[0])
    # calificador de tipo (2da/3ra palabra) que distingue productos distintos dentro del mismo rubro
    for q in t[1:3]:
        if q in QUAL:
            k += " " + q
            break
    if k == "panal":'''
assert old in s
s = s.replace(old, new, 1)
qual = '''QUAL = {"cocido", "crudo", "entera", "entero", "descremada", "descremado", "parcialmente", "natural", "saborizado", "saborizada",
        "integral", "blanco", "blanca", "negro", "negra", "rubio", "rubia", "mascabo", "comun", "fino", "grueso", "gruesa", "largo", "corto",
        "cremoso", "rallado", "untable", "duro", "fresco", "seco", "seca", "molido", "instantaneo", "instantanea", "soluble", "liquido", "liquida",
        "polvo", "barra", "gel", "aerosol", "roll", "spray", "crema", "leudante", "chocolatada", "chocolate", "vainilla", "frutilla",
        "light", "diet", "zero", "sin", "griego", "firme", "bebible", "batido", "colado", "condensada", "evaporada", "salada", "dulce",
        "picante", "verde", "rojo", "amarillo", "mineral", "gas", "tonica", "cola", "naranja", "limon", "pomelo", "manzana", "durazno",
        "multifruta", "uva", "tinto", "rosado", "espumante", "rubia", "negra", "roja", "ipa", "lager", "hoja", "doble", "triple", "simple",
        "humeda", "humedas", "descartable", "recargable", "repuesto", "concentrado", "diluir", "baja", "espuma", "delicada", "color", "blancos",
        "dental", "bucal", "corporal", "facial", "manos", "pies", "capilar", "intimo", "intima", "nocturna", "diurna", "solar",
        "infantil", "kids", "bebe", "junior", "adulto", "hombre", "mujer", "men", "women"}
'''
s = s.replace("SYN = {", qual + "SYN = {", 1)
open(p, "w", encoding="utf-8").write(s)
print("qual ok")
