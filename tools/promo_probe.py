# -*- coding: utf-8 -*-
"""Baja páginas públicas de promociones y extrae el texto visible con menciones de descuentos."""
import re, io, sys, json, urllib.request, html as H
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36", "Accept": "text/html,application/json;q=0.9,*/*;q=0.8", "Accept-Language": "es-AR,es;q=0.9"}
URLS = {
    "modo": "https://www.modo.com.ar/promos",
    "carrefour": "https://www.carrefour.com.ar/promociones-bancarias",
    "dia": "https://diaonline.supermercadosdia.com.ar/medios-de-pago-y-promociones",
    "jumbo": "https://www.jumbo.com.ar/promociones-bancarias",
    "coto_json": "https://www.coto.com.ar/sitios/cdigi/promociones?format=json",
    "coto_bancos": "https://www.coto.com.ar/sitios/cdigi/promociones-bancarias?format=json",
    "clubln": "https://club.lanacion.com.ar/beneficios/supermercados/supermercados",
    "bbva": "https://www.bbva.com.ar/personas/beneficios/supermercados.html",
    "icbc": "https://www.icbc.com.ar/personas/beneficios/supermercados",
    "santander": "https://www.santander.com.ar/personas/beneficios",
}
KW = re.compile(r"(\d{1,2}\s?%|tope|reintegro|lunes|martes|mi[ée]rcoles|jueves|viernes|s[áa]bado|domingo)", re.I)
out = {}
for k, u in URLS.items():
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40)
        b = r.read().decode("utf-8", "ignore")
        ct = r.headers.get("Content-Type", "")
    except Exception as e:
        print(f"== {k}: ERR {str(e)[:80]}")
        continue
    open(f"C:/Users/ncort/compra-del-mes/tools/promo_{k}.txt", "w", encoding="utf-8").write(b)
    if "json" in ct or b.lstrip().startswith("{"):
        txt = b
    else:
        # next data?
        nd = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', b, re.S)
        if nd:
            txt = nd.group(1)
        else:
            t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", b, flags=re.S)
            t = re.sub(r"<[^>]+>", "\n", t)
            txt = H.unescape(t)
    lines = [l.strip() for l in re.split(r"[\n\r]+|\\n", txt) if l.strip()]
    hits = [l[:220] for l in lines if KW.search(l)]
    print(f"== {k}: {len(b)//1024} KB, {len(hits)} líneas con pistas")
    for l in hits[:45]:
        print("  ", l)
