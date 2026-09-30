# civil-code-advisor — 民法典适用技能

一个供 Claude Code / QwenWork / 通用 Agent Skills 使用的法律检索技能：内置《中华人民共和国民法典》**1260 条全文**与 **271 件现行有效**民事、商事、民事诉讼与执行衔接类司法解释全文，并在原文之上做了逐条蒸馏，用于：

- 按请求权基础与争点定位法条（合同、担保、物权、侵权、人格权、婚姻家庭、继承、时效）
- 起草或审查合同与文书时找条文依据
- 判断 2021-01-01 前后新旧法适用与溯及力
- 查期间、除斥期间、举证责任分配、立案案由与法条对应

## 仓库结构

| 路径 | 内容 |
|---|---|
| `civil-code-advisor/` | 技能本体：`SKILL.md` + 语料 + 蒸馏层 + 索引 + 工具 |
| `civil-code-advisor.zip` / `civil-code-advisor.skill` | 整包下载，与目录内容一致（338 个文件，压缩 2.5MB） |
| `提交说明.md` | SkillHub 提交表单稿与安全合规预答记录 |

技能目录内部：

```
civil-code-advisor/
├── SKILL.md          # 技能入口：分层路由、标准工作流、「引用前三查」纪律
├── SOURCE.md         # 语料来源与构建说明
├── LICENSE           # 分层授权（见下）
├── corpus/           # 原文层：民法典全文、271 件司法解释、4 份会议纪要（逐件标注法释号与施行日期）
├── distill/          # 蒸馏层：1260 张要件卡片、434 条解释速查、220 节点请求权路由、5 张衔接表
├── index/            # 机器索引：解释逐条 JSONL、引用倒排、覆盖表、施行衔接条款
└── tools/            # 13 个离线脚本：ask.py / find.py 检索，REFRESH.md 语料刷新
```

## 安装

方式一（推荐）：下载 `civil-code-advisor.zip` 解压，或 `git clone` 本仓库后，把 `civil-code-advisor/` 整个文件夹复制到所用平台的技能目录，例如：

```bash
# Claude Code / 通用 Agent Skills
git clone https://github.com/ChensuLegal/civil-code-advisor.git
cp -r civil-code-advisor/civil-code-advisor ~/.claude/skills/

# ZCode
cp -r civil-code-advisor/civil-code-advisor ~/.zcode/skills/
```

方式二（SkillHub）：见 `提交说明.md` 第六节，上传 `civil-code-advisor.skill`。

## 快速上手

技能安装后，对话中提到民法典条文、请求权基础、司法解释、新旧法衔接等即自动触发。也可以直接用命令行工具检索：

```bash
cd civil-code-advisor
python tools/ask.py 686      # 第686条：原文 + 要件卡片 + 哪些解释引用了它
python tools/find.py 保证期间  # 跨层关键词检索
```

## 语料快照与刷新

语料快照 **2026-09-30**：镜像 `lawtext/laws` 同步至 2026-09-29（其司法解释层实际覆盖到公布日 2026-05-21）；2026-06 至 09 的 19 件新法释为人工补抓并双源核验。二次分发前请按 `tools/REFRESH.md` 重跑刷新并复核效力，或在交付物中注明快照日期。

## 已知边界

- 蒸馏卡片中的「配套解释」含原文明示援引与蒸馏判定的功能对应两类，后者以 `(推定)` 标记；写入对外文书前必须按 `SKILL.md`「引用前三查」回查 `corpus/` 原文。
- T4 扩展层 87 件（知识产权、生态环境、海事海商等）仅收录全文与索引，未做逐条蒸馏。
- 刑事实务、行政、国家赔偿、区际司法协助文件不在范围内，理由见 `civil-code-advisor/index/excluded_manifest.md`。

## 许可

分层授权，详见 [`civil-code-advisor/LICENSE`](civil-code-advisor/LICENSE)：

- **法条与司法解释正文**（`corpus/`）：国家机关发布的立法、司法性质文件，依《著作权法》第五条不适用著作权保护，不主张权利。
- **蒸馏层**（`distill/`、`index/`、`tools/`、`SKILL.md`）：CC BY-NC-SA 4.0（署名—非商业性使用—相同方式共享）。

## 免责声明

本技能是检索与分析辅助工具，输出为蒸馏成果，**不构成法律意见**，不替代执业判断。现行有效性以引用当日的一手来源为准。

---

构建信息：语料民法典 1260 条（flk 版全文，逐条校验）+ 司法解释 271 件 + 参考层纪要 4 份；机器索引含解释逐条 JSONL（5051 条）、民法典←解释引用倒排、1260 条被引覆盖表、施行衔接条款表。构建日期 2026-09-30。
