---
name: cardweave
description: >-
  Use this skill whenever the user wants to generate daily card-style posters
  from structured content, create social-media-ready visual cards for AI/agent
  news, produce a series of 9 themed posters (cover → details → conclusion
  across 3 categories: Business Trend / Tool Tutorial / Daily Brief), or
  convert structured JSON data into styled standalone HTML or PNG cards.
version: 1.1.0
author: Doon神
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [creative, card-poster, html-generation, hn-curation, social-media]
    related_skills: [image-gen-prompt-zimage, local-service-web-ui]
    requires_toolsets: [terminal, file]
---

# Cardweave — 每日卡片海报生成器

Generate 9 styled HTML card posters (3 series × 3 pages) from HN-curated content. Each series has its own color scheme and layout type. Optionally export as 9:16 PNG via Playwright.

The pipeline is self-contained — no API keys needed. HN content comes from Algolia's free API, editorial content is fetched via urllib.

## When to Use

- User asks to "make cards", "generate posters", "do today's cards", "run cardweave"
- User provides a date and wants 9 social-media-ready poster images
- User wants daily AI/agent news delivered as visual cards
- User wants to produce WeChat public account articles with embedded card images

**Don't use for:** one-off generic image generation (use image-gen-prompt-zimage instead), non-poster layout HTML generation, or tasks unrelated to the cardweave pipeline.

## Directory Structure

```
${HERMES_SKILL_DIR}/
├── SKILL.md                         # This file
├── README.md                        # Human setup guide
├── .gitignore
├── cardweave_db.json                # Search result database (append-only, date-accumulated)
├── assets/
│   └── base.html                    # CSS master template (color variables, layout grid)
├── scripts/
│   ├── setup.py                     # Reset template.json with today's date
│   ├── search_all.py                # Search all sources → db
│   ├── hn_search.py                 # Algolia HN Search API wrapper
│   ├── curate.py                    # Read db + rules → output 选题.json
│   ├── generate.py                  # template.json + base.html → 9 HTML pages
│   ├── editorial.py                 # Legacy: auto-fill Chinese (retired from pipeline)
│   ├── translate.py                 # Legacy: static translation table
│   └── screenshot.mjs               # Playwright screenshot script
├── templates/
│   └── template.json                # Data source (the pipeline target)
├── references/
│   ├── data-schema.md               # JSON field reference
│   └── flowchart.md                 # Pipeline flow diagram
├── rules/
│   └── curation.yaml                # Curation rules (search sources, selection, layout)
└── {date}/                          # Generated output (gitignored)
    ├── trend/  cover.html p2.html p3.html    # Purple · Business Trend
    ├── tool/   cover.html p2.html p3.html    # Green  · Tool Tutorial
    ├── brief/  cover.html p2.html p3.html    # Amber  · Daily Brief
    └── screenshots/                           # PNG exports (optional)
```

## Pipeline

The pipeline is **unidirectional** — each step reads the previous step's output and produces input for the next.

### Step 0 — Date Init (setup.py)

```bash
cd ${HERMES_SKILL_DIR} && python3 scripts/setup.py
```

Generates an empty `templates/template.json` with `_meta.date` locked to today. This date is never changed by subsequent steps. The output directory and card footer always show this date.

### Step 1 — Search → Database (search_all.py)

```bash
cd ${HERMES_SKILL_DIR} && python3 scripts/search_all.py
```

Reads `rules/curation.yaml` search sources, queries Algolia HN Search API (free, no key needed), deduplicates, writes to `cardweave_db.json`. Each entry has `isNew=true`, `used=false`.

### Step 2 — Curate → 选题.json (curate.py)

```bash
cd ${HERMES_SKILL_DIR} && python3 scripts/curate.py
```

Reads `_meta.date` from `templates/template.json`, selects candidate entries per series from the DB, writes to `{date}/选题.json`. Does NOT touch template.json.

- **Input:** cardweave_db.json + rules/curation.yaml + templates/template.json (_meta.date)
- **Output:** `{date}/选题.json` — DB-format entries organized by brief/trend/tool
- **Fallback:** If today's data is sparse (<5 entries or max<50 points), automatically uses the latest date with sufficient data. The output directory date (`{date}/`) stays locked to _meta.date regardless of fallback.

### Step 3 — Fetch, Translate, Fill (Agent manual)

The Agent reads `选题.json`, fetches each URL's content, and produces three things:

1. **正文.md** — Source text (≤500 chars) saved to `正文/{series}_{n}.md`
2. **template.json** — Filled with Chinese content (titles, descriptions, articles)
3. **公众号文章** — 3 WeChat articles saved as `{series}_article.html`

This step is manual because the content requires creative judgment (Chinese headlines, article structure, tone).

### Step 4 — Generate HTML (generate.py)

```bash
cd ${HERMES_SKILL_DIR} && python3 scripts/generate.py
# Or specify output directory:
cd ${HERMES_SKILL_DIR} && python3 scripts/generate.py -o /path/to/output
```

Reads `templates/template.json` + `assets/base.html` (CSS master), renders 9 HTML pages.

Default output: `${HERMES_SKILL_DIR}/{date}/` (gitignored).
Use `-o` / `--output-dir` to redirect to any base path — the date subdirectory is created automatically underneath (e.g., `-o ./output` → `./output/{date}/`).

```
{date}/
├── trend/  cover.html p2.html p3.html    # Purple  #A855F7
├── tool/   cover.html p2.html p3.html    # Green   #34D399
└── brief/  cover.html p2.html p3.html    # Amber   #F59E0B
```

### Step 5 — Write WeChat Articles (Agent Work)

Based on the filled template.json, write 3 WeChat public account articles (one per series), saved as `{series}_article.html` (inline CSS, no JS, ready to paste into WeChat editor).

**Article specs:**

| Element | Requirement |
|---------|-------------|
| Format | `.html` with inline CSS |
| Title | Suspense/conflict/numbers upfront. brief=3 signals, trend=contrast conflict, tool=pain+fix |
| Opening | First 3 lines decide fate: start from pain point/conflict |
| Body | Short paragraphs (≤5 lines), visual anchor every 300 chars (blockquote, color block, divider, table) |
| Layout | 16px font, 1.75 line height, max 3 colors. Use `<div style="background:...">` for emphasis |
| Card images | Embed 3 card poster screenshots (9:16 PNG) inline |
| Follow CTA | Gradient background block at bottom: slogan + "长按识别关注" + "点个在看" |
| Engagement | End with `💬 聊两句：...` to prompt comments |
| Reference links | Original sources at the end |

### Step 6 — Export PNG (Optional)

Two approaches:

**A) Automatic (if Playwright is installed):**
```bash
cd ${HERMES_SKILL_DIR} && python3 scripts/generate.py --screenshot
# With custom output:
cd ${HERMES_SKILL_DIR} && python3 scripts/generate.py -o /path/to/output --screenshot
```

**B) Manual via `npx playwright`:**
```bash
cd ${HERMES_SKILL_DIR}
npm install -g playwright
npx playwright install chromium
# Then use the screenshot script or inline node script
```

Screenshot naming: `{seq}_{category}_{page}_{label}.png`
- `01_商业趋势_P1_封面.png`
- `02_工具推荐_P2_详情.png`
- etc.

## Design Reference

### Color System

| Series | data-series | Primary | Gradient |
|--------|------------|---------|----------|
| Business Trend | trend | #A855F7 (Purple) | D8B4FE → A855F7 → 7C3AED |
| Tool Tutorial | tool | #34D399 (Green) | 6EE7B7 → 34D399 → 059669 |
| Daily Brief | brief | #F59E0B (Amber) | FCD34D → F59E0B → D97706 |

### Page Layouts

| Page | Layout | Key Elements |
|------|--------|-------------|
| Cover | tag → title(3-segment) → divider → subtitle → footer | bg-text 300px backdrop |
| P2 (trend) | data-list | Vertical data cards, left gradient border, large numbers |
| P2 (tool) | pain-list | ◆ marked problem + indented solution |
| P2 (brief) | news-list | ①②③ numbered, bold title + muted description |
| P3 (trend/brief) | body-list | Gradient label → text → closing quote |
| P3 (tool) | steps | 01/02/03 numbered code blocks |

### Design Principles

- **Dark background** #06061A, white text, gradient emphasis
- **No progress indicators** — each card is self-contained, no nav elements
- **bg-text** 300px backdrop character for visual depth
- **Card size** 540×960px (9:16), 2x screenshot = 1080×1920
- **P3 closing** is the most shareable element — gradient text + divider emphasis

Full reference: `references/data-schema.md` for JSON field specs.

## Common Pitfalls

1. **Wrong working directory** — must run from `${HERMES_SKILL_DIR}` (the repo root), not from `scripts/` or any subdirectory
2. **p2.type doesn't match items structure** — data-list needs {num, title, desc}; pain-list needs {problem, solution}; news-list needs {title, desc}
3. **cover.title missing fields** — pre, big2, highlight all three are required
4. **"待填" placeholder blocks generate** — editorial.py must run first; generate.py refuses to proceed if any placeholder remains
5. **Screenshots come out black** — check HTML renders in browser first, verify Playwright Chromium is installed
6. **Don't patch CSS incrementally** — always regenerate all 9 HTML pages, never edit generated files directly
7. **Date confusion** — `curate.py --date` should be the data's creation date (from the search results), NOT the current system date

## Verification Checklist

- [ ] Template.json has no "待填" placeholders
- [ ] 9 HTML pages generated in the date directory
- [ ] cover.html renders correctly in browser
- [ ] All 3 color schemes correct (purple/green/amber)
- [ ] Screenshot PNG files > 60KB (rendering normal)
- [ ] WeChat articles saved as `{series}_article.html`
