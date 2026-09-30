#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验收：核对蒸馏层覆盖计数与民法典条文全量映射，输出 index/verify.txt。"""
import io
import os
import re
import glob
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(ROOT, 'skill_out')
out = io.open(os.path.join(SK, 'index', 'verify.txt'), 'w', encoding='utf-8')

TIT = re.compile(r'^###\s+第(\d{1,4}|[一二三四五六七八九十百千零]{1,8})条')
CN = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}


def cn2int(s):
    total = num = 0
    for ch in s:
        if ch in CN:
            num = CN[ch]
        elif ch == '十':
            total += (num or 1) * 10
            num = 0
        elif ch == '百':
            total += (num or 1) * 100
            num = 0
        elif ch == '千':
            total += (num or 1) * 1000
            num = 0
    return total + num


seen = collections.Counter()
files = sorted(glob.glob(os.path.join(SK, 'distill', '要件卡片', '*.md')))
out.write('== 要件卡片逐文件计数 ==\n')
for p in files:
    n = 0
    for line in io.open(p, encoding='utf-8'):
        m = TIT.match(line)
        if m:
            g = m.group(1)
            seen[int(g) if g.isdigit() else cn2int(g)] += 1
            n += 1
    out.write('  %-46s %4d 条\n' % (os.path.basename(p).encode('unicode_escape').decode()[:46], n))
nums = set(seen)
missing = sorted(set(range(1, 1261)) - nums)
dup = {k: v for k, v in seen.items() if v > 1}
out.write('覆盖 %d/1260，缺 %d，重复 %d\n' % (len(nums), len(missing), len(dup)))
if missing:
    out.write('缺号: %s\n' % missing[:40])
if dup:
    out.write('重复: %s\n' % list(dup.items())[:20])

out.write('\n== 其他蒸馏文件行数与条目 ==\n')
for sub in ['解释速查', '请求权基础', '衔接适用']:
    for p in sorted(glob.glob(os.path.join(SK, 'distill', sub, '*.md'))):
        t = io.open(p, encoding='utf-8').read()
        lines = [l for l in t.split('\n') if l.strip()]
        items = len(re.findall(r'^##\s', t, re.M)) + len(re.findall(r'^-\s+解释第', t, re.M))
        out.write('  %-14s %-40s 非空行%5d 条目%4d 字%6d\n' % (
            sub, os.path.basename(p).encode('unicode_escape').decode()[:40],
            len(lines), items, len(t)))

out.write('\n== 卡片字段完整度（要件卡片） ==\n')
tot = {'功能': 0, '规则': 0, '配套解释': 0, '要件': 0, '效果': 0, '易错': 0, '举证': 0}
for p in files:
    t = io.open(p, encoding='utf-8').read()
    for k in tot:
        tot[k] += len(re.findall(r'^-\s*\*{0,2}%s' % k, t, re.M))
out.write('  %s（卡片总数 %d）\n' % (tot, len(seen)))

out.write('\n== 语料层 ==\n')
out.write('  corpus/ssjf %d 件, corpus/mfd %d 件, corpus/cankao %d 件\n' % (
    len(glob.glob(os.path.join(SK, 'corpus', 'ssjf', '*.md'))),
    len(glob.glob(os.path.join(SK, 'corpus', 'mfd', '*'))),
    len(glob.glob(os.path.join(SK, 'corpus', 'cankao', '*.md')))))
out.write('  index/articles_all.jsonl 条文 %d 行\n' % sum(
    1 for _ in io.open(os.path.join(SK, 'index', 'articles_all.jsonl'), encoding='utf-8')))
out.close()
print('cards=%d missing=%d dup=%d' % (len(nums), len(missing), len(dup)))
