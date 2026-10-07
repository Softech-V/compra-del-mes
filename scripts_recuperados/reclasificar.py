# -*- coding: utf-8 -*-
"""Reubica productos nuevos según lo que SON (no el gusto): snacks sabor asado -> Almacén, rabas -> Heladera, etc."""
import json, os, re, sys, io, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))

def norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()

# (regex sobre nombre normalizado, categoría destino) — se evalúan en orden, gana la primera
RULES = [
    (r"\bpanal|toallitas humedas|oleo calcareo|leche infantil|nidina|nutrilon|sancor bebe|papilla|mamadera|chupete|\bbebe\b|baby", "Bebé"),
    (r"congelad|mccain|helado\b|nugget|rebozad|medallon|hamburguesa|patitas|rabas|formitas|bastones de|pizza|prepizza|empanada|tarta de|tapas? (de|para)", "Heladera"),
    (r"papas? fritas|papas pay|snack|nacho|palitos|chizito|pochoclo|tostadita|mani\b|maní|dorito|cheetos|pringles|krachito|quento|lays|pehuamar|saladix|3d\b", "Almacén"),
    (r"galletita|alfajor|chocolate|bombon|caramelo|gomita|chicle|turron|oblea|budin|magdalena|cereal|copos de|granola|barrita|mermelada|dulce de leche|\bmiel\b|cafe\b|nescafe|yerba|\bte\b|mate cocido|cacao|nesquik|azucar|edulcorante|tostada|grisin|bizcocho|pan lact|pan de|tortilla", "Desayuno y merienda"),
    (r"gaseosa|coca|pepsi|sprite|fanta|cerveza|\bvino\b|agua mineral|agua saborizada|agua con gas|soda\b|\bjugo\b(?! de limon)|energizante|isotonic|gatorade|powerade|sidra|fernet|aperitivo", "Bebidas"),
    (r"detergente|lavandina|jabon en polvo|jabon liquido para ropa|jabon para ropa|suavizante|limpiador|desengrasante|papel higienico|rollo de cocina|servilleta|bolsa|esponja|insecticida|raid\b|desodorante de ambiente|aromatiza|lustramuebles|cera\b|limpiavidrio|quitamancha|apresto|antihumedad|fosforo|vela\b|trapo|pano\b|guante|lavavajilla|finish", "Limpieza y hogar"),
    (r"shampoo|acondicionador|desodorante|antitranspirante|pasta dental|cepillo|enjuague bucal|hilo dental|jabon de tocador|jabon liquido|toallitas femeninas|protector diario|tampon|higiene intima|crema (facial|corporal|para manos|de manos|antiarrugas|hidratante)|serum|afeitar|gillette|bic\b|repelente|protector solar|talco|colonia|desmaquillante|tintura|coloracion|gel para|fijador|piojo", "Perfumería e higiene"),
    (r"yogur|\bleche\b|manteca|margarina|crema de leche|queso|ricota|fiambre|jamon|salame|salamin|mortadela|salchicha|bondiola|panceta|longaniza|chorizo (seco|colorado|espanol)|huevo|ravioles|noquis|sorrentino|pasta fresca|postre|flan\b|dulce de membrillo|levadura", "Heladera"),
    (r"x kg|por kg|\bkg\b", None),  # frescos por kg: no mover (carne/verdura ya bien)
]

ing = json.load(open(os.path.join(BASE, "ingredientes.json"), encoding="utf-8"))
pre = json.load(open(os.path.join(BASE, "ingredientes.pre-base.json"), encoding="utf-8"))
protegidos = {i["id"] for c in pre["categorias"] for i in c["items"]}
cats = {c["nombre"]: c for c in ing["categorias"]}
moves = []
for c in ing["categorias"]:
    keep = []
    for it in c["items"]:
        if it["id"] in protegidos:
            keep.append(it); continue
        low = norm(it["nombre"])
        target = c["nombre"]
        for pat, dest in RULES:
            if re.search(pat, low):
                if dest:
                    target = dest
                break
        if target != c["nombre"]:
            moves.append((c["nombre"], target, it["nombre"]))
            cats[target]["items"].append(it)
        else:
            keep.append(it)
    c["items"] = keep
json.dump(ing, open(os.path.join(BASE, "ingredientes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"movidos: {len(moves)}")
for a, b, n in moves:
    print(f"  {a} → {b}: {n}")
print({c["nombre"]: len(c["items"]) for c in ing["categorias"]})
