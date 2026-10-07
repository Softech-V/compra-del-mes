# -*- coding: utf-8 -*-
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(BASE, "filtrar_raw.py")
s = open(p, encoding="utf-8").read()

s = s.replace('''         "alfajor", "caramelo", "gomita", "cereal", "barrita", "sabor ", "esencia", "aroma", "jabon", "shampoo", "crema", "pet"]''',
'''         "alfajor", "caramelo", "gomita", "cereal", "barrita", "sabor ", "esencia", "aroma", "jabon", "shampoo", "crema", "pet",
         "hamburguesa", "pastelito", "raviol", "pizza", "tablita", "sorrentino", "empanada", "tarta", "milanesa de soja", "medallon"]
BRANDS = ["coca", "sprite", "fanta", "pepsi", "lays", "bimbo", "serenisima", "sancor", "ilolay", "paty", "knorr", "hellmann", "natura",
          "cocinero", "marolio", "arcor", "terrabusi", "bagley", "oreo", "nesquik", "nescafe", "dolca", "cabrales", "taragui", "playadito",
          "rosamonte", "quilmes", "brahma", "stella", "ariel", "ala", "skip", "vivere", "cif", "magistral", "ayudin", "raid", "off",
          "colgate", "dove", "rexona", "sedal", "pantene", "head", "huggies", "pampers", "johnson", "casancrem", "danonino", "danone",
          "yogurisimo", "ser", "tregar", "milkaut", "la paulina", "lucchetti", "matarazzo", "don vicente", "gallo", "molinos", "exquisita"]''', 1)

old = '''        if iid in viejos_ids:
            # item con receta: aceptar salvo salto >40% con producto distinto
            if old and old.get("precio") and abs(row["precio"] - old["precio"]) / old["precio"] > 0.4 and norm(old.get("producto", ""))[:25] != norm(name)[:25]:
                reason = "salto>40% y producto distinto"'''
new = '''        if iid in viejos_ids:
            # item con receta: aceptar salvo salto >40% con producto distinto (y peor match que el anterior)
            if old and old.get("precio") and abs(row["precio"] - old["precio"]) / old["precio"] > 0.4 and norm(old.get("producto", ""))[:25] != norm(name)[:25]:
                itn = toks(ing_nom.get(iid, ""))
                sc_old = sum(1 for t in itn if t in toks(old.get("producto", "")))
                sc_new = sum(1 for t in itn if t in toks(name))
                old_brand = [b for b in BRANDS if b in norm(old.get("producto", ""))]
                if any(c in norm(name) for c in CROSS) and not any(c in norm(ing_nom.get(iid, "")) for c in CROSS):
                    reason = "salto>40% y otra categoría"
                elif old_brand and not any(b in norm(name) for b in old_brand):
                    reason = f"salto>40% y cambia de marca ({old_brand[0]})"
                elif sc_new < sc_old:
                    reason = "salto>40% y match peor que el anterior"'''
assert old in s
s = s.replace(old, new, 1)

old2 = '''            s_ref, s_new = size(refname), size(name)
            if s_ref and (not s_new or s_ref[1] != s_new[1] or abs(s_ref[0] - s_new[0]) > 0.12 * s_ref[0]):
                reason = f"tamaño {s_new} vs ref {s_ref}"'''
new2 = '''            s_ref, s_new = size(refname), size(name)
            por_kg_ref = bool(re.search(r"\\b(x|por)\\s*(kg|kilo)\\b", norm(refname)))
            if por_kg_ref and not s_new:
                pass  # carnes/verduras por kg en otros súper suelen no traer tamaño en el nombre
            elif s_ref and (not s_new or s_ref[1] != s_new[1] or abs(s_ref[0] - s_new[0]) > 0.12 * s_ref[0]):
                reason = f"tamaño {s_new} vs ref {s_ref}"'''
assert old2 in s
s = s.replace(old2, new2, 1)

old3 = '''ing = load("ingredientes.json")'''
new3 = '''ing = load("ingredientes.json")
ing_nom = {i["id"]: i["nombre"] for c in ing["categorias"] for i in c["items"]}'''
assert old3 in s
s = s.replace(old3, new3, 1)
open(p, "w", encoding="utf-8").write(s)
print("filtrar patch ok")
