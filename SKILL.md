---
name: cardweave
description: >-
  Use this skill whenever the user wants to generate daily card-style posters
  from structured content, create social-media-ready visual cards for AI/agent
  news, produce a series of 9 themed posters (cover → details → conclusion
  across 3 categories: Business Trend / Tool Tutorial / Daily Brief), or
  convert structured JSON data into styled standalone HTML or PNG cards.
---

# Cardweave — 每日卡片海报生成器

Generate 9 styled HTML card posters (3 series × 3 pages) from structured JSON data. Each series has its own color scheme and layout templates. Optional PNG export via Playwright.

## 快速入门

```bash
git clone https://github.com/kissnger/cardweave-skill
cd cardweave-skill/

# 编辑数据 → 生成 HTML
vim templates/template.json
python3 scripts/generate.py

# 打开查看
open {日期}/trend/cover.html
```

## 目录结构

```
cardweave-skill/
├── SKILL.md                         # 技能定义（此文件）
├── README.md
├── .gitignore
├── assets/
│   └── base.html                    # 设计母版（CSS 变量体系，非必要不改）
├── scripts/
│   └── generate.py                  # 生成脚本
├── templates/
│   └── template.json                # 数据源模板（每天改这个）
├── references/
│   └── data-schema.md               # JSON 字段参考
└── {日期}/                           # 生成输出（已 gitignore）
    ├── trend/  cover.html · p2.html · p3.html
    ├── tool/   cover.html · p2.html · p3.html
    ├── brief/  cover.html · p2.html · p3.html
    └── screenshots/                 # PNG（--screenshot 时生成）
```

## 工作流程

### 1. 找内容

每次必须搜索当天的真实新闻，不要复用旧数据。

- **trend / 商业趋势**：一个大的行业转折 / 事件
- **tool / 工具教程**：HN 热榜、GitHub 新星、Show HN 高赞项目
- **brief / 每日简讯**：3 条 AI/Agent 领域热点

提取关键数字（百分比、金额、用时）用于 P2 数据卡片。

### 2. 填数据源

编辑 `templates/template.json`，替换字符串值，保持结构不变。

**关键字段规则：**

| 字段 | 可选值 | 注意 |
|------|--------|------|
| `p2.type` | `data-list` / `pain-list` / `news-list` | 影响 P2 布局模板 |
| `p3.type` | `body-list` / `steps` | 影响 P3 布局模板 |
| `cover.title` | — | 必须包含 `pre` + `big2` + `highlight` |
| `brand` | — | 不要改，已按系列预设配色 |

详细字段参考见 `references/data-schema.md`。

### 3. 生成

```bash
# 只生成 HTML
python3 scripts/generate.py

# 生成 HTML + 截图（需 Playwright）
python3 scripts/generate.py --screenshot
```

输出目录以日期命名（`_meta.date` 或当天日期）。

### 4. 截图环境准备（一次性）

```bash
pip3 install --break-system-packages playwright
playwright install chromium
```

## 配色系统

| 系列 | data-series | 主色 | 渐变 |
|------|-------------|------|------|
| 商业趋势 | trend | #A855F7 (紫) | D8B4FE → A855F7 → 7C3AED |
| 工具教程 | tool | #34D399 (绿) | 6EE7B7 → 34D399 → 059669 |
| 每日简讯 | brief | #F59E0B (琥珀) | FCD34D → F59E0B → D97706 |

## 页面布局

| 页面 | 布局 | 关键元素 |
|------|------|---------|
| 封面 | tag → 标题(3段) → 分割线 → 副标题 → footer | bg-text 巨字背景 |

| P2 data-list (trend) | 纵向数据卡片 | 左渐变边框 + 大号数字 + 来源脚注 |
| P2 pain-list (tool) | 大字纯文字 | ◆ 标记 + 缩进解决方案 |
| P2 news-list (brief) | ①②③ 编号 | 粗体标题 + 半透明描述 |

| P3 body-list | 标签+正文 | 渐变金句 + 分割线 |
| P3 steps (tool) | 编号代码块 | 01/02/03 + 等宽字体 |

## 设计原则

- **深色底** #06061A，白字，渐变强调
- **无进度指示器** — 每页自成一体的独立卡片，不加导航元素
- **bg-text** 300px 背底巨字提升视觉深度
- **卡片尺寸** 540×960px (9:16)，2x 截图 = 1080×1920
- **P3 closing** 是最有传播力的元素 — 渐变文字 + 分割线强化

## 常见问题

1. **工作目录不对** — 必须从 repo 根目录 (`cardweave-skill/`) 运行
2. **p2.type 与 items 结构不匹配** — data-list 需要 num/title/desc；pain-list 需要 problem/solution；news-list 需要 title/desc
3. **cover.title 缺字段** — pre/big2/highlight 三个都要
4. **截图全黑** — 先检查 HTML 在浏览器中能否正常渲染，再确认 playwright chromiunm 已安装
5. **不要反复 patch CSS** — 每次重新生成完整的 9 页 HTML，不要增量改

## 验证清单

- [ ] 9 页 HTML 全部生成在日期目录下
- [ ] cover.html 在浏览器打开正常渲染
- [ ] 三类配色正确（紫/绿/琥珀）
- [ ] 截图 PNG 文件大小 > 60KB（渲染正常）
