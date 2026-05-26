---
name: cardweave-skill
description: >-
  Use this when generating daily card-style poster series (9 cards: 3 series ×
  3 pages). Covers HN search → DB curation → HTML/PNG render pipeline.
  Triggers: '出海报', '出卡片', '今天发'.
version: 6.2.0
author: Doon神
license: MIT
metadata:
  hermes:
    tags: [card-design, poster, social-media, html-to-png, daily-brief]
    related_skills: [image-gen-prompt-zimage, writing-plans, hn-scraper]
---

# Cardweave — 每日卡片海报生成器

9 张文字海报卡片（3类×3页），深色底#06061A + CSS变量三配色（紫/绿/琥珀）。

**项目根目录：** `./` — github.com/kissnger/cardweave-skill

## 输出目录规范

所有管道脚本和 agent 创作步骤统一用 `config/curation.yaml` 的 `output.base_dir` 作为根目录。
不传 `-o` 时自动从 rules 文件读取。

```
{output_base}/{date}/
├── articles/           ← 3 篇公众号文章（agent 手动写）
├── screenshots/        ← 9 张 PNG 截图（step4 产出）
└── tmp/
    ├── 01_selection.json   ← 选题清单（step2 产出）
    ├── 01_tags.json        ← 话题标签（step_tag 产出）
    ├── 02_drafts/          ← 正文草稿（agent 手动写）
    └── cards/              ← 9 页 HTML 海报（step4 产出）
```

默认路径：`{output_base} = ~/.hermes/skills/creative/output`（相对于 skill 根目录的 `../output`）。
CLI 传 `-o` 可覆盖，但不要输出到 skill 目录树内（安全门禁会拒绝）。

## 管道速览

```
① 采集
step0_setup.py                                 → template.json (空骨架，date=今天)
step1_search.py                                → cardweave_db.json

② 策展
step2_curate.py [-o <dir>]                     → tmp/01_selection.json
step_tag.py [-o <dir>] [--update-template]     → tmp/01_tags.json

③ 创作（Agent 自动）
获取正文 → 填 template.json → 写3篇公众号文章 → articles/
                                            └──文章里要嵌入卡片截图

④ 产出
step4_generate.py [-o <dir>] [--screenshot]   → tmp/cards/ → screenshots/
                                            └──截图出来后，patch 文章里的 img src
```

**`-o <dir>` 可选**：不传则从 `config/curation.yaml` 的 `output.base_dir` 读取默认路径。
路径相对于 skill 根目录解析，安全门禁禁止输出到 skill 目录树内。

日期链：setup 锁定 `_meta.date` → curate 只读不改 → generate 用它建输出子目录

用户说"跑一下skill" = 跑通以上全流程。**两样东西都要交：**

| 实物 | 内容 | 谁用 |
|------|------|------|
| **公众号文章** (`articles/`) | 每系列一篇，inline CSS 长文，直接粘贴到微信编辑器发 | 关注公众号的读者 |
| **海报卡片** (`screenshots/`) | 3类×3页=9张 540×960 竖屏 PNG，嵌入文章 + 发朋友圈 | 文章读者 + 转发传播 |

**顺序问题：** ③写文章时还没截图，所以文章里的 `<img>` 先写成占位 HTML，等④截图出来后 patch 成 PNG 路径。

## 输出配置（即上述规范）

`config/curation.yaml` 的 `output.base_dir` 设默认输出基目录：

```yaml
output:
  base_dir: "../output"   # 相对 skill 根目录 → ~/.hermes/skills/creative/output/{date}/
```

**articles 和 screenshots 必须同级**（都在 `{date}/` 下），文章里的 `<img src="./screenshots/...">` 才能正确解析。
Agent 创作阶段写文章时，必须写到 `{output_base}/{date}/articles/`，不能写到 skill 目录内。

所有 pipeline 脚本不传 `-o` 时自动从 rules 文件读取。`pipeline/config.py` 是统一读取器。

## 目录总览

| 分类 | 路径 | 说明 |
|------|------|------|
| **源码** | `pipeline/` | 管道脚本（step0_setup/step1_search/step2_curate/step_tag/step4_generate） |
| | `pipeline/config.py` | 统一配置读取器：从 curation.yaml 读 output.base_dir |
| | `lib/hn_search.py` | HN Algolia API 封装 |
| | `config/curation.yaml` | 搜索+策展+输出规则（唯一配置源，不要改脚本参数） |
| | `templates/template.json` | 数据源模板（每日手动填这个） |
| | `assets/base.html` | 设计母版（CSS 变量体系） |
| | `cardweave_db.json` | HN 数据仓库（skill 管理，不属输出） |
| | `references/` | 参考文档（规则/策略/写作指南） |
| **输出** | `{output.base_dir}/{date}/` | 产物（见上表） |

## 每日工作流

### ① 采集 — Step 0: 初始化
```bash
python3 pipeline/step0_setup.py
```
生成空 template.json，锁定 `_meta.date` 为当天。

### ① 采集 — Step 1: 搜索入库
```bash
python3 pipeline/step1_search.py
```
按 curation.yaml 的 4 源搜 HN，去重追加到 cardweave_db.json。

### ② 策展 — Step 2: 内容出库
```bash
python3 pipeline/step2_curate.py
```
读 `_meta.date` → 按 min_points + max_candidates 筛候选 → 写出 tmp/01_selection.json。
不传 `-o` 则用 rules 文件的 output.base_dir。跨源去重。

### ② 策展 — Step 3: 标签生成
```bash
python3 pipeline/step_tag.py
python3 pipeline/step_tag.py --update-template   # 同时写入 template.json
```
读 01_selection.json 标题 → 自动生成中文标签 → 写出 tmp/01_tags.json。`--update-template` 写入 template.json.cover.tag。

### ③ 创作（Agent 自动）
读 tmp/01_selection.json，对每个 URL：
- **获取正文** → tmp/02_drafts/（≤500字，Tavily Extract / urllib）
- **填 template.json** — cover.title 三段中文 / p2 items 无重复 / p3 分析+金句 / tool.p3.steps 3个不同命令
- **填 template.json brand 字段** — 每个系列需要 `brand.bg_word` + `p2.tag/title` + `p3.tag/title`（generate 脚本要求，缺了报 KeyError: 'brand'）
- **写 3 篇公众号文章** → articles/（inline CSS，可直接贴微信编辑器）
  - 文章里要嵌入 3 张对应系列的海报截图，但截图还没出
  - 所以先写占位 `<img src="./screenshots/02_tool_cover_{timestamp}.png">`，等④跑完再补时间戳

### ④ 产出 — 生成海报卡片 + 截图
```bash
python3 pipeline/step4_generate.py --screenshot
```
- 从 template.json 渲染 9 页海报 HTML 到 `tmp/cards/`
- Playwright 截图到 `screenshots/`
- 递归检查"待填"门禁（有则拒绝并报位置）
- 输出 9 页到 tmp/cards/：`01_trend_cover/detail/insight`, `02_tool_*`, `03_brief_*`
- 尺寸 540×960@2x

`--screenshot` 自动生成 9 张 PNG 到 screenshots/，命名与 HTML 对齐：
`01_trend_cover_{ts}.png` / `01_trend_detail_{ts}.png` / … 每个 PNG >60KB 为正常。

### ⑤ Patch 文章
拿到截图实际时间戳后，patch articles/*.html 中的 `<img src>` 占位路径为实际 PNG 文件名：
```
./screenshots/01_trend_cover_2026-05-27_000351.png
```

## 设计规则

- **尺寸：** 540×960 (9:16)，2x 截图 = 1080×1920
- **配色：** trend 紫 `#A855F7` / tool 绿 `#34D399` / brief 琥珀 `#F59E0B`
- **布局：** cover(封面)、data-list/trend-p2、pain-list/tool-p2、news-list/brief-p2、body-list/p3(通用)、steps/tool-p3
- **禁止：** 无导航/进度指示，卡片自成一页。图片不手动改动。
- **文章标题：** 不要用 ① ② ③ 编号前缀（用户反馈不美观），直接写标题文本

## 已知 Bug

| # | 问题 | 状态 |
|---|------|------|
| 1 | setup.py 骨架缺 brand/cover/p2/p3。跑完 setup 后若 template.json 过简，从 git 恢复再手动填 | |
| 2 | step1_search.py `from hn_search import fetch` 找不到 lib/hn_search.py，依赖 `sys.path.insert` 修复 | |
| 3 | step4_generate.py `--screenshot` 模式 file:// 路径是相对路径报 ERR_INVALID_URL | ✅ 已修 |
| 4 | template.json 少了 brand 或 p2/p3 的 tag/title 会报 KeyError: 'brand'（创作阶段必须补全） | 注意 |

## Troubleshooting

| 现象 | 解决 |
|------|------|
| 搜不到结果 | 降低 min_points / 缩短 days / 简化 queries（先用单次词测通） |
| 周末数据稀薄 | Tavily 搜当天 AI 新闻补充 |
| 旧会话残留预填内容 | 先跑 setup.py 清空 template.json 再重填 |
| 日期不对（输出目录不是当天） | 没跑 setup.py 或手动改过 template.json，重新 setup |
| 截图失败 / Playwright 未安装 | `npm install -g playwright && npx playwright install chromium` |
| 文章 img 指向 HTML 而非 PNG | generate 跑完后 patch img src 为 `screenshots/01_trend_cover_{ts}.png` |
| KeyError: 'brand' 在 generate 时 | 创作阶段没填 brand/p2/p3 tag+title，补全 template.json 再重跑 |

## 验证清单

- [ ] setup → _meta.date = 今天
- [ ] 4 源搜通，cardweave_db.json 有数据
- [ ] curate -o → tmp/01_selection.json（各系列有条目）
- [ ] tag -o → tmp/01_tags.json（tag 可选写入 template.json）
- [ ] 正文存 tmp/02_drafts/
- [ ] template.json 含 brand + p2/p3 tag+title
- [ ] template.json cover.title 中文 / p2 无重复 / p3 steps 不重复
- [ ] 3 篇文章在 articles/（无 ① ② ③ 编号标题）
- [ ] generate -o 通过待填门禁，9 页 HTML 在 tmp/cards/
- [ ] 9 张 PNG 在 screenshots/，全部 >60KB
- [ ] 三类配色正确（紫/绿/琥珀）
- [ ] 文章 img src 已 patch 为实际 PNG 路径
