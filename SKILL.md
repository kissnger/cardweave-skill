---
name: cardweave
description: >-
  Use this skill whenever the user wants to generate daily card-style posters
  from structured content, create social-media-ready visual cards for AI/agent
  news, produce a series of 9 themed posters (cover → details → conclusion
  across 3 categories: Business Trend / Tool Tutorial / Daily Brief), or
  convert structured JSON data into styled standalone HTML or PNG cards.
---

# Cardweave — Daily Card Poster Generator

Generate 9 styled HTML card posters (3 series × 3 pages) from structured JSON data. Each series has its own color scheme, layout templates, and optional PNG screenshot output via Playwright.

## Directory Structure

```
cardweave-skill/
├── SKILL.md                     # This file — skill definition
├── assets/
│   └── base.html                # Design master (CSS variables, do NOT edit)
├── scripts/
│   └── generate.py              # Generator script (run from repo root)
├── templates/
│   └── template.json            # Data source template (edit this daily)
├── references/                  # Optional: layout specs, color system docs
├── README.md
└── .gitignore
```

Generated output goes to `{date}/`:
```
{date}/
├── trend/  cover.html · p2.html · p3.html
├── tool/   cover.html · p2.html · p3.html
├── brief/  cover.html · p2.html · p3.html
└── screenshots/   (when --screenshot flag)
```

## How to Use

### 1. Edit data source

Edit `templates/template.json` — replace string values, keep the JSON structure intact.

**Critical field rules:**

| Field | Valid values | Required sub-fields |
|-------|-------------|---------------------|
| `p2.type` | `data-list`, `pain-list`, `news-list` | `data-list`: items need `num/title/desc`. `pain-list`: items need `problem/solution`. `news-list`: items need `title/desc` |
| `p3.type` | `body-list`, `steps` | `body-list`: items need `label/text` + `closing` string. `steps`: items need `code` + `footer` string |
| `cover.title` | any text | `pre` (first line), `big2` (large-font line, displayed as block), `highlight` (gradient highlight text) |
| `brand` block | do NOT modify | Pre-configured colors per series |

### 2. Generate HTML

```bash
cd cardweave-skill/
python3 scripts/generate.py templates/template.json
```

Output: 9 HTML files in the date directory.

### 3. Generate PNGs (optional — requires Playwright)

```bash
# One-time setup
pip3 install --break-system-packages playwright
playwright install chromium

# Generate with screenshots
python3 scripts/generate.py templates/template.json --screenshot
```

Output: 9 PNG files at 1080×1920px in `{date}/screenshots/`.

Naming format: `01_P1_商业趋势_{date}_{timestamp}.png` through `03_P3_简讯观察_{date}_{timestamp}.png`.

## Color System

Three series switch automatically via the `data-series` attribute on the `<html>` tag — no manual CSS changes needed.

| Series | data-series | Primary | Gradient |
|--------|-------------|---------|----------|
| Business Trend | trend | #A855F7 (purple) | D8B4FE → A855F7 → 7C3AED |
| Tool Tutorial | tool | #34D399 (green) | 6EE7B7 → 34D399 → 059669 |
| Daily Brief | brief | #F59E0B (amber) | FCD34D → F59E0B → D97706 |

## Page Layout Specifications

- **Cover**: tag → 3-part title (pre/big2/highlight) → gradient divider line → subtitle → footer. Background decoration word (bg-text) at 0.04 opacity serves as visual anchor.
- **P2 — Data (trend)**: Vertical data cards with left brand-gradient accent border (border-image). Source credit with gradient separator line at bottom.
- **P2 — Pain (tool)**: Large text, no card borders. ◆ marker before each problem statement. Solution text indented with left reference line for visual separation.
- **P2 — News (brief)**: ①②③ numbered circle badges. Bold white title with reduced-opacity description paragraph.
- **P3 — Conclusion (trend/brief)**: Body list with label + text → gradient separator line → closing quote (designed as the most shareable element for social screenshots).
- **P3 — Steps (tool)**: Numbered code blocks (01/02/03) with monospace font and shell prompt prefix. Footer with project attribution.

## Common Pitfalls

1. **Wrong `type` field value** — mismatched type breaks layout. Ensure item fields match the type you selected.
2. **Missing `cover.title` sub-fields** — `pre`, `big2`, and `highlight` are all required. Missing one causes a blank title area.
3. **Playwright screenshot error** — Chromium must be installed via `playwright install chromium`. The Python package alone is not enough.
4. **Wrong working directory** — Always run from the repo root (`cardweave-skill/`). The script uses relative paths (`assets/base.html`, `templates/`).
5. **Invalid `data-series` value** — Only `trend`, `tool`, or `brief` are accepted. Any other value produces unstyled or blank pages.

## Verification Checklist

- [ ] All 9 HTML files generated in the `{date}/` directory
- [ ] Opening any `cover.html` in a browser shows a styled card with correct color scheme and content
- [ ] Data source has correct `type` values matching the item structures
- [ ] (Optional) All 9 PNG files present in `screenshots/` directory
