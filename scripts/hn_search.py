#!/usr/bin/env python3
"""
Hacker News 搜索工具（Algolia API）— 用于填充卡片海报数据源

比 Firebase API 快得多，支持关键词搜索、按分数筛选、按时间范围。

用法：
  python3 scripts/hn_search.py                           # Show HN 最新 10 条
  python3 scripts/hn_search.py --top                     # 首页热门前 10
  python3 scripts/hn_search.py --search "AI agent"       # 按关键词搜索
  python3 scripts/hn_search.py --search "code" --min 50  # 搜索 + 最低分数
  python3 scripts/hn_search.py --days 7                  # 最近 7 天
  python3 scripts/hn_search.py --json                    # 输出完整 JSON
  python3 scripts/hn_search.py --cardweave              # 输出 cardweave 格式

数据源：Algolia HN Search API（免费，无需认证）
  https://hn.algolia.com/api
"""
import json, sys, time
from urllib.request import urlopen, Request
from urllib.error import URLError
from datetime import datetime, timezone, timedelta

API = "https://hn.algolia.com/api/v1"

def search(params, sort_by_date=False):
    """调用 Algolia HN Search API"""
    endpoint = "search_by_date" if sort_by_date else "search"
    url = f"{API}/{endpoint}?{params}"
    try:
        req = Request(url, headers={"User-Agent": "cardweave/1.0"})
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except (URLError, json.JSONDecodeError, OSError) as e:
        print(f"[错误] Algolia 请求失败: {e}", file=sys.stderr)
        return None

def fetch(tags="show_hn", query="", min_points=0, days=0, count=10, sort_by_date=True):
    """获取 HN 条目"""
    params = []
    if tags:
        params.append(f"tags={tags}")
    if query:
        params.append(f"query={query}")

    filters = []
    if min_points > 0:
        filters.append(f"points>={min_points}")
    if days > 0:
        cutoff = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
        filters.append(f"created_at_i>{cutoff}")
    if filters:
        params.append("numericFilters=" + ",".join(filters))

    params.append(f"hitsPerPage={count}")

    result = search("&".join(params), sort_by_date=sort_by_date)
    if not result:
        return []
    return result.get("hits", [])

def show_items(items):
    """终端预览"""
    print(f"\n{'='*60}")
    type_label = {
        "show_hn": "Show HN",
        "front_page": "首页热门",
        "ask_hn": "Ask HN",
        "story": "全部故事",
    }.get(items[0].get("_tags", [""])[0] if items else "", "HN")
    print(f"  {type_label} — 共 {len(items)} 条")
    print(f"{'='*60}\n")
    for i, item in enumerate(items, 1):
        title = item.get("title", "无标题")
        points = item.get("points", 0)
        comments = item.get("num_comments", 0)
        author = item.get("author", "?")
        url = item.get("url") or f"https://news.ycombinator.com/item?id={item['objectID']}"
        hn_url = f"https://news.ycombinator.com/item?id={item['objectID']}"
        created = datetime.fromtimestamp(item.get("created_at_i", 0)).strftime("%m-%d %H:%M")
        print(f"  {i:2d}. {title}")
        print(f"      ↑{points}  💬{comments}  👤{author}  🕐{created}")
        print(f"      {url}")
        print()

def to_json(items):
    """输出完整 JSON"""
    output = []
    for item in items:
        output.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "hn_url": f"https://news.ycombinator.com/item?id={item['objectID']}",
            "points": item.get("points", 0),
            "comments": item.get("num_comments", 0),
            "author": item.get("author"),
            "created_at": item.get("created_at"),
        })
    return json.dumps(output, ensure_ascii=False, indent=2)

def to_cardweave(items):
    """输出 cardweave pain-list 格式"""
    pains = []
    for item in items[:3]:
        title = item.get("title", "")
        url = item.get("url") or f"https://news.ycombinator.com/item?id={item['objectID']}"
        points = item.get("points", 0)
        # 从标题推断痛点内容
        pains.append({
            "problem": f"{title}",
            "solution": f"↑{points} 分 · {url}"
        })
    return json.dumps(pains, ensure_ascii=False, indent=2)

# ── 主入口 ──
if __name__ == "__main__":
    tags = "show_hn"
    query = ""
    min_points = 0
    days = 0
    count = 10
    output = "preview"

    args = sys.argv[1:]

    # 故事类型与排序
    sort_by_date = True
    for flag in list(args):
        if flag == "--top":
            tags = "front_page"
            args.remove(flag)
        elif flag == "--ask":
            tags = "ask_hn"
            args.remove(flag)
        elif flag == "--show":
            tags = "show_hn"
            args.remove(flag)
        elif flag == "--popular":
            sort_by_date = False
            args.remove(flag)

    # 关键词搜索
    for i, arg in enumerate(args):
        if arg == "--search" and i + 1 < len(args):
            query = args[i + 1]

    # 参数解析
    i = 0
    while i < len(args):
        if args[i] == "--min" and i + 1 < len(args):
            min_points = int(args[i + 1])
            i += 1
        elif args[i] == "--days" and i + 1 < len(args):
            days = int(args[i + 1])
            i += 1
        elif args[i] == "--count" and i + 1 < len(args):
            count = int(args[i + 1])
            i += 1
        elif args[i] == "--json":
            output = "json"
        elif args[i] == "--cardweave":
            output = "cardweave"
        i += 1

    items = fetch(tags, query, min_points, days, count, sort_by_date)

    if not items:
        print("未找到结果。试试调整搜索条件。", file=sys.stderr)
        sys.exit(1)

    if output == "json":
        print(to_json(items))
    elif output == "cardweave":
        print(to_cardweave(items))
    else:
        show_items(items)
