# -*- coding: utf-8 -*-
"""Limpieza post-expansión: saca no-comestibles/aparatos y recomprime imágenes nuevas."""
import json, os, io, sys, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
added = json.load(open(os.path.join(BASE, "base_carrefour_added.json"), encoding="utf-8"))
ing = json.load(open(os.path.join(BASE, "ingredientes.json"), encoding="utf-8"))
pcf_p = os.path.join(BASE, "precios_carrefour.json")
pcf = json.load(open(pcf_p, encoding="utf-8"))
imgs_p = os.path.join(BASE, "imagenes_data.json")
imgs = json.load(open(imgs_p, encoding="utf-8"))
pre = json.load(open(os.path.join(BASE, "imagenes_data.pre-base.json"), encoding="utf-8"))

# 1) sacar aparatos / cosas raras
BAD = ["irrigador", "cepillo electrico", "cepillo eléctrico", "maquina de", "máquina de", "afeitadora electrica"]
drop = set()
for c in ing["categorias"]:
    keep = []
    for i in c["items"]:
        low = i["nombre"].lower()
        if any(b in low for b in BAD):
            drop.add(i["id"]); continue
        keep.append(i)
    c["items"] = keep
pcf["items"] = [r for r in pcf["items"] if r["id"] not in drop]
for d in drop:
    imgs.pop(d, None)
print("eliminados:", drop)

# 2) recomprimir imágenes nuevas (las que no estaban antes)
try:
    from PIL import Image
    n = 0; before = 0; after = 0
    for k, v in list(imgs.items()):
        if k in pre or not v.startswith("data:image"):
            continue
        raw = base64.b64decode(v.split(",", 1)[1])
        before += len(raw)
        try:
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            im.thumbnail((84, 84))
            out = io.BytesIO(); im.save(out, "JPEG", quality=70, optimize=True)
            b = out.getvalue()
            if len(b) < len(raw):
                imgs[k] = "data:image/jpeg;base64," + base64.b64encode(b).decode()
                after += len(b); n += 1
            else:
                after += len(raw)
        except Exception:
            after += len(raw)
    print(f"recomprimidas {n}: {before//1024} KB → {after//1024} KB")
except ImportError:
    print("PIL no disponible, imágenes sin recomprimir")

json.dump(ing, open(os.path.join(BASE, "ingredientes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(pcf, open(pcf_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(imgs, open(imgs_p, "w", encoding="utf-8"), ensure_ascii=False)
print("imagenes_data KB:", os.path.getsize(imgs_p) // 1024)
