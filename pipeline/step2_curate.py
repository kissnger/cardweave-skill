#!/usr/bin/env python3
"""
Cardweave 内容出库 — step2_curate.py

读取 cardweave_db.json（扁平条目数组）+ config/curation.yaml，
按策展规则输出选题.json。

用法：
  cd cardweave-skill/
  python3 scripts/step2_curate.py                       # 读 template.json 的日期
  python3 scripts/step2_curate.py --review              # 只看候选，不写入
"""
import json, sys
from urllib.request import urlopen, Request
from urllib.error import URLError
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RULES_FILE = ROOT / "rules" / "curation.yaml"
DB_FILE = ROOT / "cardweave_db.json"
TEMPLATE_FILE = ROOT / "templates" / "template.json"

today = datetime.now().strftime("%Y-%m-%d")

def load_rules():
    import yaml
    with open(RULES_FILE) as f:
        return yaml.safe_load(f)

def load_db():
    if not DB_FILE.exists():
        print(f"[错误] cardweave_db.json 不存在", file=sys.stderr)
        print(f"  先跑: python3 scripts/step1_search.py", file=sys.stderr)
        sys.exit(1)
    with open(DB_FILE) as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def fetch_page_text(url, timeout=5):
    """抓取 URL 页面文本内容"""
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        with urlopen(req, timeout=timeout) as r:
            # 只读前 32KB
            html = r.read(32768).decode("utf-8", errors="replace")
        extractor = TextExtractor()
        extractor.feed(html)
        text = extractor.get_text(300)
        return text if text else None
    except Exception as e:
        return None


def get_entries(db, date_str=None, category=None, is_new_only=False, days_range=2):
    """从扁平的 db.entries 数组中筛选条目
    days_range: 从 date_str 向前多少天都命中（默认2天，含当天）
    """
    entries = db.get("entries", [])
    result = []

    from datetime import datetime, timedelta
    end = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.now()
    start = end - timedelta(days=days_range - 1)

    for e in entries:
        if date_str:
            d = e.get("created_at", "")[:10]
            if not d:
                continue
            ed = datetime.strptime(d, "%Y-%m-%d")
            if ed < start or ed > end:
                continue
        if category and e.get("category") != category:
            continue
        if is_new_only and not e.get("isNew", False):
            continue
        result.append(e)

    return result


def build_cover(candidates, select_rules, layout, date_str):
    """构建 cover 结构，auto_score 直接填，manual 留候选"""
    max_cands = select_rules.get("max_candidates", 3)
    strategy = select_rules.get("strategy", "manual")
    best = candidates[0] if candidates else None

    tag_template = layout.get("tag", "")
    footer_template = layout.get("footer", "")
    tag_default = tag_template.split("·")[0].strip() if "·" in tag_template else tag_template
    footer_default = footer_template.split("·")[-1].strip() if "·" in footer_template else footer_template

    if strategy == "auto_score" and best:
        content = fetch_page_text(best['url'])
        subtitle = content[:160].replace('\n', ' ') if content else best['url']
        return {
            "_candidates": candidates[:max_cands],
            "tag": tag_default + f" · {best['category']}",
            "title": {
                "pre": best["title"][:15],
                "big2": best["title"][:30],
                "highlight": f"↑{best['points']} · {best['category']}",
            },
            "subtitle": subtitle,
            "footer": f"{date_str} · {footer_default}",
        }
    # manual 模式保持原有占位逻辑
    return {
        "_candidates": candidates[:max_cands],
        "tag": tag_default + " · 待填",
        "title": {
            "pre": (best["title"][:15] if best else "待填"),
            "big2": "待填大标题",
            "highlight": "渐变高亮段 · 待填",
        },
        "subtitle": "待填 — 背景说明和分析判断",
        "footer": f"{date_str} · {footer_default}",
    }


def build_pain_list(candidates, select_rules, date_str):
    """构建 pain-list，auto_score 抓 URL 内容填 solution"""
    max_items = select_rules.get("max_items", 3)
    selected = candidates[:max_items]
    items = []
    for e in selected:
        content = fetch_page_text(e['url'])
        solution = content[:120].replace('\n', ' ') if content else f"↑{e['points']} 分 · {e['url']}"
        items.append({
            "problem": e["title"],
            "solution": solution,
            "_url": e["url"],
        })
    if not items:
        items.append({"problem": "待填痛点", "solution": "待填解决方案"})

    return {
        "_selected_ids": [e["story_id"] for e in selected],
        "tag": "传统痛点",
        "title": "为什么需要这个工具？",
        "type": "pain-list",
        "items": items,
    }


def build_data_list(candidates, select_rules, date_str):
    """构建 data-list，auto_score 抓 URL 内容填 desc"""
    max_items = select_rules.get("max_items", 3)
    strategy = select_rules.get("strategy", "manual")
    items = []
    for e in candidates[:max_items]:
        content = fetch_page_text(e['url']) if strategy == "auto_score" else None
        desc = content[:150].replace('\n', ' ') if content else e['url']
        items.append({
            "num": f"↑{e['points']}",
            "title": e["title"][:20] if e["title"] else "?",
            "desc": desc,
            "_url": e["url"],
        })
    # manual 模式才补占位
    if strategy != "auto_score":
        while len(items) < max_items:
            items.append({"num": "待填", "title": "待填", "desc": "待填"})

    return {
        "_candidates": [] if strategy == "auto_score" else candidates[:max_items * 2],
        "tag": "关键数据" if strategy == "auto_score" else "待填标签",
        "title": (candidates[0]["title"][:20] if candidates else "数据摘要") if strategy == "auto_score" else "待填标题",
        "type": "data-list",
        "items": items,
        "source": candidates[0]["category"] if strategy == "auto_score" and candidates else "来源 · 待填",
    }


def build_news_list(candidates, select_rules, date_str):
    """构建 news-list，auto_score 抓 URL 内容填 desc"""
    max_items = select_rules.get("max_items", 3)
    strategy = select_rules.get("strategy", "manual")
    items = []
    for e in candidates[:max_items]:
        desc = ""
        if strategy == "auto_score":
            content = fetch_page_text(e['url'])
            desc = content[:200].replace('\n', ' ') if content else e['url']
        else:
            desc = f"↑{e['points']} — 待填详情说明"
        items.append({
            "title": e["title"],
            "desc": desc,
            "_url": e["url"],
        })
    if strategy != "auto_score":
        while len(items) < max_items:
            items.append({"title": "待填", "desc": "待填"})

    return {
        "_candidates": [] if strategy == "auto_score" else candidates[:max_items * 2],
        "tag": "今日要闻",
        "title": "三条动态 值得关注",
        "type": "news-list",
        "items": items,
    }


def build_body_list(candidates, select_rules, date_str):
    """构建 body-list，留金句位"""
    max_items = select_rules.get("max_items", 2)
    items = []
    for e in candidates[:max_items]:
        items.append({
            "label": "待填标签",
            "text": f"待填正文 — {e['title'][:40]}",
        })
    while len(items) < max_items:
        items.append({"label": "待填", "text": "待填"})

    return {
        "tag": "行业观察",
        "title": "待填标题",
        "type": "body-list",
        "items": items,
        "closing": "待填 — 最有传播力的金句",
    }


def build_steps(candidates, select_rules, date_str):
    """构建 steps"""
    return {
        "_candidates": candidates[:3],
        "tag": "待填 · 快速上手",
        "title": "三步 用起来",
        "type": "steps",
        "items": [
            {"code": "pip install 待填"},
            {"code": "配置 待填"},
            {"code": "使用 待填"},
        ],
        "footer": "待填 · 来源",
    }


def pick_series(series_name, rules, db, date_str):
    """为一个系列选选题，返回 DB 原始格式的条目列表"""
    r = rules["curation"][series_name]
    src_ids = r["sources"]
    select_new = r.get("select", {}).get("isNew", True)

    # 从扁平 db 中筛候选
    all_candidates = []
    for src_id in src_ids:
        all_candidates.extend(get_entries(db, date_str=date_str, category=src_id))
    # 跨源去重
    seen = {}
    for c in all_candidates:
        sid = c["story_id"]
        if sid not in seen or c.get("points", 0) > seen[sid].get("points", 0):
            seen[sid] = c
    all_candidates = list(seen.values())

    # 按 cover 规则排序：priority_tags 优先于 points
    cover_select = r.get("cover", {}).get("select", {})
    priority_tags = cover_select.get("priority_tags", [])
    sort_by = cover_select.get("sort_by", "points")

    def sort_key(x):
        tag_boost = 0
        for i, pt in enumerate(priority_tags):
            if pt in x.get("_tags", []):
                tag_boost = (len(priority_tags) - i) * 10000
                break
        return (x.get("isNew", False), tag_boost + x.get("points", 0))

    all_candidates.sort(key=sort_key, reverse=True)

    # 按 cover 规则取候选
    select_r = cover_select
    max_n = select_r.get("max_candidates", 3)
    min_pts = select_r.get("min_points", 0)
    picked = [c for c in all_candidates if c.get("points", 0) >= min_pts and not c.get("used", False)][:max_n]
    return picked


def main():
    args = sys.argv[1:]
    review_only = False

    for a in args:
        if a == "--review":
            review_only = True

    rules = load_rules()
    db = load_db()

    date_str = today
    if TEMPLATE_FILE.exists():
        try:
            existing = json.load(open(TEMPLATE_FILE))
            ts = existing.get("_meta", {}).get("date")
            if ts:
                date_str = ts
        except (json.JSONDecodeError, KeyError):
            pass

    # 为各系列选题
    picked_ids = []
    read_ids = []
    output = {"date": date_str}
    for series_name in ["brief", "trend", "tool"]:
        items = pick_series(series_name, rules, db, date_str)
        output[series_name] = items
        for item in items:
            sid = item["story_id"]
            if series_name == "brief":
                read_ids.append(sid)
            else:
                picked_ids.append(sid)

    print(f"\n{'='*50}")
    print(f"  Cardweave 选题 — {date_str}  |  库中共 {len(db['entries'])} 条")
    for s in ["brief", "trend", "tool"]:
        items = output[s]
        pts = ", ".join(f"↑{i['points']}" for i in items[:5])
        print(f"    {s}: {len(items)} 条 ({pts})")
    print(f"{'='*50}\n")

    if review_only:
        for s in ["brief", "trend", "tool"]:
            print(f"── {s} ──")
            for i in output[s]:
                print(f"  ↑{i['points']:4d}  {i['title'][:60]}")
        return

    # 写出选题 json
    out_dir = ROOT / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    topic_file = out_dir / "选题.json"
    with open(topic_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"  📄 {topic_file.relative_to(ROOT)}")

    # 标记已用
    if picked_ids:
        for e in db["entries"]:
            if e["story_id"] in picked_ids:
                e["isNew"] = False
                e["used"] = True
    if read_ids:
        for e in db["entries"]:
            if e["story_id"] in read_ids:
                e["isNew"] = False
    if picked_ids or read_ids:
        save_db(db)
        if picked_ids:
            print(f"  ✓ {len(set(picked_ids))} 条已标记为 used")

    print(f"\n{'='*50}")
    print(f"  下一步: 获取正文 → 写中文")
    print(f"          python3 scripts/generate.py")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
