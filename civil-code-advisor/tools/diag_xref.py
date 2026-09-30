#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断引用锚点为何偏低：统计各文件的引用写法分布。"""
import io
import os
import re
import glob
import collections
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, 'skill_out')
rows = [json.loads(l) for l in io.open(os.path.join(SKILL, 'index', 'articles_all.jsonl'), encoding='utf-8')]
out = io.open(os.path.join(ROOT, 'out_xref_diag.txt'), 'w', encoding='utf-8')

pats = {
    '民法典第X条': re.compile(r'民法典\s*第[一二三四五六七八九十百千零]{1,8}条'),
    '《中华人民共和国民法典》': re.compile(r'《中华人民共和国民法典》'),
    '本法第X条': re.compile(r'本法\s*第[一二三四五六七八九十百千零]{1,8}条'),
    '本解释第X条': re.compile(r'本解释\s*第[一二三四五六七八九十百千零]{1,8}条'),
    '裸第X条规定': re.compile(r'第[一二三四五六七八九十百千零]{1,8}条\s*的规定'),
    '其他法律第X条': re.compile(r'第[一二三四五六七八九十百千零]{1,8}条第[一二三四五六七八九十]{1,2}款'),
}
tot = collections.Counter()
for r in rows:
    for k, p in pats.items():
        tot[k] += len(p.findall(r['text']))
out.write('解释条文总数=%d\n' % len(rows))
for k, v in tot.items():
    out.write('  %-24s %d\n' % (k, v))

out.write('\n=== T1 各文件引用写法分布 ===\n')
byfile = collections.defaultdict(collections.Counter)
for r in rows:
    for k, p in pats.items():
        byfile[r['file']][k] += len(p.findall(r['text']))
for fn in sorted(byfile):
    if fn.startswith('T1'):
        out.write('  %s  %s\n' % (fn, dict(byfile[fn])))

out.write('\n=== 抽样：含“民法典”字样的解释条（前12条）===\n')
n = 0
for r in rows:
    if '民法典第' in r['text'] and n < 12:
        out.write('  [%s %s] %s\n' % (r['file'][:14], r['label'], r['text'][:160]))
        n += 1
out.write('\n=== 抽样：担保制度解释前6条全文 ===\n')
for r in rows:
    if '担保制度' in r['doc'] and r['no'] and r['no'] <= 6:
        out.write('  %s %s\n' % (r['label'], r['text'][:300]))
out.close()
print('ok', dict(tot))
