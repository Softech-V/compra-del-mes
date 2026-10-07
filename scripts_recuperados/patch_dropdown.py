# -*- coding: utf-8 -*-
"""Agrega al frontend el desplegable de tamaños por grupo de producto."""
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(BASE, "compra-del-mes.html")
s = open(p, encoding="utf-8").read()

# 1) CSS
css_anchor = "  .pcard .row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }"
assert css_anchor in s
s = s.replace(css_anchor, css_anchor + """
  .pcard select.sz { font-size: 12px; padding: 3px 6px; border-radius: 7px; border: 1px solid var(--line); background: var(--surface-2); color: var(--ink); max-width: 100%; }
  .pcard .szrow { display: flex; align-items: center; gap: 6px; font-size: 11.5px; color: var(--muted); flex-wrap: wrap; }
  .pcard .otros { font-size: 11px; color: var(--accent, #4caf7d); }""", 1)

# 2) estado S.sel
old_state = "  S.tengo = S.tengo || {};"
assert old_state in s
s = s.replace(old_state, old_state + "\n  S.sel = S.sel || {};", 1)

# 3) render con clusters
old_start = """      const items = standalone.filter(i => i.cat === c && matches(i));
      if (!items.length) return;
      const grid = document.createElement('div'); grid.className = 'grid';
      let activos = 0;
      items.forEach(it => {
        const n = S.prod[it.id] || 0;
        if (n) activos++;"""
new_start = """      const all = standalone.filter(i => i.cat === c);
      const items = all.filter(matches);
      if (!items.length) return;
      const grid = document.createElement('div'); grid.className = 'grid';
      let activos = 0;
      // agrupar tamaños del mismo producto en una sola tarjeta
      const clusters = [], seen = {};
      all.forEach(i => {
        if (i.grupo) { if (seen[i.grupo]) { seen[i.grupo].push(i); return; } seen[i.grupo] = [i]; clusters.push(seen[i.grupo]); }
        else clusters.push([i]);
      });
      clusters.forEach(members => {
        if (!members.some(matches)) return;
        let it = members[0];
        if (members.length > 1) {
          members.sort((a, b) => sizeOf(a) - sizeOf(b));
          const selId = S.sel[it.grupo];
          it = members.find(m => m.id === selId) || (query ? members.find(m => matches(m)) : null) || members.find(m => S.prod[m.id]) || members[0];
        }
        const n = S.prod[it.id] || 0;
        members.forEach(m => { if (S.prod[m.id]) activos++; });"""
assert old_start in s
s = s.replace(old_start, new_start, 1)

old_name = """        card.insertAdjacentHTML('beforeend', `<div class="pn">${it.nombre}</div>`);
        const row = document.createElement('div'); row.className = 'row';"""
new_name = """        card.insertAdjacentHTML('beforeend', `<div class="pn">${it.nombre}</div>`);
        if (members.length > 1) {
          const szrow = document.createElement('div'); szrow.className = 'szrow';
          szrow.append(document.createTextNode('Tamaño:'));
          const sel = document.createElement('select'); sel.className = 'sz';
          members.forEach(m => { const o = document.createElement('option'); o.value = m.id; o.textContent = sizeLabel(m) + (S.prod[m.id] ? ' ✓' : ''); if (m.id === it.id) o.selected = true; sel.append(o); });
          sel.onchange = () => { S.sel[it.grupo] = sel.value; persist(); renderProductos(); };
          szrow.append(sel);
          const otros = members.filter(m => m.id !== it.id && S.prod[m.id]);
          if (otros.length) szrow.insertAdjacentHTML('beforeend', `<span class="otros">+ ${otros.map(m => S.prod[m.id] + ' × ' + sizeLabel(m)).join(', ')} en tu compra</span>`);
          card.append(szrow);
        }
        const row = document.createElement('div'); row.className = 'row';"""
assert old_name in s
s = s.replace(old_name, new_name, 1)

# 4) helpers sizeOf / sizeLabel antes de renderProductos
helpers = """  function presOf(it) {
    const p = it.precios.carrefour || Object.values(it.precios).find(x => x);
    return (p && p.presentacion) || '';
  }
  function sizeOf(it) {
    const m = presOf(it).match(/(\\d+(?:[.,]\\d+)?)\\s*(kg|g|ml|l|un|paños|hojas)/i);
    if (!m) return 0;
    let v = parseFloat(m[1].replace(',', '.')); const u = m[2].toLowerCase();
    if (u === 'kg' || u === 'l') v *= 1000;
    return v;
  }
  function sizeLabel(it) {
    const pr = presOf(it);
    const m = pr.match(/(\\d+(?:[.,]\\d+)?)\\s*(kg|g|ml|l|un|paños|hojas)/i);
    if (!m) return pr || it.nombre.slice(0, 18);
    let v = parseFloat(m[1].replace(',', '.')); let u = m[2].toLowerCase();
    if (u === 'g' && v >= 1000) { v = v / 1000; u = 'kg'; }
    if (u === 'ml' && v >= 1000) { v = v / 1000; u = 'L'; }
    return (Math.round(v * 100) / 100).toString().replace('.', ',') + ' ' + u;
  }
  function renderProductos() {"""
assert "  function renderProductos() {" in s
s = s.replace("  function renderProductos() {", helpers, 1)
open(p, "w", encoding="utf-8").write(s)
print("frontend patch ok")
