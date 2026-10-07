# -*- coding: utf-8 -*-
"""Molinos vende por caja cerrada: si la fila trae 'caja', el costo redondea los envases a múltiplos de la caja.
integrar2 debe copiar el campo 'caja' de precios_molinos.json a la fila del item."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
h = open("compra-del-mes.html", encoding="utf-8").read()
old = '''    const packs = Math.ceil(qty / p.size - 1e-9);
    const d = promoDeal(p);'''
new = '''    let packs = Math.ceil(qty / p.size - 1e-9);
    if (p.caja > 1) packs = Math.ceil(packs / p.caja) * p.caja;  // venta por caja cerrada (Tienda Molinos)
    const d = promoDeal(p);'''
if "p.caja > 1" not in h:
    assert h.count(old) == 1, h.count(old)
    h = h.replace(old, new)
    open("compra-del-mes.html", "w", encoding="utf-8").write(h); print("HTML: costo por caja cerrada")
else:
    print("HTML ya tenía caja")
src = open("integrar2.py", encoding="utf-8").read()
old2 = '''                if row.get("sku"):
                    precios[st["key"]]["sku"] = row["sku"]
                    precios[st["key"]]["seller"] = row.get("seller", "1")
                _pk, _ms = parse_env(pres, row.get("producto") or "")'''
new2 = '''                if row.get("sku"):
                    precios[st["key"]]["sku"] = row["sku"]
                    precios[st["key"]]["seller"] = row.get("seller", "1")
                if row.get("caja"):
                    precios[st["key"]]["caja"] = int(row["caja"])
                _pk, _ms = parse_env(pres, row.get("producto") or "")'''
old3 = '''            if row.get("sku"):
                precios[st["key"]]["sku"] = row["sku"]
                precios[st["key"]]["seller"] = row.get("seller", "1")
        entry = {'''
new3 = '''            if row.get("sku"):
                precios[st["key"]]["sku"] = row["sku"]
                precios[st["key"]]["seller"] = row.get("seller", "1")
            if row.get("caja"):
                precios[st["key"]]["caja"] = int(row["caja"])
        entry = {'''
if 'row.get("caja")' not in src:
    assert src.count(old2) == 1 and src.count(old3) == 1, (src.count(old2), src.count(old3))
    src = src.replace(old2, new2).replace(old3, new3)
    open("integrar2.py", "w", encoding="utf-8").write(src); print("integrar2: copia 'caja'")
else:
    print("integrar2 ya copiaba caja")
