# Cardweave Data Schema Reference

## template.json 结构

### setup.py 初始状态

```json
{
  "_meta": {
    "schema": "card-series/v1",
    "date": "2026-05-23",
    "description": "每日卡片海报数据源"
  },
  "brief": {"name": "每日简讯", "name_en": "Daily Brief"},
  "trend": {"name": "商业趋势", "name_en": "Business Trend"},
  "tool": {"name": "工具教程", "name_en": "Tool Tutorial"}
}
```

setup.py 只生成骨架 + 日期锁定。每个系列的具体内容（cover、p2、p3）由 curate.py 填充。

### 填充后的完整状态

顶层字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `_meta` | object | 元数据：schema、date、description |
| `trend` | object | 商业趋势系列（紫） |
| `tool` | object | 工具教程系列（绿） |
| `brief` | object | 每日简讯系列（琥珀） |

## 系列结构（trend/tool/brief 共用）

### cover.title

三段标题，全部必填：

```json
"title": {
  "pre": "第一行文本",       // 56px inline
  "big2": "大字号行",       // 64px block
  "highlight": "渐变高亮段"  // 渐变文字
}
```

### cover._candidates（curate.py 自动生成）

auto_score 策略的系列，curate.py 在 cover 里放入候选条目：

```json
"_candidates": [
  {
    "story_id": "48234413",
    "title": "文章标题",
    "url": "https://...",
    "created_at": "2026-05-22T15:09:50Z",
    "_tags": ["story", "author_x", "show_hn"],
    "points": 417,
    "category": "front_page",
    "isNew": true,
    "used": false
  }
]
```

## p2.type

### data-list（trend 用）

纵向数据卡片，大号数字 + 说明。

```json
"type": "data-list",
"items": [
  { "num": "$10B", "title": "数字标", "desc": "说明文字" }
],
"source": "数据来源声明"
```

### pain-list（tool 用）

◆ 标记 + 缩进解决方案。auto_score 策略自动填充。

```json
"type": "pain-list",
"items": [
  { "problem": "痛点陈述", "solution": "解决方案说明" }
]
```

### news-list（brief 用）

①②③ 编号 + 粗体标题 + 半透明描述。

```json
"type": "news-list",
"items": [
  { "title": "标题", "desc": "详情" }
]
```

## p3.type

### body-list（trend / brief 用）

标签+正文 → 分割线 → 渐变金句（最有传播力的元素）。

```json
"type": "body-list",
"items": [
  { "label": "小标签", "text": "正文" }
],
"closing": "收束金句"
```

### steps（tool 用）

01/02/03 编号代码块。

```json
"type": "steps",
"items": [
  { "code": "command --flag" }
],
"footer": "来源 · 归属"
```

## brand 配色块

| 系列 | primary | gradient |
|------|---------|----------|
| trend | #A855F7 | D8B4FE → A855F7 → 7C3AED |
| tool | #34D399 | 6EE7B7 → 34D399 → 059669 |
| brief | #F59E0B | FCD34D → F59E0B → D97706 |

不要改配色值，配色由 CSS 变量管理。

## cardweave_db.json 条目字段

search_all.py 入库时每条结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| story_id | string | HN objectID |
| title | string | 原始标题 |
| url | string | 链接 |
| created_at | string | HN发布时间 (ISO 8601) |
| _tags | array | HN标签 |
| points | int | HN 分数 |
| category | string | 来源分类（show_hn/front_page/search） |
| isNew | bool | 新入库 |
| used | bool | 已被选入某期卡片 |

- `isNew` → curate.py 选中后设为 false
- `used` → auto_score 自动标记；manual 选中由 agent 手动标记
