#!/usr/bin/env python3
"""
Cardweave 内容出库 — curate.py

读取 cardweave_db.json（扁平条目数组）+ rules/curation.yaml，
按策展规则自动填充 template.json。

策略：
  - auto_score → 自动选最优条目填入
  - manual → 填入候选列表，我看了再调

用法：
  cd cardweave-skill/
  python3 scripts/curate.py                            # 读 template.json 的日期
  python3 scripts/curate.py --review                   # 只看候选，不写入
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
        print(f"  先跑: python3 scripts/search_all.py", file=sys.stderr)
        sys.exit(1)
    with open(DB_FILE) as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def save_template(data):
    with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ template.json 已更新")


# ── URL 内容获取 ──────────────────────────────────────────

class TextExtractor(HTMLParser):
    """简单 HTML 文本提取器"""
    def __init__(self):
        super().__init__()
        self._texts = []
        self._skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer", "header"):
            self._skip = True
    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer", "header"):
            self._skip = False
    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if t and len(t) > 20:
                self._texts.append(t)
    def get_text(self, max_chars=500):
        result = []
        total = 0
        for t in self._texts:
            if total + len(t) > max_chars:
                result.append(t[:max_chars - total])
                break
            result.append(t)
            total += len(t)
        return "\n".join(result)


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


def get_entries(db, date_str=None, category=None, is_new_only=False):
    """从扁平的 db.entries 数组中筛选条目"""
    entries = db.get("entries", [])
    result = []

    for e in entries:
        if date_str and e.get("created_at", "")[:10] != date_str:
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


def build_series(series_name, rules, db, date_str):
    """构建一个系列（trend/tool/brief）"""
    r = rules["curation"][series_name]
    src_ids = r["sources"]
    select_new = r.get("select", {}).get("isNew", True)

    brand_colors = {
        "trend": {"primary": "#A855F7", "gradient": ["#D8B4FE", "#A855F7", "#7C3AED"], "bg_word": "SHIFT"},
        "tool":  {"primary": "#34D399", "gradient": ["#6EE7B7", "#34D399", "#059669"], "bg_word": "TOOL"},
        "brief": {"primary": "#F59E0B", "gradient": ["#FCD34D", "#F59E0B", "#D97706"], "bg_word": "BRIEF"},
    }
    series_names = {
        "trend": {"name": "商业趋势", "name_en": "Business Trend"},
        "tool":  {"name": "工具教程", "name_en": "Tool Tutorial"},
        "brief": {"name": "每日简讯", "name_en": "Daily Brief"},
    }

    result = {**series_names[series_name], "brand": brand_colors[series_name]}

    # 从扁平 db 中筛候选：当天 + 指定分类 + 未用优先
    all_candidates = []
    for src_id in src_ids:
        all_candidates.extend(get_entries(db, date_str=date_str, category=src_id))
    # 跨源去重：相同 story_id 只保留最高分
    seen = {}
    for c in all_candidates:
        sid = c["story_id"]
        if sid not in seen or c.get("points", 0) > seen[sid].get("points", 0):
            seen[sid] = c
    all_candidates = list(seen.values())
    # 先按 isNew 排，再按分数或时间排
    sort_by = r.get("cover", {}).get("select", {}).get("sort_by", "points")
    if sort_by == "created_at":
        all_candidates.sort(key=lambda x: (x.get("isNew", False), x.get("created_at", "")), reverse=True)
    else:
        all_candidates.sort(key=lambda x: (x.get("isNew", False), x.get("points", 0)), reverse=True)

    # ── Cover ──
    cover_r = r.get("cover", {})
    cover_select = cover_r.get("select", {})
    cover_candidates = [c for c in all_candidates
                        if c.get("points", 0) >= cover_select.get("min_points", 0)
                        and not c.get("used", False)][:cover_select.get("max_candidates", 5)]

    # priority_tags: 把优先源的同分条目提到前面
    priority_tags = cover_select.get("priority_tags", [])
    if priority_tags:
        priority = [c for c in cover_candidates if c.get("category") in priority_tags]
        others = [c for c in cover_candidates if c.get("category") not in priority_tags]
        cover_candidates = (priority + others)[:cover_select.get("max_candidates", 5)]
    result["cover"] = build_cover(cover_candidates, cover_select, cover_r.get("layout", {}), date_str)

    # ── P2 ──
    p2_r = r.get("p2", {})
    p2_layout = p2_r.get("layout", "pain-list")
    p2_select = p2_r.get("select", {})
    p2_candidates = [c for c in all_candidates
                     if c.get("points", 0) >= p2_select.get("min_points", 0)
                     and not c.get("used", False)][:p2_select.get("max_items", 5) * 2]

    if p2_layout == "pain-list":
        result["p2"] = build_pain_list(p2_candidates, p2_select, date_str)
    elif p2_layout == "data-list":
        result["p2"] = build_data_list(p2_candidates, p2_select, date_str)
    elif p2_layout == "news-list":
        result["p2"] = build_news_list(p2_candidates, p2_select, date_str)
    else:
        result["p2"] = {"tag": "待填", "title": "待填", "type": "待填", "items": []}

    # ── P3 ──
    p3_r = r.get("p3", {})
    p3_layout = p3_r.get("layout", "body-list")
    p3_select = p3_r.get("select", {})
    p3_candidates = [c for c in all_candidates
                     if c.get("points", 0) >= (p3_select.get("min_points", 0) or p2_select.get("min_points", 0))
                     and not c.get("used", False)][:p3_select.get("max_items", 5)]

    if p3_layout == "steps":
        result["p3"] = build_steps(p3_candidates, p3_select, date_str)
    elif p3_layout == "body-list":
        result["p3"] = build_body_list(p3_candidates, p3_select, date_str)
    else:
        result["p3"] = {"tag": "待填", "title": "待填", "type": "待填", "items": [], "closing": "待填"}

    return result


def print_review(series_name, data):
    """打印候选供审阅"""
    print(f"\n  ── {series_name.upper()} ──")
    for section in ["cover", "p2"]:
        cands = data.get(section, {}).get("_candidates", [])
        if cands:
            label = "P2" if section == "p2" else "封面"
            print(f"  {label} 候选:")
            for c in cands:
                tag = " 🆕" if c.get("isNew") else ""
                tag += " ✅已用" if c.get("used") else ""
                print(f"    · {c.get('title','?')[:50]:50s}  ↑{c.get('points',0):3d}  [{c.get('category','?')}]{tag}")
        else:
            items = data.get(section, {}).get("items", [])
            if items:
                label = "P2" if section == "p2" else "封面"
                print(f"  {label} 已自动填充 ({len(items)} 项)")


def mark_used(db, ids):
    """将 db 中指定 story_id 的条目标记为已使用"""
    for e in db["entries"]:
        if e["story_id"] in ids:
            e["isNew"] = False
            e["used"] = True


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
    sort_by = r.get("cover", {}).get("select", {}).get("sort_by", "points")
    all_candidates.sort(key=lambda x: (x.get("isNew", False), x.get("points", 0)), reverse=True)

    # 按 cover 规则取候选
    select_r = r.get("cover", {}).get("select", {})
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

    # 检查数据是否足够，不够则 fallback
    day_entries = get_entries(db, date_str=date_str)
    max_pts = max((e.get("points", 0) for e in day_entries), default=0)
    needs_fallback = len(day_entries) < 5 or max_pts < 50
    if needs_fallback:
        dates = sorted({e["created_at"][:10] for e in db.get("entries", [])}, reverse=True)
        dates = [d for d in dates if d != date_str][:10]
        if not dates and not day_entries:
            print("[错误] 数据库中没有任何数据", file=sys.stderr)
            print("  先跑: python3 scripts/search_all.py", file=sys.stderr)
            sys.exit(1)
        for fallback in dates:
            fb = get_entries(db, date_str=fallback)
            fb_max = max((e.get("points", 0) for e in fb), default=0)
            if len(fb) >= 5 and fb_max >= 50:
                print(f"  [提示] {date_str} 数据不足({len(day_entries)}条,最高{max_pts}分)，使用 {fallback} 的数据")
                date_str = fallback
                break

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
