#!/bin/bash
cd /c/Users/ncort/compra-del-mes
echo "INICIO $(date +%H:%M:%S)"
python tools/refresh_vtex.py && python tools/retry_cf.py && python tools/refresh_coto.py && python tools/retry_coto.py
echo "FIN $? $(date +%H:%M:%S)"
