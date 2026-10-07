# La Compra del Mes

Página publicada: https://softech-v.github.io/compra-del-mes/ (index.html, con todos los datos embebidos en `GROCERY_DATA`).

- `tools/` — refresco de precios actual (07/10/2026): `refresh_vtex.py` (Carrefour/Día/Jumbo por SKU), `retry_cf.py`, `refresh_coto.py` (fichas Coto `?format=json`), `retry_coto.py`, `apply_refresh.py` (aplica sobre index.html, backup, fecha, historial.prev).
- `backups/` — copia de index.html antes de cada refresco (una por fecha).
- `scripts_recuperados/` — scripts del pipeline viejo (agosto/septiembre 2026) rescatados de las transcripciones; de referencia, dependen de JSON fuente que ya no existen.

Copia de trabajo local: `C:\Users\ncort\compra-del-mes` (clon de este repo en `deploy/`).
