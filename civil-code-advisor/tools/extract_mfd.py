#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽取《中华人民共和国民法典》全文，按 编/分编/章/节/条 五级结构化。

产出（out/mfd/）：
  民法典_全文.md        逐条重排全文（编为一级、分编/章/节为下级标题）
  articles.jsonl        逐条 JSON：no/label/part/subpart/chapter/section/text/chars
  民法典_01_总则编.md …  分编文件（7 编 + 附则）
stdout 打印 ASCII 校验统计（条数、缺号、重复、各编条数）。
"""
import io
import os
import re
import json
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'out_mfd_raw.txt')
OUTDIR = os.path.join(ROOT, 'out', 'mfd')
CN = '零〇一二三四五六七八九十百千'

TIAO_RE = re.compile(r'^-\s*\*\*(第[%s]+条)\*\*\s*\u3000*\s*(.*)$' % CN)
ITEM_RE = re.compile(r'^[（(][一二三四五六七八九十]+[）)]')
H_RE = re.compile(r'^(#{2,6})\s*(.+?)\s*$')
PART_RE = re.compile(r'^第[%s]+编(?!.*分编)' % CN)
SUBPART_RE = re.compile(r'^第[%s]+分编' % CN)
CHAP_RE = re.compile(r'^第[%s]+章' % CN)
SEC_RE = re.compile(r'^第[%s]+节' % CN)
AZH = {c: i for i, c in enumerate('一二三四五六七')}


def cn2int(s):
    digits = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
              '六': 6, '七': 7, '八': 8, '九': 9}
    units = {'十': 10, '百': 100, '千': 1000}
    total = num = 0
    for ch in s.replace('〇', '零').replace('○', '零'):
        if ch in digits:
            num = digits[ch]
        elif ch in units:
            total += (num or 1) * units[ch]
            num = 0
        else:
            return None
    return total + num


def norm(s):
    s = s.replace('\u3000', ' ').replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', s).strip()


def tight(s):
    return re.sub(r'\s+', '', s)


def parse():
    raw = io.open(SRC, encoding='utf-8').read()
    if raw.startswith('id:') or raw.startswith('title:'):
        raw = raw.split('\n---\n', 1)[-1]
    lines = raw.split('\n')
    start = None
    for i, l in enumerate(lines):
        m = H_RE.match(l.strip())
        if m and PART_RE.match(tight(norm(m.group(2)))):
            start = i
            break
    if start is None:
        raise SystemExit('body start not found')

    part = subpart = chapter = section = ''
    articles, cur, buf = [], None, []
    for l in lines[start:]:
        st = l.strip()
        if not st:
            continue
        m = H_RE.match(st)
        if m:
            t = tight(norm(m.group(2)))
            if PART_RE.match(t):
                part, subpart, chapter, section = t, '', '', ''
            elif SUBPART_RE.match(t):
                subpart, chapter, section = t, '', ''
            elif CHAP_RE.match(t):
                chapter, section = t, ''
            elif SEC_RE.match(t):
                section = t
            else:
                part, subpart, chapter, section = t, '', '', ''
            continue
        m = TIAO_RE.match(st)
        if m:
            if cur:
                finish(cur, buf)
                articles.append(cur)
            label = m.group(1)
            cur = {'no': cn2int(label[1:-1]), 'label': label, 'part': part,
                   'subpart': subpart, 'chapter': chapter, 'section': section,
                   'text': '', 'chars': 0}
            buf = [m.group(2)]
        elif cur is not None:
            s = re.sub(r'^[-*]\s*', '', st)
            if s:
                buf.append(s)
    if cur:
        finish(cur, buf)
        articles.append(cur)
    return articles


def finish(cur, buf):
    """buf 为逐段列表（第1段=第1款，其余为后续款/项）；同时保留扁平 text 便于全文检索。"""
    paras = [norm(b) for b in buf if norm(b)]
    cur['paras'] = paras
    cur['text'] = norm(' '.join(paras))
    cur['chars'] = len(cur['text'])


HEADER = ('> 制定机关：全国人民代表大会　通过：2020-05-28 十三届全国人大三次会议　'
          '施行：2021-01-01　效力：现行有效\n'
          '> 来源：国家法律法规数据库 flk.npc.gov.cn/detail?id=ff808081729d1efe01729d50b5c500bf'
          '（lawtext/laws 镜像，逐条重排，未经删改）\n')


def render(items, title):
    o = io.StringIO()
    o.write('# %s\n\n%s\n' % (title, HEADER))
    cur = {'part': None, 'subpart': None, 'chapter': None, 'section': None}
    order = ('part', 'subpart', 'chapter', 'section')
    for a in items:
        for i, key in enumerate(order):
            val = a.get(key) or ''
            if cur[key] == val:
                continue
            lvl = i + 2
            if val:
                o.write('\n%s %s\n\n' % ('#' * lvl, val))
            cur[key] = val
            for deeper in order[i + 1:]:      # 上层变化时重置下层，保证重复章名也打印
                cur[deeper] = None if not a.get(deeper) else object()
        paras = a.get('paras') or [a['text']]
        o.write('**%s**　%s\n' % (a['label'], paras[0]))
        for p in paras[1:]:
            if ITEM_RE.match(p):
                o.write('- %s\n' % p)
            else:
                o.write('\n%s\n' % p)
        o.write('\n')
    return o.getvalue()


def main():
    articles = parse()
    nums = [a['no'] for a in articles]
    missing = sorted(set(range(1, 1261)) - set(nums))
    dup = [n for n, c in collections.Counter(nums).items() if c > 1]
    print('articles=%d min=%s max=%s missing=%d dup=%d chars=%d' %
          (len(articles), min(nums), max(nums), len(missing), len(dup),
           sum(a['chars'] for a in articles)))
    per = collections.OrderedDict()
    for a in articles:
        per.setdefault(a['part'], []).append(a)
    for p, items in per.items():
        print('  %-14s n=%4d %s..%s chars=%6d' %
              (p.encode('unicode_escape').decode()[:14], len(items),
               items[0]['label'].encode('unicode_escape').decode()[:14],
               items[-1]['label'].encode('unicode_escape').decode()[:14],
               sum(i['chars'] for i in items)))
    os.makedirs(OUTDIR, exist_ok=True)
    with io.open(os.path.join(OUTDIR, 'articles.jsonl'), 'w', encoding='utf-8') as f:
        for a in articles:
            f.write(json.dumps(a, ensure_ascii=False) + '\n')
    with io.open(os.path.join(OUTDIR, '民法典_全文.md'), 'w', encoding='utf-8') as f:
        f.write(render(articles, '中华人民共和国民法典（全文·逐条重排版）'))
    for idx, (p, items) in enumerate(per.items(), 1):
        slug = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]', '', p)
        fn = os.path.join(OUTDIR, '民法典_%02d_%s.md' % (idx, slug))
        with io.open(fn, 'w', encoding='utf-8') as f:
            f.write(render(items, '中华人民共和国民法典 · %s' % p))
    print('files=%d -> %s' % (len(per) + 2, OUTDIR))


if __name__ == '__main__':
    main()
