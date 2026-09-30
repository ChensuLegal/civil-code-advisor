#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把民法典 articles.jsonl 按条号区间切成给子代理阅读的分片文件（纯文本，含编章节）。"""
import io
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'skill_out', 'corpus', 'mfd', 'articles.jsonl')
OUT = os.path.join(ROOT, 'out', 'mfd_chunks')
RANGES = [
    ('01_总则编_1-102', 1, 102),
    ('02_总则编_103-204', 103, 204),
    ('03_物权编_205-320', 205, 320),
    ('04_物权编_321-462', 321, 462),
    ('05_合同编通则_463-594', 463, 594),
    ('06_典型合同一_595-760', 595, 760),
    ('07a_典型合同二_761-875', 761, 875),
    ('07b_典型合同三准合同_876-988', 876, 988),
    ('08_人格权编婚姻家庭上_989-1090', 989, 1090),
    ('09_婚姻家庭下继承_1091-1163', 1091, 1163),
    ('10_侵权责任编附则_1164-1260', 1164, 1260),
]
os.makedirs(OUT, exist_ok=True)
arts = [json.loads(l) for l in io.open(SRC, encoding='utf-8')]
idx = {a['no']: a for a in arts}
for name, lo, hi in RANGES:
    o = io.open(os.path.join(OUT, name + '.txt'), 'w', encoding='utf-8')
    o.write('# 民法典 第%d条—第%d条（共%d条）\n\n' % (lo, hi, hi - lo + 1))
    n = 0
    for no in range(lo, hi + 1):
        a = idx.get(no)
        if not a:
            o.write('!! 缺失第%d条\n' % no)
            continue
        n += 1
        loc = '｜'.join([x for x in (a['part'], a.get('subpart'), a['chapter'], a['section']) if x])
        o.write('【%s】%s\n' % (a['label'], loc))
        if len(a['paras']) > 1:
            for i, p in enumerate(a['paras'], 1):
                o.write('  <%d> %s\n' % (i, p))
        else:
            o.write('  %s\n' % a['text'])
        o.write('\n')
    o.close()
    print('%s n=%d' % (name.encode('unicode_escape').decode()[:20], n))
