#!/usr/bin/env python3
"""
Cardweave 流程初始化 — setup.py

删除旧的 template.json，生成新的空模板，日期锁定为当天。
之后 curate.py 会沿用这个日期，不会被数据日期覆盖。

用法：
  cd cardweave-skill/
  python3 scripts/setup.py
  python3 scripts/search_all.py
  python3 scripts/curate.py --date YYYY-MM-DD   # 沿用 setup 的日期
  python3 scripts/editorial.py
  python3 scripts/generate.py
"""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "template.json"
TODAY = datetime.now().strftime("%Y-%m-%d")

template = {
    "_meta": {
        "schema": "card-series/v1",
        "date": TODAY,
        "description": "每日卡片海报数据源",
    },
    "brief": {"name": "每日简讯", "name_en": "Daily Brief"},
    "trend": {"name": "商业趋势", "name_en": "Business Trend"},
    "tool": {"name": "工具教程", "name_en": "Tool Tutorial"},
}

with open(TEMPLATE, "w", encoding="utf-8") as f:
    json.dump(template, f, ensure_ascii=False, indent=2)

print(f"  ✓ {TEMPLATE}")
print(f"  ✓ 日期: {TODAY}")
