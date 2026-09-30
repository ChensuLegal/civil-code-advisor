#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 manifest 选中的文件规范化落盘为技能语料层 corpus/。

- corpus/mfd/       民法典全文（复制自 out/mfd/）
- corpus/ssjf/      司法解释全文（去 front matter，加统一引用头，文件名 = 层_序号_短名.md）
- corpus/cankao/    会议纪要等参考层
- index/corpus_files.tsv  归一化文件名 ↔ 原标题/法释号/施行日/字数/条数/源路径/flk链接
"""
import io
import os
import re
import sys
import shutil
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.environ.get('SKILL_OUT') or os.path.join(ROOT, 'skill_out')
LAWS = os.path.join(ROOT, 'laws')

SLIP_STRIP = re.compile(r'[《》“”"\'（）()\[\]、，,。：:；;·\s/\\|*?<>！!？]+')
TITLE_PREFIX = re.compile(r'^最高人民法院(股份有限公司)?(人民)?法院?')


def slug(title, n=14):
    t = re.sub(r'^最高人民法院关于', '', title)
    t = re.sub(r'^关于', '', t)
    t = re.sub(r'^最高人民检察院', '', t)
    t = SLIP_STRIP.sub('', t)
    t = re.sub(r'[^\u4e00-\u9fff0-9A-Za-z]', '', t)
    return (t[:n] or 'untitled')


def norm_body(raw):
    """去 front matter，返回 (fm_dict, body)。"""
    fm = {}
    m = re.match(r'^---\n(.*?)\n---\n', raw, re.S)
    body = raw
    if m:
        for line in m.group(1).split('\n'):
            mm = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
            if mm:
                fm[mm.group(1)] = mm.group(2).strip().strip('"\'')
        body = raw[m.end():]
    return fm, body.strip()


def header(title, fashi, eff, pub, flk, chars, tier, topic, src):
    L = ['# ' + title, '']
    L.append('> 文件性质：司法解释（最高人民法院）')
    if fashi:
        L.append('> 文号：%s' % fashi)
    L.append('> 公布：%s　施行：%s　效力：现行有效（国家法律法规数据库标注）' % (pub or '—', eff or '—'))
    L.append('> 主题归类：%s（层级 %s）' % (topic, tier))
    L.append('> 来源：%s' % (flk or 'flk.npc.gov.cn'))
    L.append('> 正文约 %d 字' % chars)
    L.append('> 原文件：%s' % src)
    L.append('> 本文件为逐段重排版，未作删节；引用时以本文件正文为准，重大援引请回查来源链接。')
    L.append('')
    L.append('---')
    L.append('')
    return '\n'.join(L)


def main():
    msrc = os.path.join(ROOT, 'out', 'inventory', 'manifest.tsv')
    rows = []
    with io.open(msrc, encoding='utf-8') as f:
        head = f.readline().rstrip('\n').split('\t')
        for line in f:
            rows.append(dict(zip(head, line.rstrip('\n').split('\t'))))
    os.makedirs(os.path.join(SKILL, 'corpus', 'ssjf'), exist_ok=True)
    os.makedirs(os.path.join(SKILL, 'corpus', 'mfd'), exist_ok=True)
    os.makedirs(os.path.join(SKILL, 'corpus', 'cankao'), exist_ok=True)
    os.makedirs(os.path.join(SKILL, 'index'), exist_ok=True)

    # 民法典
    for fn in os.listdir(os.path.join(ROOT, 'out', 'mfd')):
        shutil.copy2(os.path.join(ROOT, 'out', 'mfd', fn),
                     os.path.join(SKILL, 'corpus', 'mfd', fn))

    out_rows = []
    cnt = {}
    for r in rows:
        tier = r['tier']
        cnt[tier] = cnt.get(tier, 0) + 1
        src = os.path.join(ROOT, r['path'].replace('/', os.sep))
        if not os.path.exists(src):
            sys.stderr.write('MISS %s\n' % r['path'].encode('unicode_escape').decode())
            continue
        raw = io.open(src, encoding='utf-8', errors='replace').read()
        fm, body = norm_body(raw)
        body = re.sub(r'^\s*\*\*(.+?)\*\*\s*$', r'# \1', body, count=1, flags=re.M)
        fn = '%s_%03d_%s.md' % (tier, cnt[tier], slug(r['title']))
        with io.open(os.path.join(SKILL, 'corpus', 'ssjf', fn), 'w', encoding='utf-8') as f:
            f.write(header(r['title'], r['fashi'], r['eff'], '', r['flk'],
                           int(r['chars'] or 0), tier, r['topic'], r['path']))
            f.write(body + '\n')
        out_rows.append([fn, tier, r['topic'], r['fashi'], r['eff'][:10], r['chars'],
                         r['tiao'], r['title'], r['path'], r['flk'], r['id']])

    # 参考层：appendix 中的会议纪要/纪要类
    ap = os.path.join(LAWS, 'content', 'appendix')
    n = 0
    for fn in sorted(os.listdir(ap)):
        if not fn.endswith('.md'):
            continue
        if not re.search(r'纪要|座谈会|工作会议', fn):
            continue
        raw = io.open(os.path.join(ap, fn), encoding='utf-8').read()
        fm, body = norm_body(raw)
        title = fm.get('title') or re.sub(r'\.md$', '', fn)
        n += 1
        dst = 'REF_%02d_%s.md' % (n, slug(title, 18))
        with io.open(os.path.join(SKILL, 'corpus', 'cankao', dst), 'w', encoding='utf-8') as f:
            f.write('# %s\n\n> 文件性质：审判工作会议纪要/政策性文件（非司法解释，不得作为裁判依据直接援引，'
                    '可作为裁判口径参考）\n> 来源：lawtext/laws content/appendix/%s\n\n---\n\n' % (title, fn))
            f.write(body + '\n')
        out_rows.append([dst, 'REF', '会议纪要', fm.get('publication_date', ''),
                         fm.get('effective_date', '')[:10], str(len(body)), '0', title,
                         'content/appendix/' + fn, fm.get('urls', '').split('|')[0], fm.get('id', '')])

    cols = ['file', 'tier', 'topic', 'fashi', 'eff_date', 'chars', 'tiao', 'title', 'src_path', 'flk_url', 'id']
    with io.open(os.path.join(SKILL, 'index', 'corpus_files.tsv'), 'w', encoding='utf-8') as f:
        f.write('\t'.join(cols) + '\n')
        for r in out_rows:
            f.write('\t'.join(str(x).replace('\t', ' ') for x in r) + '\n')
    print('corpus files=%d (ssjf %d, ref %d)' % (len(out_rows), sum(cnt.values()), n))
    print('tiers', cnt)


if __name__ == '__main__':
    main()
