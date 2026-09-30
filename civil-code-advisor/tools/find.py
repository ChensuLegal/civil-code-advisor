#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨层关键词检索：python tools/find.py 高空抛物 [上限条数]"""
import io
import os
import re
import sys
import glob

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYERS = [('要件卡片', ['distill/要件卡片/*.md']),
          ('解释速查', ['distill/解释速查/*.md']),
          ('请求权基础', ['distill/请求权基础/*.md']),
          ('衔接适用', ['distill/衔接适用/*.md']),
          ('民法典', ['corpus/mfd/民法典_全文.md']),
          ('司法解释', ['corpus/ssjf/*.md']),
          ('参考层', ['corpus/cankao/*.md'])]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    kw = sys.argv[1]
    lim = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    rx = re.compile(kw)
    shown = 0
    for name, patterns in LAYERS:
        hits = []
        for pat in patterns:
            for p in glob.glob(os.path.join(ROOT, pat)):
                for i, line in enumerate(io.open(p, encoding='utf-8', errors='replace'), 1):
                    if rx.search(line):
                        hits.append((os.path.basename(p), i, line.strip()[:150]))
                        if len(hits) >= 8:
                            break
                    if len(hits) >= 8:
                        break
        if hits:
            print('\n### %s（显示前%d条命中）' % (name, len(hits)))
            for fn, i, s in hits:
                print('  %s:%d  %s' % (fn, i, s))
                shown += 1
        if shown >= lim:
            print('\n（已达上限 %d，加参数放宽或用更精确关键词）' % lim)
            return


if __name__ == '__main__':
    main()
