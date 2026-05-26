# Pipeline Flow Reference

## 输出基目录

所有管道脚本统一通过 `pipeline/config.py` 读取输出路径：
1. CLI `-o <dir>` 优先
2. 否则读 `config/curation.yaml` 的 `output.base_dir`（相对于 skill 根目录）
3. 安全门禁检查：禁止输出到 skill 目录树内

产物统一放在 `{output_base}/{date}/` 下（下表中以 `{out}/` 简写）。

## 5 阶段管道

| 阶段 | Step | 脚本 | Input | Rule | Output |
|------|------|------|-------|------|--------|
| ①采集 | 0 | `step0_setup.py` | 无 | `_meta.date = datetime.now()` | `templates/template.json`（空骨架） |
| ①采集 | 1 | `step1_search.py` | config/curation.yaml | 4源OR合并, story_id去重, 48h窗口 | `cardweave_db.json` |
| ②策展 | 2 | `step2_curate.py [-o <dir>]` | DB + config/curation.yaml + template._meta.date | min_points + max_candidates分系列；跨源去重 | `{out}/tmp/01_selection.json` |
| ②策展 | 3 | `step_tag.py [-o <dir>] [--update-template]` | `{out}/tmp/01_selection.json` | 从标题自动生成话题标签 | `{out}/tmp/01_tags.json` (+ 可选更新 template.json) |
| ③创作 | — | Agent 自动 | `{out}/tmp/01_selection.json` | 正文≤500字；中文标题/描述/金句；**文章和截图必须同级** | `{out}/tmp/02_drafts/{series}_{n}.md` + `template.json`(中文) + `{out}/articles/` 3篇公众号文章 |
| ④产出 | 4 | `step4_generate.py [-o <dir>] [--screenshot]` | template.json + base.html | 递归检查"待填"门禁；安全门禁拒绝 skill 目录树内输出 | `{out}/tmp/cards/` 9页HTML + `{out}/screenshots/` 9张PNG |
| ⑤Patch | — | Agent 手动 | `{out}/articles/*.html` | 替换 `<img>` 占位路径为实际时间戳 | 文章内的 img src 指向 `./screenshots/{name}_{ts}.png` |

## 关键约定

- **日期传递**：setup.py → template.json.\_meta.date 锁定今天 → curate 只读 → generate 用做目录名
- **articles 和 screenshots 必须同级**（都在 `{date}/` 下），img 才能用 `./screenshots/...` 相对路径
- **文章标题禁止用 ① ② ③ 编号前缀**
- **`-o <dir>` 可选**：不传则走 `config/curation.yaml output.base_dir` 默认路径
- **绝对路径直接使用**，相对路径相对于 skill 根目录解析

## 产出物关系

```
01_selection.json（原始条目+URL）
  → Agent获取正文 → tmp/02_drafts/{series}_{n}.md（≤500字）
  → Agent填写 → template.json（中文三段式标题 + 中文p2/p3 + 三步命令 + brand字段）
  → Agent写文章 → {out}/articles/{seq}_{series}.html（3篇，无编号标题）
  → generate.py → {out}/tmp/cards/ 9页HTML
  → --screenshot → {out}/screenshots/ 9张PNG
  → Agent patch 文章 img src → 最终文章（可发布）
```

## 路径文件清单

```
{output_base}/{date}/
├── articles/              ← Agent 手动写
│   ├── 01_trend_*.html
│   ├── 02_tool_*.html
│   └── 03_brief_*.html
├── screenshots/           ← step4 --screenshot 产出
│   ├── 01_trend_cover_{ts}.png
│   ├── (共9张)
│   └── 03_brief_insight_{ts}.png
└── tmp/
    ├── 01_selection.json   ← step2_curate 产出
    ├── 01_tags.json        ← step_tag 产出
    ├── 02_drafts/          ← Agent 手动写
    └── cards/              ← step4_generate 产出
        ├── 01_trend_cover.html
        └── (共9页)
```
