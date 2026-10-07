# -*- coding: utf-8 -*-
"""07/09 frontend: promos NxM / 2da al X% en el costo, precio por unidad real (pack/meas),
desplegable de tamaños elige por defecto el menor precio por cantidad, etiqueta del pack."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
p = "compra-del-mes.html"
h = open(p, encoding="utf-8").read()
if "function promoDeal(" in h:
    print("HTML ya parcheado"); sys.exit(0)

def rep(old, new, count=1):
    global h
    assert h.count(old) == count, (h.count(old), old[:80])
    h = h.replace(old, new)

# 1) costo con promos NxM y "2da al X%"
rep('''  function costItem(it, qty, storeKey) {
    const p = it.precios[storeKey];
    if (!p || p.precio == null || qty <= 0) return null;
    return it.kind === 'bulk' ? p.precio / p.size * qty : Math.ceil(qty / p.size - 1e-9) * p.precio;
  }''',
'''  // promo por producto: {n, pay} = llevando n unidades se pagan pay (2x1 -> {2,1}; 3x2 -> {3,2}; 2da al 70% -> {2,1.3})
  function promoDeal(p) {
    if (!p || !p.promo) return null;
    const s = String(p.promo).toLowerCase();
    let m = s.match(/(\\d+)\\s?x\\s?(\\d+)/);
    if (m && +m[1] > +m[2] && +m[2] > 0) return { n: +m[1], pay: +m[2] };
    m = s.match(/2d[ao]\\s*(?:al|a)\\s*(\\d+)\\s?%/) || s.match(/(\\d+)\\s?%\\s*(?:en\\s+la\\s+|la\\s+)?2d[ao]/);
    if (m && +m[1] > 0 && +m[1] <= 100) return { n: 2, pay: 1 + (1 - (+m[1]) / 100) };
    return null;
  }
  const effPrice = p => { const d = promoDeal(p); return d ? p.precio * d.pay / d.n : p.precio; };
  function costItem(it, qty, storeKey) {
    const p = it.precios[storeKey];
    if (!p || p.precio == null || qty <= 0) return null;
    if (it.kind === 'bulk') return p.precio / p.size * qty;
    const packs = Math.ceil(qty / p.size - 1e-9);
    const d = promoDeal(p);
    return d ? (Math.floor(packs / d.n) * d.pay + (packs % d.n)) * p.precio : packs * p.precio;
  }''')

# 2) precio por cantidad real
rep('''  function unitPriceTxt(it, p) {
    if (!p || !p.size) return '';
    let v, suf;
    if (it.unit === 'g') { v = p.precio / p.size * 1000; suf = '/kg'; }
    else if (it.unit === 'ml') { v = p.precio / p.size * 1000; suf = '/L'; }
    else { v = p.precio / p.size; suf = '/un'; }
    return '$' + Math.round(v).toLocaleString('es-AR') + suf;
  }''',
'''  // cantidad normalizada de una fila de precio: {v, u} en g / ml / un
  function normQty(it, p) {
    if (!p) return null;
    if (it.unit === 'g' || it.unit === 'ml') return p.size ? { v: p.size, u: it.unit } : null;
    if (p.meas && p.meas.v) return { v: p.meas.v, u: p.meas.u };
    if (p.pack > 1) return { v: p.pack, u: 'un' };
    return { v: p.size || 1, u: 'un', envase: true };
  }
  // precio efectivo (con promo) por kg / L / unidad; null si no se puede
  function perQty(it, p) {
    const q = normQty(it, p);
    if (!q || !q.v || p.precio == null) return null;
    const pr = effPrice(p);
    return { v: q.u === 'un' ? pr / q.v : pr / q.v * 1000, u: q.u, envase: !!q.envase };
  }
  function unitPriceTxt(it, p) {
    const r = perQty(it, p);
    if (!r) return '';
    const suf = r.u === 'g' ? '/kg' : r.u === 'ml' ? '/L' : '/un';
    const d = promoDeal(p);
    return '$' + Math.round(r.v).toLocaleString('es-AR') + suf + (p.pack > 1 && r.u === 'un' ? ' (' + p.pack + ' un)' : '') + (d ? ' c/promo' : '');
  }
  // entre tamaños de un mismo producto: el de menor precio por cantidad (mejor tienda visible, promos incluidas)
  function cheapestMember(members) {
    const rows = [];
    members.forEach(m => {
      let best = null;
      SVIS().forEach(s => { const r = perQty(m, m.precios[s.key]); if (r && !r.envase && (best == null || r.v < best.v)) best = r; });
      if (best) rows.push({ m, v: best.v, u: best.u });
    });
    if (!rows.length) return null;
    const cnt = {}; rows.forEach(r => { cnt[r.u] = (cnt[r.u] || 0) + 1; });
    const u = Object.keys(cnt).sort((a, b) => cnt[b] - cnt[a])[0];
    const cand = rows.filter(r => r.u === u).sort((a, b) => a.v - b.v);
    return cand.length ? cand[0].m : null;
  }''')

# 3) selección por defecto en el desplegable
rep('''          it = members.find(m => m.id === selId) || (query ? members.find(m => matches(m)) : null) || members.find(m => S.prod[m.id]) || members[0];''',
'''          it = members.find(m => m.id === selId) || (query ? members.find(m => matches(m)) : null) || members.find(m => S.prod[m.id]) || cheapestMember(members) || members[0];''')

# 4) etiqueta del tamaño: si es un pack de N unidades sin medida en g/ml, mostrar "N un"
rep('''  function sizeLabel(it) {
    const pr = presOf(it);''',
'''  function sizeLabel(it) {
    const pr = presOf(it);
    const pk = Math.max(0, ...Object.values(it.precios).map(p => (p && p.pack) || 0));
    if (pk > 1 && !/\\d\\s*(kg|g|gr|grs|ml|cc|l|lt|lts)\\b/i.test(pr)) return pk + ' un';''')

open(p, "w", encoding="utf-8").write(h)
print("HTML parcheado: promoDeal/effPrice, normQty/perQty, unitPriceTxt, cheapestMember, sizeLabel")
