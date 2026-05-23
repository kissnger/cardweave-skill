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
│   ├── search_all.py                # Search all sources → db
│   ├── hn_search.py                 # Algolia HN Search API wrapper
│   ├── curate.py                    # Read db + rules → fill template.json
│   ├── editorial.py                 # Auto-fetch URLs → write Chinese copy
│   ├── generate.py                  # template.json + base.html → 9 HTML pages
│   ├── translate.py                 # Static translation table (legacy, editorial.py preferred)
│   └── setup.py                     # Reset template.json with today's date
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

All commands run from `${HERMES_SKILL_DIR}`. The pipeline is **unidirectional** — each step reads the previous step's output and produces input for the next.

### Step 1 — Search → Database

```bash
cd ${HERMES_SKILL_DIR} && python3 scripts/search_all.py
```

Reads `rules/curation.yaml` search sources, queries Algolia HN Search API (free, no key needed), deduplicates, writes to `cardweave_db.json`. Each entry has `isNew=true`, `used=false`.

**Search sources** (configured in `rules/curation.yaml`):

| Source | Type | Queries (OR) | Min points | Window |
|--------|------|-------------|------------|--------|
| show_hn | show_hn | AI, agent | 10 | 48h |
| front_page | front_page | AI, agent, developer | 5 | 48h |
| ai_keyword | search | AI training, agent LLM, compute model | 20 | 48h |
| dev_keyword | search | AI agent, developer tool, database | 10 | 48h |

### Step 2 — Curate → Template

```bash
cd ${HERMES_SKILL_DIR} && python3 scripts/curate.py --date YYYY-MM-DD
```

Reads `cardweave_db.json` + `rules/curation.yaml`, selects best entries per series, writes candidate data to `templates/template.json`. The `--date` parameter sets `_meta.date` — use the data's creation date, not the current system date.

**Output rules** (per `rules/curation.yaml`):

| Series | Count | Sources | Min points | Notes |
|--------|-------|---------|------------|-------|
| brief | 3 fixed | front_page, ai_keyword | 30 | Non-consuming (read-only) |
| trend | 1-3 | front_page, ai_keyword, dev_keyword | 200 | |
| tool | 1 fixed | show_hn, dev_keyword (no front_page) | 2 | Show HN priority |

**Output order:** brief → trend → tool (brief picks first, doesn't consume entries).

### Step 3 — Editorial (Auto-Fill Chinese)

```bash
cd ${HERMES_SKILL_DIR} && python3 scripts/editorial.py
```

Iterates each series' cover/P2/P3 slots, fetches the original URL content via urllib, extracts the first 3000 characters of meaningful text, and fills in Chinese:
- Cover title (三段式: pre / big2 / highlight)
- Subtitle
- P2 items (descriptions)
- P3 body text and closing quote

Only overwrites **placeholders** left by curate.py (those starting with "待填", English truncated with "…", pure-URL subtitles). Never overwrites existing Chinese copy.

**Gate check in generate.py:** `generate.py` refuses to run if any "待填" placeholder remains — tells you to run editorial.py first.

### Step 4 — Generate HTML

```bash
cd ${HERMES_SKILL_DIR} && python3 scripts/generate.py
# Or specify output directory:
cd ${HERMES_SKILL_DIR} && python3 scripts/generate.py -o /path/to/output
```

Reads `templates/template.json` + `assets/base.html` (CSS master), renders 9 HTML pages.

Default output: `${HERMES_SKILL_DIR}/{date}/` (e.g., `cardweave-skill/2026-05-23/`).
Use `-o` / `--output-dir` to redirect to any base path — the date subdirectory is created automatically underneath (e.g., `-o ./output` → `./output/2026-05-23/`).

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
