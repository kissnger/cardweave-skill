---
name: cardweave-skill
description: >-
  Use this when generating daily card-style poster series (9 cards: 3 series ×
  3 pages). Covers HN search → DB curation → HTML/PNG render pipeline.
  Triggers: '出海报', '出卡片', '今天发'.
version: 5.0.0
author: Doon神
license: MIT
metadata:
  hermes:
    tags: [card-design, poster, social-media, html-to-png, daily-brief]
    related_skills: [image-gen-prompt-zimage, writing-plans, hn-scraper]
---

# Cardweave — 每日卡片海报生成器

9 张文字海报卡片（3类×3页），深色底#06061A + CSS变量三配色（紫/绿/琥珀）。

**项目根目录：** `./` — 源码 + Agent 说明书合一，git 仓库直连 `github.com/kissnger/cardweave-skill`

## 管道流程

### 6 步管道

```
step0_setup.py   →  template.json(空骨架,_meta.date=今天)    锁定输出日期
step1_search.py  →  cardweave_db.json(扁平数组)               按规则搜 HN,4源 OR 合并
step2_curate.py  →  {date}/选题.json(DB原始格式,按分类组织)   选候选,不碰 template.json
step_tag.py      →  template.json.cover.tag                   从选题标题自动生成话题标签
  ↓  (手动)    →  获取正文(.md≤500字) + 填 template.json(中文) + 写3篇公众号文章
generate.py    →  9页 HTML                                   渲染器(内置"待填"门禁)
```

用户说"跑一下skill" = `setup → search → curate → tag → 手动填内容 → generate → 截图9张` 全流程。generate 跑完不是终点，文章和截图是强制产出。

### 日期传递链

```
step0_setup.py     ──→  template.json._meta.date  = 今天
                         ↓  (curate.py 只读不改)
curate.py           ──→  读 _meta.date 筛选 DB 条目
                         ↓
generate.py -o out/  →  out/{_meta.date}/  (输出日期子目录)
```

核心规则：`_meta.date` = 发布日（setup 锁定，永不改变）。`curate.py` 不再接收 `--date` 参数。每天的数据当天筛，数据不够就直接出空选题，不退让。

### 关键原则
- **setup.py 先行**：它生成空 template.json 并锁定 `_meta.date` 为当天。后续 curate.py 读这个日期筛选数据但不覆盖它，所以输出目录名和卡片 footer 永远显示当天。
- **curate.py 只出选题**：不再写 template.json 或 .md 文件。产出是 `{date}/选题.json`（DB 原始格式条目按 brief/trend/tool 分类）。
- **curate.py 按 2 天窗口筛数据**：`pick_series()` 从 template.json 读 `_meta.date`，然后在 DB 中找 `created_at` 落在 [`_meta.date` - 1天, `_meta.date`] 范围内的条目。不是精确日期匹配，否则漏掉前一天的优秀条目。
- **step 3 是手动的**：读选题.json → 用 Tavily/urllib 获取每个 URL 正文(≤500字) → 手动填template.json(中文) → 手动写3篇公众号文章。
- **generate.py 的"待填"门禁**：启动时递归扫描 template.json 所有字段，任何含"待填"就拒绝运行并报位置。
- **"用脚本解决，不用备注提醒"**：任何需要"小心/注意/不要"的约束都应该用脚本封死（setup 锁定日期、generate 拒绝占位符），不要在文档里写注意事项。

---

## 目录结构

```
./
├── .git/                                  # GitHub: kissnger/cardweave-skill
├── SKILL.md                               # 主文档 + Agent 操作手册
├── cardweave_db.json                      # HN 数据仓库（扁平数组，按时间降序）
├── README.md
├── .gitignore
│
├── config/
│   └── curation.yaml                      # 搜索+策展规则（唯一配置）
│
├── pipeline/                              # 管道脚本（按序号执行）
│   ├── step0_setup.py                     # 日期初始化
│   ├── step1_search.py                    # 搜索入库
│   ├── step2_curate.py                    # 读 _meta.date → 选题.json
│   ├── step_tag.py                        # 话题标签生成
│   └── step4_generate.py                  # 渲染器（9页 HTML + 截图）
│
├── lib/                                   # 共享模块
│   ├── hn_search.py                       # HN Algolia API 封装
│   └── screenshot.mjs                     # 独立 Playwright 截图脚本
│
├── templates/
│   └── template.json                      # 数据源模板（每日改这个）
│
├── assets/
│   └── base.html                          # 设计母版（CSS 变量体系）
│
├── references/                            # Agent 参考文档
│   ├── curation-rules.md                  # 策展规则详情
│   ├── data-schema.md                     # JSON 字段参考
│   ├── pipeline-flow.md                   # 管道流程图
│   ├── quantity-rules.md                  # 数量硬约束
│   ├── tag-generation-rules.md            # 标签生成规则
│   ├── wechat-article-writing.md          # 公众号文章写作指南（文章级）
│   └── wechat-account-strategy.md         # 公众号起号策略（账号级）
│
└── output/                                # 生成内容（gitignored）
    └── {date}/
        ├── 选题.json
        ├── tags.json
        ├── 正文/                          # 参考素材 .md（≤500字）
        ├── {系列}/  cover.html p2.html p2.html  # 卡片 HTML（3系列×3页=9页）
        ├── {系列}_article.html             # 3 篇公众号文章
        └── screenshots/
            ├── 01_P1_商业趋势_{timestamp}.png
            ├── 01_P2_趋势数据_{timestamp}.png
            ├── ...
            └── 09_P3_简讯观察_{timestamp}.png
```

---

## 每日工作流

### Step 0 — 日期初始化（step0_setup.py）

```bash
python3 pipeline/step0_setup.py
```

生成空的 template.json，`_meta.date` 锁定为当天。后续步骤不改这个日期，输出目录名永远 = 当天。

### Step 1 — 搜索入库（step1_search.py）

```bash
python3 pipeline/step1_search.py
```

按 `config/curation.yaml` 的 4 个搜索源搜 HN，去重后追加到 `cardweave_db.json`。

### Step 2 — 内容出库（step2_curate.py）

```bash
python3 pipeline/step2_curate.py
```

从 template.json 读 `_meta.date`，按策展规则从 DB 筛各分类候选条目，写出 `{date}/选题.json`。**不再碰 template.json，不再接收 `--date 参数`。**

- 每系列按 `min_points` + `max_candidates` 从 DB 取候选
- 跨源去重（相同 story_id 保留最高分）

选题.json 格式：
```json
{"date": "2026-05-23", "brief": [...], "trend": [...], "tool": [...]}
```
每个条目是 DB 原始格式（story_id, title, url, points, category, ...）。

### Step 3 — 生成话题标签（step_tag.py）

```bash
python3 pipeline/step_tag.py --update-template
```

读取 `选题.json` 各系列条目的标题，自动生成简短中文话题标签（后缀），
拼合 `curation.yaml` 中定义的标签前缀，直接写入 `template.json` 的 `cover.tag` 字段。

- brief → 标签后缀固定为日期 `{date}`
- trend → 从首条标题关键词提取，如「能力跃进」「成本警报」「安全警示」
- tool → 优先取工具名（首词，如 `Agent.email`），否则按规则匹配

输出 `{date}/tags.json` 供参考。

匹配规则参考：`references/tag-generation-rules.md`

### Step 5 — 获取正文 + 填 template.json + 写文章（Agent 手动）

读 `{date}/选题.json`，对每个 URL：

**5a. 获取正文**
```bash
# 用 Tavily Extract 或 urllib 获取每篇正文
# 截断到 ≤500 字，保存为 {date}/正文/{系列}_{编号}.md
```

**5b. 填 template.json**
- cover.title: pre/big2/highlight 三段中文
- cover.subtitle: 中文一句话
- p2 items: 中文描述，无重复
- p3 items: 中文分析 + 金句
- tool.p3.steps: 3 个不同命令（git clone → ls → cat README）

**5c. 写 3 篇公众号文章**
- brief_article.html / trend_article.html / tool_article.html
- inline CSS，可直接粘贴到公众号编辑器
- 配色与对应卡片系列一致
- 底部 CTA + "💬 聊两句" + 参考来源
- **账号级策略**：搜一搜SEO（标题/正文嵌入关键词）、助推机制检查（发文次数/互动达标）、发文时间窗口——见 `references/wechat-account-strategy.md`

template.json 格式不变（三段式标题 + 三系列 × 三页布局 + 配色变量）。

### Step 6 — 生成卡片 HTML

```bash
# `-o` 是必选参数（代码已强制，不传报错退出）
python3 pipeline/step4_generate.py -o ./output
python3 pipeline/step4_generate.py -o ./output --screenshot        # + PNG 截图（推荐）
python3 pipeline/step4_generate.py -o /absolute/path                # 自定义路径
```

- 启动时递归扫描 template.json，任何字段含"待填"会拒绝运行并报位置
- `-o /path` 自动在指定路径下创建 `{_meta.date}` 子目录。例如 `-o output/` → `output/2026-05-23/`。日期来自 template.json 的 `_meta.date`
- 正常输出 9 页 HTML

### Step 7 — 截图

**Bug 警示：`generate.py --screenshot` 使用相对路径传入 Playwright 的 `file://` URL，导致 `net::ERR_INVALID_URL`。** 建议用独立 Playwright 脚本截图：

```bash
# 方法 A（推荐）— 独立 Node.js Playwright 脚本：
NODE_PATH=$(npm root -g) node << 'EOF'
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
const BASE = '/absolute/path/to/output/2026-05-23';
const SS_DIR = path.join(BASE, 'screenshots');
fs.mkdirSync(SS_DIR, { recursive: true });
const series = [
  {dir:'trend',label:'商业趋势'},{dir:'tool',label:'工具教程'},{dir:'brief',label:'每日简讯'}
];
const seq = {brief:'03',trend:'01',tool:'02'};
const pages = ['cover','p2','p3'];
const pageLabels = {cover:'P1_封面',p2:'P2_详情',p3:'P3_收束'};
const ts=new Date().toISOString().slice(0,19).replace(/[T:]/g,'_').replace(/-/g,'-');
(async()=>{
  const b=await chromium.launch();
  for(const s of series) for(const p of pages){
    const png = `${seq[s.dir]}_${pageLabels[p]}_${s.label}_${ts}.png`;
    const pg=await b.newPage({viewport:{width:540,height:960}});
    await pg.goto(`file://${path.join(BASE,s.dir,p+'.html')}`,{waitUntil:'networkidle'});
    await pg.screenshot({path:path.join(SS_DIR,png)});
    await pg.close();
    const st=fs.statSync(path.join(SS_DIR,png));
    console.log(st.size>60000?'✅':'⚠️',png,`(${(st.size/1024).toFixed(0)}KB)`);
  }
  await b.close();
})();
EOF
```

注意：Playwright 全局安装时（`npm install -g playwright`），Node 脚本必须加 `NODE_PATH=$(npm root -g)`，否则找不到模块。

```bash
# 方法 B — 单独写 .js 文件跑（如果嫌 heredoc 太长）：
cat > /tmp/screenshot.js << 'SCRIPT'
...（同上脚本内容）...
SCRIPT
NODE_PATH=$(npm root -g) node /tmp/screenshot.js && rm /tmp/screenshot.js
```

截图命名：`{seq}_{page}_{category}_{timestamp}.png`
- `01_P1_商业趋势_2026-05-23_233251.png`
- `01_P2_趋势数据_2026-05-23_233251.png`
- `02_P1_工具教程_2026-05-23_233251.png`
- `03_P1_每日简讯_2026-05-23_233251.png`

验证：每个 PNG >60KB，否则渲染异常。

**对应关系：**
- brief_article.html → screenshots/03_*.png（每日简讯）
- trend_article.html → screenshots/01_*.png（商业趋势）
- tool_article.html → screenshots/02_*.png（工具教程）

操作：先 `ls screenshots/` 确认实际文件名（含时间戳），再用 patch 工具逐个更新每篇文章的 img src。

## 数据库格式

`cardweave_db.json` 结构（扁平数组，无嵌套，无 Algolia 原生垃圾）：

```json
{
  "last_updated": "2026-05-22T23:56:20",
  "entries": [
    {
      "story_id": "48234287",
      "title": "原文标题（英文）",
      "url": "https://...",
      "created_at": "2026-05-22T15:09:50Z",
      "_tags": ["story", "author_x", "show_hn"],
      "points": 65,
      "category": "show_hn",
      "isNew": true,
      "used": false
    }
  ]
}
```

规则：
- **无 `_meta` 嵌套。** `story_id` 到 `category` 是顶层字段。
- **无 Algolia 垃圾字段。** `extract_entry()` 只提取 10 个有用字段，丢弃 `_highlightResult`、`children`（评论ID数组）等。
- **去重：** 相同 `story_id` 不入库。多个搜索源可能返回同一条目。
- **排序：** 按 `created_at` 降序（最新在前）。

### 数据展示规则（重要）

当用户问"数据长什么样"时：
1. **先展示原始数据**（API 返回的完整结构或 DB 里的完整条目），不要自作聪明只展示清理后的摘要
2. 用户明确指定字段后才按需精简
3. 如果展示 DB 结构，**列出所有字段名和说明**，不要只给一两行示例

---

## 搜索源配置（config/curation.yaml）

### 4 个搜索源

| 源 | 类型 | queries（OR 合并） | min | 时间 | 用途 |
|----|------|---------------------|-----|------|------|
| show_hn | show_hn | AI, agent | 10 | 48h | tool 主力源 |
| front_page | front_page | AI, agent, developer | 5 | 48h | brief + trend 主力源 |
| ai_keyword | search | AI training, agent LLM, compute model | 20 | 48h | trend 补充 |
| dev_keyword | search | AI agent, developer tool, database | 10 | 48h | tool + trend 补充 |

所有配置在 `config/curation.yaml` 里改，**不要改脚本本身的搜索参数**。

### 用户强约束（不可违背）

1. **所有内容必须是 AI/Agent/Dev 相关。** 不要抓 ShadowCat QR 传文件、宗教传播动画这类无关内容。
2. **所有内容必须在 48 小时内。** 每个源固定 `days: 2`。
3. **出库顺序：brief → trend → tool。** brief 只读不占，trend/tool 消耗。
4. **内容以中文为主体。** HN 搜到的是英文，填写 template.json 时必须写成中文。翻译脚本 translate.py 只能做基础标题翻译，正文和金句必须人工写。
5. **数量硬约束：** brief=固定3条，trend=1-3条，tool=固定1条。tool 不能凑数——DB 里只有 1 个合格工具就只放 1 条，不许用 front_page 新闻补位。

### Algolia 查询陷阱（重要）

- **不支持 `|` OR 语法。** `query: "AI|agent|LLM"` 会返回 0 结果。  
  ✅ 正确做法：用 `queries: ["AI", "agent"]` 列表，每个词独立搜，结果 OR 合并。
- **空格是 AND。** `query: "AI LLM"` 要求文章同时包含 AI 和 LLM。
- **`query` 参数在 show_hn/front_page 源中也生效。** 可以加 `query: "AI"` 来过滤特定 TAG 下的关键词。
- **返回 0 结果时：** 降低 `min_points`、缩短 `days`、简化 `queries`（先用单个词测通）。
- **原始响应含大量垃圾字段：** `_highlightResult`（高亮匹配信息，很大）、`children`（评论ID数组，有时几十个）、多时间格式。入库前必须用 `extract_entry()` 剥离。

---

## 设计规则

- **深色底** #06061A，白字 + 渐变强调
- **无导航/进度指示** — 卡片自成一体的独立单页
- **卡片尺寸** 540×960 (9:16)，2x 截图 = 1080×1920\n- **配色：** trend 紫 #A855F7 / tool 绿 #34D399 / brief 琥珀 #F59E0B\n- **PNG 命名：** `{序号}_{分类名}_{页码}.png`（如 `01_商业趋势_P1_封面.png`），或带时间戳 `{序号}_{页码}_{分类名}_{时间戳}.png`

## 布局类型

| 模板 | 用于 | 字段要求 |
|------|------|---------|
| cover | 封面 | tag + title(pre/big2/highlight) → 分割线 → subtitle → footer |
| data-list | trend/p2 | num(大号数字) + title + desc，渐变边界卡片 |
| pain-list | tool/p2 | problem(◆痛点) + solution(缩进说明) |
| news-list | brief/p2 | title(①②③编号) + desc(半透明) |
| body-list | p3(通用) | label(小标签) + text(正文) → 分割线 → closing(金句) |
| steps | tool/p3 | code(等宽命令框) 01/02/03 |

---

## 常见问题

1. **项目已合并为单一目录：** **项目根目录 `./`** 既是 Agent 说明书也是 git 代码库，直连 `github.com/kissnger/cardweave-skill`。直接 commit + push 即可上 GitHub。
2. **搜不到结果：** 当前时间段 HN 没有相关 AI/Dev 内容。调高时间段或用 Tavily 补。
3. **周末 HN 数据稀薄（brief=0 / tool=0）：** 周六日 HN 活跃度低，curate.py 可能筛不到足够条目。用 Tavily Search 搜当天 AI/Agent 新闻补充（query: "AI news today YYYY-MM-DD" 或 "AI agent tools"）。template.json 需重新填写，不要用旧预填内容。
4. **template.json 残留旧会话预填内容：** 从历史会话恢复时，template.json 可能含有之前填的中文内容，与当天 HN 搜索结果不匹配。先跑 setup.py 清空或手动删除旧内容再重填。
5. **curate.py 选错 tool 条目：** v4.7.0 前按分数纯排序，高分非工具条目挤掉 show_hn 工具。已修：tag_boost 逻辑让 priority_tags 条目获得 (N-i)*10000 加分确保优先。
6. **curate.py 按精确日期筛漏数据：** v4.6.0 前 `created_at[:10] == date_str` 漏掉前一天的优秀条目。已修：改为 2 天窗口（[date_str-1d, date_str]）。
7. **内容不相关：** queries 列表太宽松或 min_points 太低。收紧条件。
8. **DB 膨胀：** 正常 <10KB/20条。如果几十KB，extract_entry() 没过滤 Algolia 垃圾。
9. **"跑一下skill"：** = 跑完 `setup → search → curate → 手动操作 → generate → 截图` 全流程。generate 跑完不是终点，文章和截图是强制产出。
10. **在哪找仓库：** **项目根目录 `./`** — 带有 .git，直连 GitHub remote `kissnger/cardweave-skill`。
11. **`-o` 是必选参数：** generate.py 已从代码层面强制，不传即报错退出。输出到 `/path/{_meta.date}/`。
12. **完整交付物：** 9 页 HTML + 9 张 PNG + 3 篇公众号文章。generate.py 跑完只是第一步。
13. **日期值：** `_meta.date` 由 setup.py 锁定为当天。curate.py 只读不改，generate.py 用它决定输出目录。curate.py 不再接受 `--date` 参数。
14. **日期不对：** 先跑 setup.py 锁定 `_meta.date` 为今天。如果输出目录不是当天，说明没跑 setup.py 或手动改过 template.json。
15. **截图失败/Playwright 未安装：** `npm install -g playwright && npx playwright install chromium`。pip3 可能因 PEP 668 失败，推荐 npm。
16. **用户问 API/数据长什么样：** 展示原始数据（API 返回完整结构或 DB 完整条目），不要只展示清理后的摘要。用户指哪改哪。
17. **文章 &lt;img&gt; 路径是 HTML 不是 PNG：** generate.py 跑完后 img src 指向 `./brief/cover.html` 而非截图。截图结束后用 patch 更新为 `./screenshots/0{seq}_{page}_{category}_{timestamp}.png`。先 `ls screenshots/` 确认文件名。
18. **输出放 `./output/{date}/`：** 所有产物用 `generate.py -o ./output` 输出到 `output/{date}/`。项目目录只放源码和模板，不混入生成文件。
19. **editorial.py 已删除：** 从 v4.3.0 起改为手动步骤。填 template.json 和写中文全是 Agent 手动操作。
20. **选题.json 格式：** `{"date":"...","brief":[...],"trend":[...],"tool":[...]}`，条目是 DB 原始格式。手动步骤第一步就是读这个文件。
21. **手动步骤具体干什么：** (a) 对选题.json 每个 URL 获取原文(≤500字)；(b) 用中文填 template.json；(c) 写 3 篇公众号文章。做完才能跑 generate.py。
22. **Step 3 是 Agent 做，不是用户做：** 用户只定方向，不插手具体写作。Step 3 产出 = 正文.md + template.json（中文） + 3 篇公众号文章。

---

## Changelog

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-05-26 | 5.0.0 | 重构：技能名 cardweave → cardweave-skill，目录结构模块化（pipeline/lib/config/assets/templates/references/output），所有路径改为相对引用 |
| 2026-05-23 | 4.8.0 | 新增 step_tag.py：从选题标题自动生成中文话题标签，写入 template.json.cover.tag |
| | | 修复 curate.py get_entries() 按精确日期漏数据的 bug——改为 2 天窗口 ([date_str-1d, date_str]) |
| 2026-05-23 | 4.3.0 | curate.py 改为只出选题.json，不再写 template.json |
| | | editorial.py 从管道移除，改为手动步骤 |
| | | 新增 Step 3 手动操作规范（获取正文→填template→写文章） |
| | | 更新日期传递链文档（setup 锁定 → curate 只读 → generate 使用） |
| | | 更新验证清单为 5 步流程 |
| 2026-05-23 | 4.5.0 | `generate.py` 从代码层面强制 `-o` 为必选参数，不传即报错退出，消除默认写入 skill 源目录的隐患 |\n| | | Step 5 移除重复的截图命名段落 |\n| 2026-05-23 | 4.6.0 | Step 5 修复 `--screenshot` 相对路径 bug（`file://../output/` 导致 `ERR_INVALID_URL`），改用独立 Node Playwright 脚本 + 绝对路径 |\n| | | 新增 `NODE_PATH=$(npm root -g)` 全局 Playwright node 运行说明 |\n| | | 新增周末 HN 数据稀薄时用 Tavily 补充内容的经验 |\n| | | 新增旧会话 template.json 残留预填内容的提醒 |
| 2026-05-23 | 4.4.0 | 输出位置改为 task 层 output/ 目录，不在 skill 源目录内 |\n| | | 移除对已删除文件（step5_screenshot.mjs、flowchart.md、editorial.py）的引用 |\n| | | Step 4 默认命令改为 `-o ../output` |\n| | | Step 5 仅保留 `--screenshot` 方法，删除已退役的 .mjs 方案 |\n| | | 截图命名规范统一为实际输出格式（带时间戳） |\n| | | 目录结构调整：output/{date}/ 与 skill 源码分离 |\n| 2026-05-23 | 4.3.1 | Step 5 截图方法改为推荐 generate.py --screenshot（一步到位） |
| | | 新增 Step 5b（截图后更新文章 img 路径） |
| | | 更正截图命名规范为实际输出格式 |
| 2026-05-23 | 4.2.0 | 修复 4 个 bug：curate 跨源去重 / fallback 阈值 / _is_hole 覆盖标题 / steps 多样性 |
| 2026-05-23 | 4.1.0 | curate.py 移除 --date 参数，改从 template.json 读 _meta.date |
| | | generate.py -o 自动建 {_meta.date} 子目录 |
| | | 新增 references/pipeline-flow.md |

---

## 验证清单

- [ ] setup.py → _meta.date = 今天
- [ ] 4 个搜索源全部跑通
- [ ] cardweave_db.json 有数据
- [ ] curate.py 产出 {date}/选题.json，有各系列条目
- [ ] step_tag.py 产出 tags.json，tags 写入 template.json.cover.tag
- [ ] 手动步骤：正文 ≤500 字已存 .md
- [ ] template.json cover.title 全是中文，无英文截断
- [ ] template.json P2 items 无重复条目
- [ ] template.json P3 steps 三条命令各不相同
- [ ] 3 篇公众号文章已写入 output/{_meta.date}/
- [ ] generate.py 未因"待填"拒绝，9 页 HTML 全部生成
- [ ] 9 张海报截图已生成（screenshots/ 下 PNG 全部 >60KB）
- [ ] 三类配色正确（紫/绿/琥珀）
