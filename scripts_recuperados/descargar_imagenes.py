# -*- coding: utf-8 -*-
"""Descarga miniaturas de producto y las guarda como data URIs en imagenes_data.json."""
import json, os, re, base64, sys, io
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "imagenes_urls.json"), encoding="utf-8") as f:
    urls = json.load(f)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36"}

def variants(url):
    out = []
    m = re.match(r"(https://[a-z]+\.vteximg\.com\.br/arquivos/ids/)(\d+)(/.*)", url)
    if m:
        out.append(m.group(1) + m.group(2) + "-140-140" + m.group(3))  # miniatura VTEX
    out.append(url.replace("/large/", "/medium/") if "/large/" in url else url)
    if url not in out:
        out.append(url)
    return out

data = {}
for iid, url in urls.items():
    got = None
    for v in variants(url):
        try:
            r = requests.get(v, headers=HEADERS, timeout=15)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image") and len(r.content) > 500:
                got = r.content
                break
        except Exception:
            continue
    if not got:
        print(f"SIN IMAGEN: {iid}")
        continue
    if len(got) > 220_000:
        print(f"MUY PESADA ({len(got)//1024}KB), salto: {iid}")
        continue
    b64 = base64.b64encode(got).decode()
    data[iid] = "data:image/jpeg;base64," + b64
    print(f"ok {iid}: {len(got)//1024}KB")

with open(os.path.join(BASE, "imagenes_data.json"), "w", encoding="utf-8") as f:
    json.dump(data, f)
print(f"{len(data)} imágenes embebidas, total {sum(len(v) for v in data.values())//1024}KB")
