#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查民法典源文件的行结构，供解析器校正。"""
import io
import os
import re
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with io.open(os.path.join(ROOT, 'index.tsv'), encoding='utf-8') as f:
    head = f.readline().rstrip('\n').split('\t')
    recs = [dict(zip(head, l.rstrip('\n').split('\t'))) for l in f]
m = [r for r in recs if r['layer'] == '法律' and r['title'] == '中华人民共和国民法典']
out = io.open(os.path.join(ROOT, 'out_mfd_probe.txt'), 'w', encoding='utf-8')
out.write('matches=%d\n' % len(m))
if not m:
    out.write('\n'.join(r['title'] for r in recs if r['layer'] == '法律' and '民法典' in r['title'])[:3000])
    out.close()
    raise SystemExit(0)
p = os.path.join(ROOT, m[0]['path'].replace('/', os.sep))
raw = io.open(p, encoding='utf-8').read()
body = re.split(r'^---\n', raw, maxsplit=2)[-1]
io.open(os.path.join(ROOT, 'out_mfd_raw.txt'), 'w', encoding='utf-8').write(body)
lines = body.split('\n')
out.write('meta: %s\n' % {k: m[0][k] for k in ('id', 'status', 'pub_date', 'eff_date', 'author')})
out.write('body_chars=%d lines=%d\n\n=== first 40 lines ===\n' % (len(body), len(lines)))
out.write('\n'.join(lines[:40]))
c = collections.Counter()
for l in lines:
    s = l.strip()
    if not s:
        continue
    if s.startswith('#'):
        c['md_heading'] += 1
    if re.match(r'^\*\*第.{1,8}编', s):
        c['bold_bian'] += 1
    if re.match(r'^第.{1,8}编', s):
        c['plain_bian'] += 1
    if re.match(r'^\*\*第.{1,8}章', s):
        c['bold_zhang'] += 1
    if re.match(r'^\*\*第.{1,8}条', s):
        c['bold_tiao'] += 1
    if re.match(r'^第.{1,8}条', s):
        c['plain_tiao'] += 1
    if s.startswith('>'):
        c['quote'] += 1
out.write('\n\n=== pattern counts ===\n%s\n' % dict(c))
out.write('\n=== sample bold_tiao lines ===\n')
n = 0
for l in lines:
    if re.match(r'^\*\*第.{1,8}条', l.strip()):
        out.write(l.strip()[:120] + '\n')
        n += 1
        if n >= 6:
            break
out.write('\n=== md_heading samples ===\n')
n = 0
for l in lines:
    if l.strip().startswith('#'):
        out.write(l.strip()[:80] + '\n')
        n += 1
        if n >= 20:
            break
out.close()
print('ok')
