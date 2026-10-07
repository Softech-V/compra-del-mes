# -*- coding: utf-8 -*-
import json, re, collections, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
f = "C:/Users/ncort/.claude/projects/C--Users-ncort-Ads-Analytics-para-VSC-dashboard-reporting/7d404d61-4350-449a-ba38-19455fe041ac.jsonl"
cands = []
urls = collections.Counter()
pat = re.compile(r'https?://(?:www\.)?cotodigital\.com\.ar/[^\s"\\\'<>]{0,160}')
for line in open(f, encoding="utf-8", errors="ignore"):
    for u in pat.findall(line):
        urls[re.sub(r'\d{3,}', 'N', u)[:120]] += 1
    if "cotodigital" not in line:
        continue
    try:
        o = json.loads(line)
    except Exception:
        continue
    for c in (o.get("message", {}).get("content") or []):
        if isinstance(c, dict) and c.get("type") == "tool_use":
            s = c["input"].get("content") or c["input"].get("command") or ""
            if "cotodigital" in s and "def " in s and ("urlopen" in s or "requests" in s or "http" in s):
                cands.append((c["name"], len(s), s))
print("candidatos:", [(n, l) for n, l, _ in cands])
for u, n in urls.most_common(30):
    print(n, u)
if cands:
    n, l, s = max(cands, key=lambda x: x[1])
    open("C:/Users/ncort/compra-del-mes/scripts_recuperados/scrape_coto_src.txt", "w", encoding="utf-8").write(s)
    print("=====")
    print(s[:7000])
