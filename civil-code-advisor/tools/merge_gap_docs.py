#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 out/gap_docs/ 补抓的 2026 年新件合并进语料层 corpus/ssjf/，并追加索引行。"""
import io
import os
import re
import glob
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.environ.get('SKILL_OUT') or os.path.join(ROOT, 'skill_out')
GAP = os.path.join(ROOT, 'out', 'gap_docs')
BAD = re.compile(r'[^\u4e00-\u9fff0-9A-Za-z]+')


def slug(t, n=14):
    t = re.sub(r'^最高人民法院关于', '', t)
    t = re.sub(r'^关于', '', t)
    t = re.sub(r'^最高人民法院、最高人民检察院', '', t)
    return BAD.sub('', t)[:n] or 'untitled'


def parse_fm(raw):
    fm, body = {}, raw
    m = re.match(r'^---\n(.*?)\n---\n', raw, re.S)
    if m:
        body = raw[m.end():]
        cur = None
        for line in m.group(1).split('\n'):
            mm = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
            if mm:
                fm[mm.group(1)] = mm.group(2).strip().strip('"\'')
                cur = mm.group(1)
            elif re.match(r'^\s*-\s+', line) and cur:
                fm[cur] = (fm.get(cur, '') + ' | ' + line.strip()[1:].strip()).strip(' |')
    return fm, body.strip()


def main():
    idxp = os.path.join(SKILL, 'index', 'corpus_files.tsv')
    rows = []
    with io.open(idxp, encoding='utf-8') as f:
        head = f.readline().rstrip('\n').split('\t')
        for line in f:
            rows.append(line.rstrip('\n'))
    added = 0
    for p in sorted(glob.glob(os.path.join(GAP, '*.md'))):
        base = os.path.basename(p)
        if base.startswith('_'):
            continue
        raw = io.open(p, encoding='utf-8').read()
        fm, body = parse_fm(raw)
        title = fm.get('title') or base
        tier = fm.get('tier_hint') or 'T4'
        added += 1
        fn = '%s_9%02d_%s.md' % (tier, added, slug(title))
        srcs = fm.get('sources', '')
        o = io.StringIO()
        o.write('# %s\n\n' % title)
        o.write('> 文件性质：司法解释（最高人民法院）\n')
        if fm.get('fashi'):
            o.write('> 文号：%s\n' % fm['fashi'])
        o.write('> 公布：%s　施行：%s　效力：现行有效\n' % (fm.get('issue_date', '—'), fm.get('effective_date', '—')))
        o.write('> 主题层级：%s（2026 年新增/修正件，经补抓入库）\n' % tier)
        o.write('> 核验状态：%s\n' % fm.get('verified', '未标注'))
        o.write('> 抓取来源：%s\n' % srcs)
        o.write('> 备注：%s\n' % fm.get('note', ''))
        o.write('> 本文件为逐段重排版，未作删节；因镜像库尚未收录本件，重大援引请回查上述来源。\n')
        o.write('\n---\n\n')
        o.write(body + '\n')
        io.open(os.path.join(SKILL, 'corpus', 'ssjf', fn), 'w', encoding='utf-8').write(o.getvalue())
        nchar = len(body)
        niao = len(re.findall(r'^\s*(?:-\s*)?\*\*?第[一二三四五六七八九十百千零]{1,9}条', body, re.M))
        rows.append('\t'.join([fn, tier, '2026补抓', fm.get('fashi', ''),
                              (fm.get('effective_date') or '')[:10], str(nchar), str(niao),
                              title, 'out/gap_docs/' + base, srcs.split(' | ')[0], '']))
    with io.open(idxp, 'w', encoding='utf-8') as f:
        f.write('\t'.join(head) + '\n')
        for r in rows:
            f.write(r + '\n')
    print('gap docs merged=%d total index rows=%d' % (added, len(rows)))


if __name__ == '__main__':
    main()
