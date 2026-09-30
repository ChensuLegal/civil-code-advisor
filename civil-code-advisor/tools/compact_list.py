#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 candidates.tsv 压成紧凑清单（仅有效件，标题截断），供人工圈定入库范围。"""
import io
import os
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'out', 'inventory', 'candidates.tsv')
OUT = os.path.join(ROOT, 'out', 'inventory', 'compact.txt')

rows = []
with io.open(SRC, encoding='utf-8') as f:
    head = f.readline().rstrip('\n').split('\t')
    for line in f:
        rows.append(dict(zip(head, line.rstrip('\n').split('\t'))))

out = io.open(OUT, 'w', encoding='utf-8')
by = collections.defaultdict(list)
for r in rows:
    by[r['bucket']].append(r)
for b in sorted(by):
    act = [r for r in by[b] if r['status'] == '有效']
    out.write('\n######## %s  有效%d/共%d\n' % (b, len(act), len(by[b])))
    for r in sorted(act, key=lambda x: (-int(x['mfd_refs'] or 0), x['eff'])):
        t = r['title'].replace('最高人民法院关于', '').replace('关于', '')
        out.write('  %s | %s | 条%-4s 字%-6s 民法典%-3s | %s\n' %
                  ((r['eff'] or '--------')[:10], (r['fashi'] or '').ljust(14),
                   r['tiao'], r['chars'], r['mfd_refs'], t[:46]))
out.close()
print('ok')
