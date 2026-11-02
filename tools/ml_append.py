# -*- coding: utf-8 -*-
"""Lee por stdin un JSON (lista de resultados de fichas ML leídas en el navegador) y lo appendea a tools/ml_new_" + TAG + ".jsonl.
Muestra el delta contra el precio actual del catálogo. Uso: python tools/ml_append.py < lote.json"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "C:/Users/ncort/compra-del-mes"
import os; TAG = os.environ.get("ML_TAG", "1110")
todo = {r["id"]: r for r in json.load(open(BASE + "/tools/ml_todo_" + TAG + ".json", encoding="utf-8"))}
rows = json.load(io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8'))
with open(BASE + "/tools/ml_new_" + TAG + ".jsonl", "a", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
        old = todo.get(r["id"], {}).get("precio")
        new = r.get("precio")
        d = f"{(new-old)/old*100:+.0f}%" if old and new else ("AGOTADO" if not new else "nuevo")
        print(f"{r['id'][:30].ljust(30)} {str(old).rjust(7)} -> {str(new).rjust(7)} {d:>8}  {(r.get('producto') or '')[:45]}")
done = sum(1 for _ in open(BASE + "/tools/ml_new_" + TAG + ".jsonl", encoding="utf-8"))
print(f"-- acumulado: {done}/{len(todo)}")
