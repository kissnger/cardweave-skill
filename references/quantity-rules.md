# Cardweave 数量硬约束

来源：config/curation.yaml + 用户 D on神 明确指定。**不可违背。**

| 系列 | 条目数 | 数据源 | min_points | 占用规则 |
|------|--------|--------|-----------|---------|
| **brief** | **固定 3 条** | front_page, ai_keyword | 30 | isNew=false（只读不占，不消耗） |
| **trend** | **1-3 条** | front_page, ai_keyword, dev_keyword | 200 | isNew=false, used=true（消耗） |
| **tool** | **固定 1 条** | **show_hn, dev_keyword**（禁止 front_page） | **2** | isNew=false, used=true（消耗） |

## 出库顺序

1. brief 先挑（只读不占，分数不是最高也能进）
2. trend 再挑（消耗）
3. tool 最后挑（消耗）

## tool 特殊规则

- 禁止从 front_page 源取条目（避免新闻文章冒充工具）
- min_points 仅 2（宁低勿漏，低分但真实的 Show HN 工具也可以上）
- 固定 1 条，不够就空，不凑数
- 必须有 URL 且是实际可用的开源工具/服务
