#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐条解析司法解释全文，抽取引用锚点，构建条文级索引与引用图谱。

产出（index/）：
  articles_all.jsonl    每一条文记录：file/doc_title/tier/no/label/text/kuan/refs/other_refs/self_ref
  xref_mfd.tsv          倒排：民法典条号 -> 解释文件 + 解释条号 + 首句摘要
  mfd_coverage.tsv      民法典 1260 条逐条：被引用次数、引用它解释件数、引用文件清单
  transition.tsv        时间效力/施行衔接条款摘录
  xref_stats.txt        统计摘要
"""
import io
import os
import re
import json
import glob
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.environ.get('SKILL_OUT') or os.path.join(ROOT, 'skill_out')
CORP = os.path.join(SKILL, 'corpus')
IDX = os.path.join(SKILL, 'index')
CN = '零〇一二三四五六七八九十百千'

TIAO_RE = re.compile(r'^\s*(?:[-*]\s*)?\*{0,2}(第[%s]+条)\*{0,2}[　\s]*(.*)$' % CN)
KUAN_KOU = re.compile(r'^\s*(?:[-*]\s*)?[（(]([一二三四五六七八九十]+)[）)]')
# 民法典引用（全称/简称），可带款、项
MFD_RE = re.compile(r'(?:中华人民共和国)?民法典[第]?\s*([%s]{1,8})条(?:第([一二三四五六七八九十]+)款)?'
                    r'(?:第([一二三四五六七八九十]+)项)?' % CN)
OTHER_RE = re.compile(r'《中华人民共和国([^》]{2,25})》\s*第([%s0-9]{1,8})条(?:第([一二三四五六七八九十]+)款)?' % CN)
SELF_RE = re.compile(r'本法第([%s]{1,8})条' % CN)
TRANS_RE = re.compile(r'(施行后|施行前|生效之日起|尚未审结|尚未审理|本解释施行|修改后|溯及|适用)')
NUM = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7,
       '八': 8, '九': 9}


def cn2int(s):
    if s is None:
        return None
    s = s.replace('〇', '零')
    if s.isdigit():
        return int(s)
    total = num = 0
    for ch in s:
        if ch in NUM:
            num = NUM[ch]
        elif ch == '十':
            total += (num or 1) * 10
            num = 0
        elif ch == '百':
            total += (num or 1) * 100
            num = 0
        elif ch == '千':
            total += (num or 1) * 1000
            num = 0
        else:
            return None
    return total + num


def split_articles(body):
    """返回 [(label, no, text, kuan_list)]，按“第X条”切分全文。"""
    out = []
    cur = None
    buf = []
    for line in body.split('\n'):
        st = line.strip()
        if not st or st.startswith('#') or st.startswith('>') or st.startswith('---'):
            continue
        m = TIAO_RE.match(st)
        if m and cn2int(m.group(1)[1:-1]):
            if cur:
                out.append(finish(cur, buf))
            cur = {'label': m.group(1), 'no': cn2int(m.group(1)[1:-1])}
            buf = [m.group(2)]
        elif cur is not None:
            buf.append(re.sub(r'^[-*]\s*', '', st))
    if cur:
        out.append(finish(cur, buf))
    return out


def finish(cur, buf):
    paras = [re.sub(r'\s+', ' ', b).strip() for b in buf]
    paras = [p for p in paras if p]
    cur['text'] = ' '.join(paras)
    cur['paras'] = paras
    return (cur['label'], cur['no'], cur['text'], paras)


def main():
    files = []
    with io.open(os.path.join(IDX, 'corpus_files.tsv'), encoding='utf-8') as f:
        head = f.readline().rstrip('\n').split('\t')
        for line in f:
            r = dict(zip(head, line.rstrip('\n').split('\t')))
            files.append(r)

    all_rows = []
    xref = collections.defaultdict(list)          # mfd_no -> [(file, tiao, snippet)]
    trans = []
    total_articles = 0
    docs_with_articles = 0
    for r in files:
        if r['tier'] == 'REF':
            continue
        p = os.path.join(CORP, 'ssjf', r['file'])
        if not os.path.exists(p):
            p = os.path.join(CORP, 'cankao', r['file'])
        raw = io.open(p, encoding='utf-8').read()
        body = raw.split('\n---\n', 1)[-1]
        arts = split_articles(body)
        if arts:
            docs_with_articles += 1
        total_articles += len(arts)
        for label, no, text, paras in arts:
            refs = []
            for m in MFD_RE.finditer(text):
                n = cn2int(m.group(1))
                if n and 1 <= n <= 1260:
                    refs.append({'n': n, 'kuan': m.group(2) or '', 'xiang': m.group(3) or ''})
            others = [{'law': m.group(1), 'n': m.group(2), 'kuan': m.group(3) or ''}
                      for m in OTHER_RE.finditer(text)]
            selfr = [cn2int(x) for x in SELF_RE.findall(text)]
            seen, uniq = set(), []
            for x in refs:
                k = (x['n'], x['kuan'], x['xiang'])
                if k not in seen:
                    seen.add(k)
                    uniq.append(x)
            for x in uniq:
                xref[x['n']].append((r['file'], label, text[:70]))
            if TRANS_RE.search(text) and re.search(r'施行|生效|尚未|溯及', text):
                trans.append((r['file'], r['title'], label, text[:180]))
            all_rows.append({'file': r['file'], 'doc': r['title'], 'tier': r['tier'],
                             'fashi': r['fashi'], 'eff': r['eff_date'],
                             'no': no, 'label': label, 'kuan': len(paras),
                             'chars': len(text), 'text': text,
                             'mfd_refs': uniq, 'other_refs': others, 'self_refs': selfr})
    os.makedirs(IDX, exist_ok=True)
    with io.open(os.path.join(IDX, 'articles_all.jsonl'), 'w', encoding='utf-8') as f:
        for row in all_rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    with io.open(os.path.join(IDX, 'xref_mfd.tsv'), 'w', encoding='utf-8') as f:
        f.write('mfd_no\tdoc_file\ttiao\tsnippet\n')
        for n in sorted(xref):
            for fn, lab, sn in xref[n]:
                f.write('%d\t%s\t%s\t%s\n' % (n, fn, lab, sn.replace('\t', ' ')))

    mfd = [json.loads(l) for l in io.open(os.path.join(CORP, 'mfd', 'articles.jsonl'), encoding='utf-8')]
    with io.open(os.path.join(IDX, 'mfd_coverage.tsv'), 'w', encoding='utf-8') as f:
        f.write('no\tlabel\tpart\tchapter\tcited_times\tcited_docs\tcited_by\n')
        cov = 0
        for a in mfd:
            lst = xref.get(a['no'], [])
            docs = sorted(set(x[0] for x in lst))
            if docs:
                cov += 1
            f.write('%d\t%s\t%s\t%s\t%d\t%d\t%s\n' %
                    (a['no'], a['label'], a['part'], a['chapter'], len(lst), len(docs),
                     ';'.join(docs)))
    with io.open(os.path.join(IDX, 'transition.tsv'), 'w', encoding='utf-8') as f:
        f.write('file\tdoc\ttiao\ttext\n')
        for fn, title, lab, t in trans:
            f.write('%s\t%s\t%s\t%s\n' % (fn, title, lab, t.replace('\t', ' ').replace('\n', ' ')))

    st = io.open(os.path.join(IDX, 'xref_stats.txt'), 'w', encoding='utf-8')
    st.write('解释文件数(不含参考层)=%d，其中有逐条结构者=%d\n' % (
        len([r for r in files if r['tier'] != 'REF']), docs_with_articles))
    st.write('解释条文总数=%d\n' % total_articles)
    st.write('民法典被解释引用条文数=%d/1260（%.1f%%）\n' % (cov, cov * 100.0 / 1260))
    st.write('引用锚点总数=%d\n' % sum(len(v) for v in xref.values()))
    byfile = collections.Counter(r['file'] for r in all_rows)
    st.write('\n无逐条结构的文件（需人工确认是否为批复/通知类短文）：\n')
    for r in files:
        if r['tier'] != 'REF' and not byfile.get(r['file']):
            st.write('   %s  %s\n' % (r['file'], r['title']))
    top = sorted(xref.items(), key=lambda kv: -len(kv[1]))[:25]
    st.write('\n被引用最多的民法典条文 TOP25：\n')
    lab = {a['no']: a['label'] for a in mfd}
    pt = {a['no']: a['part'] for a in mfd}
    for n, v in top:
        st.write('   %s(%s) 被引%d次，涉及%d件\n' % (lab.get(n, n), pt.get(n, '')[:8],
                                               len(v), len(set(x[0] for x in v))))
    st.close()
    print('articles=%d xref=%d coverage=%d' % (total_articles, sum(len(v) for v in xref.values()), cov))


if __name__ == '__main__':
    main()
