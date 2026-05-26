# Cardweave — 每日卡片海报生成器

一键生成 9 张 AI/Agent 新闻卡片海报（3 类 × 3 页），适配社交媒体分享和公众号配图。

## 安装

```bash
git clone https://github.com/kissnger/cardweave-skill
cd cardweave-skill/
```

无需 API Key。所有数据来自 Algolia HN Search 免费 API。

## 一键运行

```bash
python3 pipeline/step1_search.py          # 搜索 → 入库
python3 pipeline/step2_curate.py          # 出选题（输出路径从 config 读取）
python3 pipeline/step_tag.py              # 生成标签
python3 pipeline/step4_generate.py        # 生成 9 页 HTML 海报
```

输出路径默认由 `config/curation.yaml` 的 `output.base_dir` 控制（`../output` → `~/.hermes/skills/creative/output/{date}/`）。
也支持 `-o <路径>` 覆盖。

## 可选：PNG 截图

需要 Playwright + Chromium：

```bash
npm install -g playwright
npx playwright install chromium
python3 pipeline/step4_generate.py --screenshot
```

截图输出到 `{output_base}/{date}/screenshots/`。

## 输出结构

```
{output_base}/{date}/
├── articles/           ← 3 篇公众号文章
├── screenshots/        ← 9 张 PNG 截图（--screenshot）
└── tmp/
    ├── 01_selection.json   ← 选题清单
    ├── 01_tags.json        ← 话题标签
    ├── 02_drafts/          ← 正文草稿
    └── cards/              ← 9 页 HTML 海报
```

## 项目结构

```
assets/base.html        # CSS 母版（颜色变量体系）
pipeline/               # 管道脚本（按序号执行）
  ├── config.py         # 统一输出路径读取器
  ├── step0_setup.py    # 初始化 template.json
  ├── step1_search.py   # HN 搜索入库
  ├── step2_curate.py   # 策展出选题
  ├── step_tag.py       # 生成话题标签
  └── step4_generate.py # 生成海报 + 截图
lib/                    # 共享模块
references/             # 字段文档 + 流程图
config/curation.yaml    # 唯一配置源（搜索 · 策展 · 输出路径）
templates/template.json # 数据源（运行时生成，不追踪 git）
```

完整文档见 [SKILL.md](SKILL.md)（给 AI Agent 读的详细操作手册）。

## 许可证

MIT
