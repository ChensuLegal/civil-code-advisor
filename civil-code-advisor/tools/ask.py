#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""条文问答：python tools/ask.py 1254   或   python tools/ask.py 第六百八十六条

一次给出：民法典原文（分款）+ 蒸馏卡片 + 哪些司法解释引用了它 + 覆盖统计。
"""
import io
import os
import re
import sys
import json
import glob

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CN = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}


def cn2int(s):
    if s.isdigit():
        return int(s)
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


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    arg = sys.argv[1].strip()
    m = re.search(r'(\d+|第?[一二三四五六七八九十百千零]+条)', arg)
    txt = m.group(1) if m else arg
    no = cn2int(txt.replace('第', '').replace('条', '')) if not txt.isdigit() else int(txt)
    if not no or not 1 <= no <= 1260:
        print('无法识别条号：%s' % arg)
        return
    art = None
    for line in io.open(os.path.join(ROOT, 'corpus', 'mfd', 'articles.jsonl'), encoding='utf-8'):
        a = json.loads(line)
        if a['no'] == no:
            art = a
            break
    label = '第%s条' % txt.replace('第', '').replace('条', '') if txt.isdigit() else txt
    if txt.isdigit():
        for line in io.open(os.path.join(ROOT, 'corpus', 'mfd', 'articles.jsonl'), encoding='utf-8'):
            a = json.loads(line)
            if a['no'] == no:
                label = a['label']
                break
    print('=' * 70)
    print('%s　（%s）' % (label, '｜'.join(
        [x for x in (art['part'], art.get('subpart'), art['chapter'], art['section']) if x]) if art else ''))
    print('=' * 70)
    if art:
        if len(art['paras']) > 1:
            for i, p in enumerate(art['paras'], 1):
                print('  第%d款  %s' % (i, p))
        else:
            print('  ' + art['text'])
    print('\n--- 蒸馏卡片 ---')
    head_rx = re.compile(r'^###\s+第(\d+|[一二三四五六七八九十百千零]{1,8})条')
    found = False
    for p in sorted(glob.glob(os.path.join(ROOT, 'distill', '要件卡片', '*.md'))):
        blk, keep = [], False
        for line in io.open(p, encoding='utf-8'):
            m = head_rx.match(line)
            if m:
                if keep:
                    break
                num = m.group(1)
                keep = (int(num) if num.isdigit() else cn2int(num)) == no
                if keep:
                    blk.append(line.rstrip())
            elif keep:
                blk.append(line.rstrip())
        if keep:
            print('\n'.join(blk).rstrip())
            print('（源文件：%s）' % os.path.basename(p))
            found = True
            break
    if not found:
        print('  未找到该条卡片。')
    print('\n--- 引用了本条的司法解释（原文明示）---')
    n = 0
    for line in io.open(os.path.join(ROOT, 'index', 'xref_mfd.tsv'), encoding='utf-8'):
        c = line.rstrip('\n').split('\t')
        if len(c) >= 4 and c[0] == str(no):
            n += 1
            print('  [%s %s] %s' % (c[1][:22], c[2], c[3][:70]))
    if not n:
        print('  无明示援引；请到 distill/要件卡片/ 对应卡片的「配套解释」行看功能对应，'
              '并按 SKILL.md「引用前三查」核对解释原文。')
    docs = sorted(set(l.split('\t')[1] for l in io.open(os.path.join(ROOT, 'index', 'xref_mfd.tsv'),
                                                       encoding='utf-8')
                      if l.startswith(str(no) + '\t')))
    if docs:
        print('  涉及解释文件：%s' % ', '.join(docs))


if __name__ == '__main__':
    main()
