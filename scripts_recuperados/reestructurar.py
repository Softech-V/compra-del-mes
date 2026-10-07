# -*- coding: utf-8 -*-
"""Crea la categoría Heladera, mueve los fríos, y agrega todos los items nuevos (sin precio)."""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, "ingredientes.json"), encoding="utf-8") as f:
    ing = json.load(f)

# --- índice actual ---
all_items = {}
for c in ing["categorias"]:
    for it in c["items"]:
        all_items[it["id"]] = it

A_HELADERA = ["jamon", "queso-cremoso", "queso-rallado", "crema", "manteca",
              "queso-untable", "yogur-bebible", "postrecitos", "tapas-tarta", "tapas-empanadas", "patitas"]
A_DESAYUNO = ["leche"]

NUEVOS = [
 # (cat, id, nombre)
 ("Carnicería", "tira-asado", "Asado (tira) x kg"), ("Carnicería", "chorizo", "Chorizos x kg"),
 ("Carnicería", "matambre", "Matambre x kg"), ("Carnicería", "carne-estofado", "Carne para estofado x kg"),
 ("Carnicería", "pollo-entero", "Pollo entero x kg"), ("Carnicería", "merluza", "Filet de merluza x kg"),
 ("Heladera", "salchichas", "Salchichas (x6)"), ("Heladera", "queso-danbo", "Queso danbo/barra en fetas"),
 ("Heladera", "salame", "Salame"), ("Heladera", "mortadela", "Mortadela"),
 ("Heladera", "yogur-firme", "Yogur firme (pack x4)"), ("Heladera", "ricota", "Ricota"),
 ("Heladera", "muzzarella", "Muzzarella"), ("Heladera", "tapas-pizza", "Prepizzas (x2)"),
 ("Heladera", "leche-chocolatada", "Leche chocolatada 1L"), ("Heladera", "dulce-de-leche", "Dulce de leche ~400g"),
 ("Heladera", "panceta", "Panceta"), ("Heladera", "provoleta", "Provoleta"),
 ("Almacén", "aceitunas", "Aceitunas verdes"), ("Almacén", "atun-lata", "Atún en lata"),
 ("Almacén", "arvejas-lata", "Arvejas en lata"), ("Almacén", "mayonesa", "Mayonesa"),
 ("Almacén", "ketchup", "Ketchup"), ("Almacén", "mostaza", "Mostaza"),
 ("Almacén", "caldos", "Caldos en cubo"), ("Almacén", "sopa-instantanea", "Sopa instantánea"),
 ("Almacén", "snacks-papas", "Papas fritas de bolsa"), ("Almacén", "mani", "Maní"),
 ("Almacén", "alfajores", "Alfajores"), ("Almacén", "cacao-amargo", "Cacao amargo"),
 ("Almacén", "miel", "Miel"), ("Almacén", "levadura", "Levadura"),
 ("Almacén", "polvo-hornear", "Polvo de hornear"), ("Almacén", "premezcla-bizcochuelo", "Bizcochuelo en caja"),
 ("Almacén", "gelatina", "Gelatina / flan"), ("Almacén", "arroz-integral", "Arroz integral"),
 ("Almacén", "granola", "Granola"), ("Almacén", "tostadas", "Tostadas"),
 ("Almacén", "budin", "Budín"), ("Almacén", "pan-hamburguesa", "Pan de hamburguesa (x4)"),
 ("Almacén", "pan-pancho", "Pan de pancho (x6)"), ("Almacén", "maiz-blanco", "Maíz blanco p/ locro"),
 ("Almacén", "porotos", "Porotos"), ("Almacén", "dulce-membrillo", "Dulce de membrillo"),
 ("Almacén", "galletitas-chocolinas", "Galletitas Chocolinas"),
 ("Bebidas", "gaseosa-coca-15", "Coca-Cola 1.5L"), ("Bebidas", "gaseosa-coca-zero-225", "Coca-Cola Zero 2.25L"),
 ("Bebidas", "gaseosa-coca-zero-15", "Coca-Cola Zero 1.5L"), ("Bebidas", "gaseosa-coca-lata", "Coca-Cola lata 354ml"),
 ("Bebidas", "gaseosa-sprite-225", "Sprite 2.25L"), ("Bebidas", "gaseosa-sprite-zero", "Sprite Zero 2.25L"),
 ("Bebidas", "gaseosa-fanta-225", "Fanta naranja 2.25L"), ("Bebidas", "agua-con-gas", "Agua con gas 2L"),
 ("Bebidas", "soda", "Soda sifón 2L"), ("Bebidas", "jugo-listo", "Jugo listo Cepita 1L"),
 ("Bebidas", "vino-tinto", "Vino tinto malbec 750ml"), ("Bebidas", "fernet", "Fernet 750ml"),
 ("Desayuno y merienda", "leche-descremada", "Leche descremada larga vida 1L (adultos)"),
 ("Desayuno y merienda", "te-saquitos", "Té en saquitos (x50)"), ("Desayuno y merienda", "mate-cocido", "Mate cocido (x50)"),
 ("Limpieza y hogar", "jabon-polvo", "Jabón en polvo p/ lavarropas"), ("Limpieza y hogar", "desodorante-ambiente", "Desodorante de ambientes"),
 ("Limpieza y hogar", "limpiador-pisos", "Limpiador de pisos (Procenex)"), ("Limpieza y hogar", "lustramuebles", "Lustramuebles"),
 ("Limpieza y hogar", "insecticida", "Insecticida"), ("Limpieza y hogar", "film-cocina", "Film adherente"),
 ("Limpieza y hogar", "papel-aluminio", "Papel aluminio"), ("Limpieza y hogar", "servilletas", "Servilletas"),
 ("Limpieza y hogar", "panuelos-descartables", "Pañuelos descartables"),
 ("Perfumería e higiene", "acondicionador", "Acondicionador"), ("Perfumería e higiene", "desodorante", "Desodorante personal"),
 ("Perfumería e higiene", "afeitadoras", "Afeitadoras descartables"), ("Perfumería e higiene", "protector-solar", "Protector solar"),
 ("Perfumería e higiene", "algodon", "Algodón"), ("Perfumería e higiene", "repelente", "Repelente"),
 ("Perfumería e higiene", "cepillo-dientes", "Cepillos de dientes"), ("Perfumería e higiene", "pasta-dental-infantil", "Pasta dental infantil"),
 ("Perfumería e higiene", "shampoo-ninos", "Shampoo para chicos"),
 ("Bebé", "panales-xg", "Pañales talle XG (pack)"), ("Bebé", "oleo-calcareo", "Óleo calcáreo"),
 ("Bebé", "crema-paspaduras", "Crema para paspaduras"), ("Bebé", "jabon-liquido-bebe", "Jabón líquido de bebé"),
 ("Bebé", "leche-crecimiento", "Leche de crecimiento"),
]

# --- reconstruir categorías en orden ---
ORDEN = ["Carnicería", "Verdulería y frutas", "Heladera", "Almacén", "Desayuno y merienda",
         "Bebidas", "Limpieza y hogar", "Perfumería e higiene", "Bebé"]
nuevas = {n: [] for n in ORDEN}
for c in ing["categorias"]:
    for it in c["items"]:
        cat = c["nombre"]
        if it["id"] in A_HELADERA: cat = "Heladera"
        elif it["id"] in A_DESAYUNO: cat = "Desayuno y merienda"
        elif cat == "Fiambrería y lácteos": cat = "Heladera" if it["id"] != "huevos" else "Almacén"
        if cat not in nuevas: cat = "Almacén"
        nuevas.setdefault(cat, []).append(it)
# renombrar leche
for it in nuevas["Desayuno y merienda"]:
    if it["id"] == "leche":
        it["nombre"] = "Leche entera larga vida 1L (chicos)"
# agregar nuevos (sin duplicar)
existentes = {it["id"] for lst in nuevas.values() for it in lst}
for cat, iid, nombre in NUEVOS:
    if iid in existentes: continue
    nuevas[cat].append({"id": iid, "nombre": nombre, "cantidad_mes": "a elección", "unidad_precio": "por unidad", "busqueda": iid})
ing["categorias"] = [{"nombre": n, "items": nuevas[n]} for n in ORDEN if nuevas.get(n)]
with open(os.path.join(BASE, "ingredientes.json"), "w", encoding="utf-8") as f:
    json.dump(ing, f, ensure_ascii=False, indent=1)
for n in ORDEN:
    print(n, len(nuevas.get(n, [])))
print("total:", sum(len(v) for v in nuevas.values()))
