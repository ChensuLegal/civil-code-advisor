# 语料刷新与重建

法库镜像会滞后。本次构建实测：`lawtext/laws` 镜像（源自 flk.npc.gov.cn）司法解释层只到公布日 2026-05-21，2026 年 6—9 月的法释〔2026〕12/14/15/16/17/18/19 号全部缺失，需按第 5 步补抓。

工作目录约定：`<work>/` 下放 `laws/`（镜像仓库）、`index.tsv`、`out/`、`skill_out/`（即技能目录）。脚本按 `<work>/scripts/`、`<work>/laws/` 相对定位，也可用环境变量 `SKILL_OUT` 指定输出。

## 全量重建（7 步）

```bash
cd <work>
git clone --depth 1 https://github.com/lawtext/laws.git laws   # 1. 取镜像（约9秒，46MB）
python scripts/build_index.py                                  # 2. 解析全部文档 front matter → index.tsv
python scripts/extract_mfd.py                                  # 3. 民法典逐条结构化（自动校验 1260 条，缺号即报错）
python scripts/build_ssj_inventory.py                          # 4. 司法解释候选清单（分桶 + 效力 + 引用密度）
python scripts/build_manifest.py                               # 5. 分层清单 T1/T2/T3/T4/X（改 FORCE/EXCLUDE 可调范围）
python scripts/build_corpus.py && python scripts/merge_gap_docs.py   # 6. 语料落盘
python scripts/build_xref.py                                   # 7. 逐条解析 + 引用倒排 + 施行衔接条款
```

第 4—5 步之后必须做法宝差集核验（`mcp__pkulaw__mcp-law.get_law_list`，effectiveness=司法解释、timeliness=现行有效），把镜像缺失的新件抓进 `out/gap_docs/`（带 tier_hint 的 front matter），再跑第 6 步合并。

## 只补新件

```bash
cd <work>/laws && git pull                # 更新镜像
python ../scripts/build_index.py && python ../scripts/build_ssj_inventory.py
python ../scripts/build_manifest.py && python ../scripts/build_corpus.py
python ../scripts/build_xref.py && python ../scripts/verify_distill.py
```

## 改蒸馏层

蒸馏不随脚本自动重跑。改了 `build_manifest.py` 的层级划分后，只对**新增或换版**的文件按 `distill/_SPEC.md` 的卡片格式补蒸馏（交给子代理执行时，务必带上「逐条通读原文、区分明示援引与功能对应、卡片计数必须等于条文数」三条硬约束）。

## 自检

```bash
python scripts/verify_distill.py     # → index/verify.txt：1260 覆盖、缺号 0、各卷计数、字段完整度
python scripts/ask.py 1254           # 抽查单条：原文+卡片+被引解释
```

`extract_mfd.py` 与 `verify_distill.py` 的计数校验是硬闸门：任何一次刷新后条数不等于 1260 或缺号非空，停止交付，先修语料。
