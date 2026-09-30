#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建“民法典相关现行司法解释”候选清单。

从本地法库索引中筛选最高人民法院民事/商事/程序衔接类司法解释，
按标题关键词分桶，并统计正文中“民法典”引用次数、法释号、条数、字数。

产出 out/inventory/candidates.tsv 与 out/inventory/report.txt（分桶摘要）。
"""
import io
import os
import re
import json
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(ROOT, 'index.tsv')
OUTDIR = os.path.join(ROOT, 'out', 'inventory')

FASHI_RE = re.compile(r'法释〔(\d{4})〕(\d+)号')
# 分桶规则：按优先级第一个命中的桶
BUCKETS = [
    ('A_民法典直接配套', [r'民法典', r'担保制度', r'合同编通则', r'总则编', r'物权编', r'婚姻家庭编',
                     r'继承编', r'侵权责任编', r'人格权', r'时间效力']),
    ('B_诉讼时效与民事责任衔接', [r'诉讼时效', r'民事案件案由', r'民事案件案由规定']),
    ('C_赔偿与人身权益', [r'人身损害', r'精神损害', r'医疗事故', r'道路交通事故', r'医疗损害',
                     r'食品药品', r'安全生产', r'雇佣', r'名誉权', r'隐私', r'个人信息']),
    ('D_合同与交易类', [r'买卖合同', r'商品房', r'建设工程施工合同', r'民间借贷', r'融资租赁合同',
                    r'租赁合同', r'旅游合同', r'技术合同', r'保管', r'仓储', r'委托合同',
                    r'保证合同', r'独立保函', r'预售', r'物业']),
    ('E_婚姻家庭继承', [r'婚姻家庭', r'离婚', r'抚养', r'收养', r'继承', r'家庭暴力', r'彩礼']),
    ('F_商事主体与金融', [r'公司法', r'企业法', r'破产', r'证券', r'票据', r'保险', r'信托',
                     r'期货', r'上市公司', r'企业改制', r'合资', r'合作', r'股权质押', r'金融',
                     r'商业银行', r'票据纠纷', r'独立保函', r'保理']),
    ('G_程序与证据执行衔接', [r'民事诉讼', r'证据', r'执行', r'保全', r'调解', r'小额诉讼',
                        r'简易程序', r'送达', r'诉讼费用', r'在线诉讼', r'庭审', r'再审',
                        r'支付令', r'仲裁', r'第三人撤销', r'公益诉讼', r'司法确认', r'期间']),
    ('H_劳动与人事', [r'劳动', r'人事争议', r'工伤保险']),
    ('I_知识产权与竞争', [r'专利', r'商标', r'著作权', r'植物新品种', r'集成电路', r'垄断',
                     r'不正当竞争', r'商业秘密', r'技术调查', r'知识产权']),
    ('J_环境与消费及其他民事', [r'环境', r'生态', r'消费', r'消费者权益', r'农村土地承包',
                          r'林业', r'土地', r'房屋', r'建筑', r' maritime', r'海事', r'海商',
                          r'国家赔偿', r'司法救助', r'法律援助']),
]
EXCLUDE = [r'刑事', r'检察', r'死刑', r'贪污', r'受贿', r'未成年犯', r'减刑', r'假释',
           r'行政诉讼', r'行政机关', r'税务', r'海关', r'军事', r'涉军']


def bucket(title, body):
    for name, pats in BUCKETS:
        for p in pats:
            if re.search(p, title):
                return name
    if re.search(r'民法典', body):
        return 'K_正文引用民法典'
    return 'Z_其他'


def main():
    rows = []
    with io.open(IDX, encoding='utf-8') as f:
        head = f.readline().rstrip('\n').split('\t')
        for line in f:
            r = dict(zip(head, line.rstrip('\n').split('\t')))
            if r['layer'] != '司法解释':
                continue
            if '最高人民检察院' in r['author'] and '最高人民法院' not in r['author']:
                continue
            rows.append(r)
    out_rows = []
    for r in rows:
        p = os.path.join(ROOT, r['path'].replace('/', os.sep))
        body = io.open(p, encoding='utf-8', errors='replace').read()
        body = body.split('\n---\n', 1)[-1]
        title = r['title']
        if any(re.search(x, title) for x in EXCLUDE):
            continue
        mfd = body.count('民法典')
        fs = FASHI_RE.findall(body)
        fshi = ('法释〔%s〕%s号' % fs[0]) if fs else ''
        b = bucket(title, body)
        out_rows.append({
            'bucket': b, 'status': r['status'], 'title': title,
            'fashi': fshi, 'pub': r['pub_date'], 'eff': r['eff_date'],
            'mfd_refs': mfd, 'tiao': int(r['tiao_count'] or 0), 'chars': int(r['body_chars'] or 0),
            'author': r['author'], 'id': r['id'], 'flk': r['flk_url'],
            'path': r['path'],
        })
    os.makedirs(OUTDIR, exist_ok=True)
    cols = ['bucket', 'status', 'fashi', 'pub', 'eff', 'mfd_refs', 'tiao', 'chars',
            'title', 'author', 'id', 'flk', 'path']
    with io.open(os.path.join(OUTDIR, 'candidates.tsv'), 'w', encoding='utf-8') as f:
        f.write('\t'.join(cols) + '\n')
        for r in sorted(out_rows, key=lambda x: (x['bucket'], -x['mfd_refs'], x['title'])):
            f.write('\t'.join(str(r[c]).replace('\t', ' ') for c in cols) + '\n')

    rep = io.open(os.path.join(OUTDIR, 'report.txt'), 'w', encoding='utf-8')
    rep.write('候选总数=%d（最高法民事/商事/程序类，已排除刑事检察行政军事等）\n\n' % len(out_rows))
    by = collections.Counter((r['bucket'], r['status']) for r in out_rows)
    for b in sorted(set(r['bucket'] for r in out_rows)):
        tot = sum(v for (bb, s), v in by.items() if bb == b)
        act = sum(v for (bb, s), v in by.items() if bb == b and s == '有效')
        rep.write('== %s  共%d，其中有效%d\n' % (b, tot, act))
        for r in sorted([x for x in out_rows if x['bucket'] == b],
                        key=lambda x: (-x['mfd_refs'], x['status'] != '有效', x['title'])):
            if r['status'] != '有效':
                continue
            rep.write('   [%s] %-16s 引民法典%3d 条%4d 字%6d  %s\n' %
                      (r['status'], r['fashi'], r['mfd_refs'], r['tiao'], r['chars'], r['title']))
    rep.write('\n=== 非“有效”状态（复核用）===\n')
    for r in sorted([x for x in out_rows if x['status'] != '有效'],
                    key=lambda x: (x['status'], x['title'])):
        rep.write('   [%s] %s  %s\n' % (r['status'], r['fashi'], r['title']))
    rep.close()
    print('candidates=%d -> out/inventory/' % len(out_rows))


if __name__ == '__main__':
    main()
