# 策展规则参考 — curation.yaml

所有搜索和出库规则集中在 `config/curation.yaml`，不要改脚本。

## search.sources（搜索层）

```yaml
search:
  sources:
    - id: show_hn
      type: show_hn                     # 对应 Algolia tags=show_hn
      queries: ["AI", "agent"]          # 多个查询 OR 合并
      min_points: 10                    # 最低 HN 分数
      count: 10                         # 每查询条数
      days: 2                           # 48小时限制
      sort: by_date                     # 按时间

    - id: ai_keyword
      type: search                      # 关键词搜索
      queries: ["AI training", "agent LLM", "compute model"]
      min_points: 20
      days: 2
      sort: by_popularity               # 按热度
```

查询技巧：
- `queries` 列表里的每一项独立调 Algolia，结果合并去重（OR 效果）
- 单个 query 里空格是 AND 搜索
- 不支持 `|` pipe 语法（会被当成字面量，返回 0 结果）

## curation（出库层）

```yaml
curation:
  brief:
    sources: [front_page, ai_keyword]
    cover:
      select:
        strategy: auto_score
        min_points: 30
        sort_by: created_at              # 按时间排序（最新的优先）
        max_candidates: 5

  trend:
    sources: [front_page, ai_keyword, dev_keyword]
    p2:
      select:
        strategy: auto_score
        min_points: 200                  # 高分门槛
        max_items: 3

  tool:
    sources: [show_hn, dev_keyword]     # ⚠️ 不加 front_page，避免新闻冒充工具
    cover:
      select:
        strategy: auto_score
        min_points: 2                   # 门槛极低，确保不漏任何一个真工具
        max_candidates: 1                # 固定 1 个候选
        require_url: true                # 必须有 GitHub/演示链接
        priority_tags: ["show_hn"]       # show_hn 条目优先选作封面
    p2:
      select:
        strategy: auto_score
        min_points: 2                    # 门槛极低，宁低勿漏
        max_items: 1                     # 固定 1 条，不凑数
        require_url: true
        layout: "pain-list"
```

## 出库数量约束

| 系列 | 数量 | 说明 |
|------|------|------|
| brief | 固定 3 条 | 只读不占 |
| trend | 1-3 条 | 消耗 |
| tool | 固定 1 条 | 消耗，不得凑数 |

## 出库标记规则

| 系列 | isNew | used | 含义 |
|------|-------|------|------|
| brief | false | 不变 | 只读——读完不占，其他系列还能用 |
| trend | false | true | 消耗——用完标记，下次不推 |
| tool | false | true | 消耗——同上 |

## 出库顺序

```
brief → trend → tool
```

brief 先挑走最好的（按时间最新+>30分），trend 挑高分的，tool 拿剩下的 show_hn 项目。

## 修改原则

- 改关键词/分数/时间 → 改 `search.sources`
- 改筛选逻辑 → 改 `curation.{series}.{section}.select`
- 改布局模板 → 改 `curation.{series}.{section}.layout`
  - 不要改 `.py` 文件
  - canonical 位置是项目根目录 `./`
