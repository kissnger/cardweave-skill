#!/usr/bin/env python3
"""
Cardweave 搜索入库 — step1_search.py

读取 config/curation.yaml 的 search.sources 配置，
依次执行所有搜索，结果以扁平数组存入 cardweave_db.json。

用法：
  cd cardweave-skill/
  python3 scripts/step1_search.py              # 搜所有源，存 db
  python3 scripts/step1_search.py --list       # 只看有哪些搜索源
  python3 scripts/step1_search.py --source show_hn  # 只搜指定源
"""
import json, sys, os
from pathlib import Path
from datetime import datetime
from hn_search import fetch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RULES_FILE = ROOT / "rules" / "curation.yaml"
DB_FILE = ROOT / "cardweave_db.json"

today = datetime.now().strftime("%Y-%m-%d")

def load_rules():
    import yaml
    if not RULES_FILE.exists():
        print(f"[错误] 找不到规则文件: {RULES_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(RULES_FILE) as f:
        return yaml.safe_load(f)

def load_db():
    if DB_FILE.exists():
        with open(DB_FILE) as f:
            return json.load(f)
    return {"last_updated": "", "entries": []}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def do_search(source):
    """执行单个搜索源，支持多查询（queries列表）OR 合并"""
    print(f"  🔍 {source['id']}: {source.get('description', '')}")

    tags_map = {
        "show_hn": "show_hn",
        "front_page": "front_page",
        "ask_hn": "ask_hn",
    }
    tags = tags_map.get(source["type"], "")
    min_pts = source.get("min_points", 0)
    days = source.get("days", 0)
    count = source.get("count", 10)
    sort_by = source.get("sort", "by_date")
    sort_by_date = sort_by == "by_date"

    # 支持 queries 列表（OR 合并）和 query 单字符串（向后兼容）
    queries = source.get("queries", [])
    single_query = source.get("query", "")
    if single_query and not queries:
        queries = [single_query]

    if queries:
        print(f"     ({source['type']}, {len(queries)} 个查询, min={min_pts})")
    else:
        print(f"     ({source['type']}, min={min_pts})")

    all_items = []
    for q in queries:
        items = fetch(tags, q, min_pts, days, count, sort_by_date)
        if items:
            all_items.extend(items)

    # 去重
    seen = set()
    unique = []
    for item in all_items:
        oid = item.get("objectID", "")
        if oid not in seen:
            seen.add(oid)
            unique.append(item)

    if not unique:
        print(f"     ⚠️  无结果")
        return []
    print(f"     ✅ {len(unique)} 条 (合并后)")
    return unique


def extract_entry(raw_item, category, date_str):
    """从 Algolia 原始数据中提取需要的字段"""
    oid = raw_item.get("objectID", "")
    return {
        "story_id": oid,
        "title": raw_item.get("title", ""),
        "url": raw_item.get("url", "") or f"https://news.ycombinator.com/item?id={oid}",
        "created_at": raw_item.get("created_at", ""),
        "_tags": raw_item.get("_tags", []),
        "points": raw_item.get("points", 0),
        "category": category,
        "isNew": True,
        "used": False,
    }


def main():
    rules = load_rules()
    sources = rules["search"]["sources"]

    args = sys.argv[1:]
    if "--list" in args:
        print(f"\n可用的搜索源（共 {len(sources)} 个）:\n")
        for s in sources:
            print(f"  {s['id']:20s}  {s.get('description', '')}")
        print()
        return

    source_filter = None
    for i, a in enumerate(args):
        if a == "--source" and i + 1 < len(args):
            source_filter = args[i + 1]

    print(f"\n{'='*50}")
    print(f"  Cardweave 搜索入库 — {today}")
    print(f"{'='*50}\n")

    all_entries = []
    total = 0

    for src in sources:
        if source_filter and src["id"] != source_filter:
            continue
        items = do_search(src)
        for item in items:
            entry = extract_entry(item, src["id"], today)
            all_entries.append(entry)
        total += len(items)

    if not all_entries:
        print("  无结果，跳过入库")
        return

    # 去重（同一条目在不同源中可能出现，保留第一个）
    seen_ids = set()
    unique = []
    for e in all_entries:
        if e["story_id"] not in seen_ids:
            seen_ids.add(e["story_id"])
            unique.append(e)

    db = load_db()
    db["last_updated"] = datetime.now().isoformat()
    db["entries"].extend(unique)
    # 按时间降序排列
    db["entries"].sort(key=lambda x: x.get("created_at", ""), reverse=True)
    save_db(db)

    print(f"\n{'='*50}")
    print(f"  ✅ 入库完成")
    print(f"  本次搜索: {total} 条, 去重后: {len(unique)} 条")
    print(f"  库总计:   {len(db['entries'])} 条")
    print(f"{'='*50}\n")

    # 摘要
    print("  摘要:")
    for e in unique[:5]:
        print(f"    · {e['title'][:50]}  ↑{e['points']}")
    if len(unique) > 5:
        print(f"    ... 还有 {len(unique)-5} 条")

if __name__ == "__main__":
    main()
