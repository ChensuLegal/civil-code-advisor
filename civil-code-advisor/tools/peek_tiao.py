#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看民法典源文件中条文行的实际写法。"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = io.open(os.path.join(ROOT, 'out_mfd_raw.txt'), encoding='utf-8').read()
lines = raw.split('\n')
out = io.open(os.path.join(ROOT, 'out_tiao_style.txt'), 'w', encoding='utf-8')
pats = ['第一千二百六十条', '第九条', '第一百三十四条', '第一千零七十六条']
for p in pats:
    hits = [i for i, l in enumerate(lines) if p in l]
    out.write('### %s -> lines %s\n' % (p, hits[:8]))
    for i in hits[:2]:
        for j in range(max(0, i - 1), min(len(lines), i + 3)):
            out.write('   [%d] %r\n' % (j, lines[j][:150]))
    out.write('\n')
kinds = {}
for l in lines:
    s = l.strip()
    if not s:
        continue
    m = re.match(r'^(第[一二三四五六七八九十百千零]{1,8}条)', s)
    if m:
        kinds.setdefault('plain', 0)
        kinds['plain'] += 1
for k, v in kinds.items():
    out.write('%s %d\n' % (k, v))
out.write('total nonempty %d\n' % len([l for l in lines if l.strip()]))
out.close()
print('ok')
