#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建本地法库索引：解析 lawtext/laws 仓库 content/ 下所有文档的 front matter。

输出 index.tsv（制表符分隔，utf-8）：
path \t layer \t status \t author \t pub_date \t eff_date \t group \t title \t body_chars \t tiao_count \t flk_url
"""
import io
import os
import re
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, 'laws', 'content')
OUT = os.path.join(ROOT, 'index.tsv')

FM_RE = re.compile(r'^---\n(.*?)\n---\n', re.S)
TIAO_RE = re.compile(r'^(?:-\s*)?\*{0,2}(第[一二三四五六七八九十百千零〇]{1,9}条)', re.M)
ITEM_RE = re.compile(r'^\s*(?:\d+、|（[一二三四五六七八九十]+）)')


def parse_fm(block):
    d = {}
    key = None
    for line in block.split('\n'):
        m = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith(('"', "'")) and val[0] == val[-1] and len(val) > 1:
                val = val[1:-1]
            d[key] = val if val else ''
            if key == 'categories' and val:
                d['categories'] = val.strip('[]')
        elif re.match(r'^\s+-\s+(.*)$', line) and key in ('categories', 'tags', 'years', 'urls', 'keywords'):
            item = re.match(r'^\s+-\s+(.*)$', line).group(1).strip()
            d[key] = (d.get(key, '') + '|' + item).strip('|')
    return d


def main():
    rows = []
    for path in glob.glob(os.path.join(CONTENT, '*', '*.md')):
        layer = os.path.basename(os.path.dirname(path))
        raw = io.open(path, encoding='utf-8', errors='replace').read()
        m = FM_RE.match(raw)
        fm = parse_fm(m.group(1)) if m else {}
        body = raw[m.end():] if m else raw
        title = fm.get('title', '')
        if not title:
            continue
        urls = fm.get('urls', '')
        flk = urls.split('|')[0] if urls else ''
        rows.append({
            'path': os.path.relpath(path, ROOT).replace('\\', '/'),
            'layer': layer,
            'id': fm.get('id', ''),
            'status': fm.get('status', ''),
            'author': fm.get('author', ''),
            'pub_date': fm.get('publication_date', '') or fm.get('date', ''),
            'eff_date': fm.get('effective_date', ''),
            'group': fm.get('group', ''),
            'categories': fm.get('categories', ''),
            'title': title.replace('\t', ' '),
            'body_chars': len(body),
            'tiao_count': len(TIAO_RE.findall(body)),
            'flk_url': flk,
        })
    cols = ['path', 'id', 'layer', 'status', 'author', 'pub_date', 'eff_date',
            'group', 'categories', 'title', 'body_chars', 'tiao_count', 'flk_url']
    with io.open(OUT, 'w', encoding='utf-8', newline='') as f:
        f.write('\t'.join(cols) + '\n')
        for r in sorted(rows, key=lambda x: (x['layer'], x['title'])):
            f.write('\t'.join(str(r.get(c, '')) for c in cols) + '\n')
    sys.stderr.write('rows=%d -> %s\n' % (len(rows), OUT))

    # 汇总打印到 stdout（纯 ASCII，避免 cmd GBK 乱码）
    from collections import Counter
    by_layer = Counter(r['layer'] for r in rows)
    print('TOTAL %d docs' % len(rows))
    for k, v in sorted(by_layer.items()):
        st = Counter(r['status'] for r in rows if r['layer'] == k)
        print('  %-12s %5d  %s' % (k, v, dict(st)))


if __name__ == '__main__':
    main()
