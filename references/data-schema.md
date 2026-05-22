# Cardweave Data Schema Reference

## cover.title

Three sub-fields, all required:

| Field | Display | Size |
|-------|---------|------|
| `pre` | Inline before big2 | 56px |
| `big2` | block, large display | 64px |
| `highlight` | Gradient text via `.hl` | inline |

```json
"title": {
  "pre": "第一行文本",
  "big2": "大字号行",
  "highlight": "渐变高亮段"
}
```

## p2.type

### data-list (trend)

Vertical cards with left gradient accent border. Great for stat-heavy content.

```json
"type": "data-list",
"items": [
  { "num": "$10B", "title": "数字标", "desc": "说明文字" }
],
"source": "数据来源声明"
```

### pain-list (tool)

Large text, no card borders. ◆ marker + indented solution. Supports `<span class="hl">` inline.

```json
"type": "pain-list",
"items": [
  { "problem": "痛点陈述", "solution": "解决方案说明" }
]
```

### news-list (brief)

①②③ numbered badges. Bold title + muted description.

```json
"type": "news-list",
"items": [
  { "title": "标题", "desc": "详情" }
]
```

## p3.type

### body-list (trend / brief)

Gradient-label items + closing quote with separator line.

```json
"type": "body-list",
"items": [
  { "label": "小标签", "text": "正文" }
],
"closing": "收束金句"
```

### steps (tool)

Numbered code blocks (01/02/03) with monospace font + `$` prompt.

```json
"type": "steps",
"items": [
  { "code": "command --flag" }
],
"footer": "来源 · 归属"
```

## brand block

Do not modify. Pre-configured per series.

| Series | primary | gradient |
|--------|---------|----------|
| trend `#A855F7` | D8B4FE → A855F7 → 7C3AED |
| tool  `#34D399` | 6EE7B7 → 34D399 → 059669 |
| brief `#F59E0B` | FCD34D → F59E0B → D97706 |
