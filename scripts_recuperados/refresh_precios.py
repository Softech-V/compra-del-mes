# -*- coding: utf-8 -*-
"""Relevamiento masivo: consulta las APIs VTEX de Carrefour/Día/Jumbo para TODOS los items."""
import json, os, re, sys, io, time
import requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36"}

TERMS = {
 "tira-asado":"asado tira","chorizo":"chorizo parrillero","matambre":"matambre","carne-estofado":"roast beef",
 "pollo-entero":"pollo entero","merluza":"filet merluza","salchichas":"salchichas x6","queso-danbo":"queso danbo fetas",
 "salame":"salame milan","mortadela":"mortadela","yogur-firme":"yogur firme","ricota":"ricota","muzzarella":"muzzarella",
 "tapas-pizza":"prepizza","leche-chocolatada":"leche chocolatada 1","dulce-de-leche":"dulce de leche 400",
 "panceta":"panceta","provoleta":"provoleta","aceitunas":"aceitunas verdes","atun-lata":"atun lata",
 "arvejas-lata":"arvejas lata","mayonesa":"mayonesa 475","ketchup":"ketchup","mostaza":"mostaza",
 "caldos":"caldo knorr","sopa-instantanea":"sopa instantanea","snacks-papas":"papas fritas lays","mani":"mani salado",
 "alfajores":"alfajor triple","cacao-amargo":"cacao amargo","miel":"miel 500","levadura":"levadura seca",
 "polvo-hornear":"polvo de hornear","premezcla-bizcochuelo":"bizcochuelo exquisita","gelatina":"gelatina exquisita",
 "arroz-integral":"arroz integral 1kg","granola":"granola","tostadas":"tostadas","budin":"budin",
 "pan-hamburguesa":"pan de hamburguesa","pan-pancho":"pan de pancho","maiz-blanco":"maiz blanco","porotos":"porotos alubia",
 "dulce-membrillo":"dulce de membrillo","galletitas-chocolinas":"chocolinas","gaseosa-coca-15":"coca cola 1.5",
 "gaseosa-coca-zero-225":"coca cola zero 2.25","gaseosa-coca-zero-15":"coca cola zero 1.5","gaseosa-coca-lata":"coca cola lata 354",
 "gaseosa-sprite-225":"sprite 2.25","gaseosa-sprite-zero":"sprite zero 2.25","gaseosa-fanta-225":"fanta naranja 2.25",
 "agua-con-gas":"agua con gas 2","soda":"soda sifon","jugo-listo":"cepita 1","vino-tinto":"vino malbec 750",
 "fernet":"fernet branca 750","te-saquitos":"te saquitos 50","mate-cocido":"mate cocido 50",
 "leche-descremada":"leche descremada larga vida 1","jabon-polvo":"jabon en polvo 3","desodorante-ambiente":"desodorante ambiente",
 "limpiador-pisos":"procenex","lustramuebles":"blem","insecticida":"raid mosquitos","film-cocina":"film adherente",
 "papel-aluminio":"papel aluminio","servilletas":"servilletas","panuelos-descartables":"pañuelos descartables",
 "acondicionador":"acondicionador sedal","desodorante":"desodorante rexona","afeitadoras":"afeitadora bic",
 "protector-solar":"protector solar","algodon":"algodon","repelente":"off repelente","cepillo-dientes":"cepillo dental colgate",
 "pasta-dental-infantil":"pasta dental niños","shampoo-ninos":"shampoo johnson baby","panales-xg":"pañales huggies xg",
 "oleo-calcareo":"oleo calcareo","crema-paspaduras":"hipoglos","jabon-liquido-bebe":"jabon liquido bebe",
 "leche-crecimiento":"leche nido 3",
}

with open(os.path.join(BASE, "ingredientes.json"), encoding="utf-8") as f:
    ing = json.load(f)
items = []
for c in ing["categorias"]:
    for it in c["items"]:
        term = TERMS.get(it["id"]) or it.get("busqueda") or it["nombre"]
        items.append({"id": it["id"], "term": term, "nombre": it["nombre"]})
print(len(items), "items a relevar")

STORES = {
    "carrefour": "www.carrefour.com.ar",
    "dia": "diaonline.supermercadosdia.com.ar",
    "jumbo": "www.jumbo.com.ar",
}
SIZE_RE = re.compile(r"(\d+[.,]?\d*)\s*(kg|g|gr|grs|l|lt|lts|litros?|ml|cc|un|ud|u\b|unidades|pa[ñn]os|m\b|mt)", re.I)

def pick(prods, term):
    """elige el más barato disponible entre los primeros resultados cuyo nombre comparta tokens con el término"""
    toks = [t for t in re.split(r"\W+", term.lower()) if len(t) > 2 and not t.replace('.', '').isdigit()]
    cands = []
    for p in prods[:6]:
        try:
            it = p["items"][0]
            offer = it["sellers"][0]["commertialOffer"]
            price = offer.get("Price") or 0
            if not offer.get("IsAvailable", True) or price <= 0:
                continue
            name = p.get("productName", "")
            score = sum(1 for t in toks if t in name.lower())
            listp = offer.get("ListPrice") or price
            promo = None
            if listp > price * 1.03:
                promo = f"rebajado -{round((1 - price/listp) * 100)}% (antes ${round(listp):,})".replace(",", ".")
            cands.append({"name": name, "price": round(price), "promo": promo,
                          "url": "https://HOST/" + p.get("linkText", "") + "/p", "score": score})
        except Exception:
            continue
    if not cands:
        return None
    maxscore = max(c["score"] for c in cands)
    ok = [c for c in cands if c["score"] >= max(1, maxscore - 1)] or cands
    return min(ok, key=lambda c: c["price"])

def presentacion(name):
    sizes = SIZE_RE.findall(name)
    if sizes:
        q, u = sizes[-1]
        return f"{q} {u.lower()}"
    if re.search(r"x\s?kg|por kg", name.lower()):
        return "por kg"
    return "unidad"

resultados = {k: {} for k in STORES}
for skey, host in STORES.items():
    print(f"--- {skey} ---")
    for i, it in enumerate(items):
        try:
            url = f"https://{host}/api/catalog_system/pub/products/search/?ft={requests.utils.quote(it['term'])}&_from=0&_to=5"
            r = requests.get(url, headers=H, timeout=15)
            prods = r.json() if r.status_code in (200, 206) else []
        except Exception:
            prods = []
        best = pick(prods, it["term"]) if prods else None
        if best:
            resultados[skey][it["id"]] = {
                "producto": best["name"], "presentacion": presentacion(best["name"]),
                "precio": best["price"], "promo": best["promo"],
                "url": best["url"].replace("HOST", host),
            }
        time.sleep(0.35)
    print(f"{skey}: {len(resultados[skey])}/{len(items)} con precio")

with open(os.path.join(BASE, "refresh_raw.json"), "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=1)
print("guardado refresh_raw.json")
