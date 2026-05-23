#!/usr/bin/env python3
"""
Cardweave 内容编辑 — editorial.py

读取 curate.py 输出的 template.json（含原始 HN 数据和 URL），
对每个系列，抓取完整原文，自动填充占位符中文文案。

只填充 curate.py 遗留的原始占位符（"待填" / 英文截断以 "…" 结尾 / URL 副标题），
不会覆盖已写好的中文内容。

用法：
  cd cardweave-skill/
  python3 scripts/search_all.py
  python3 scripts/curate.py --date YYYY-MM-DD
  python3 scripts/editorial.py          # 自动写中文（新增）
  python3 scripts/generate.py           # 直接出卡
"""
import json, sys, re
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from datetime import datetime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TEMPLATE_FILE = ROOT / "templates" / "template.json"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Cardweave/1.0)"}

# ── 占位符检测 ────────────────────────────────────────

def _is_hole(text):
    """判断是否为 curate.py 遗留的原始占位符"""
    if not text or "待填" in text:
        return True
    # 原始 HN 截断：以 "…" 结尾且不含中文
    if text.endswith("…") and not re.search(r'[\u4e00-\u9fff]', text):
        return True
    # curate.py 生成的 "↑N · source" 格式 highlight
    if re.match(r'^↑\d+\s*·\s*(front_page|show_hn|ai_keyword|dev_keyword)', text):
        return True
    # 纯 URL 作为 subtitle
    if text.startswith("http") and "://" in text:
        return True
    # 纯英文字段（不含中文）— curate.py 遗留的未翻译截断
    if text and not re.search(r"[一-鿿]", text) and re.search(r"[a-zA-Z]{3,}", text):
        return True
    return False

def _trim(text, max_len=24):
    return text[:max_len-1] + "…" if len(text) > max_len else text


# ── HTML 文本提取 ─────────────────────────────────────

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._texts = []
        self._skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer", "header", "noscript"):
            self._skip = True
    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer", "header", "noscript"):
            self._skip = False
    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if t and len(t) > 30:
                self._texts.append(t)

def fetch_text(url, max_chars=3000):
    try:
        req = Request(url, headers=REQUEST_HEADERS)
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        parser = TextExtractor()
        parser.feed(html)
        text = "\n".join(parser._texts)
        return text[:max_chars]
    except Exception:
        return ""


# ── 填充逻辑 ──────────────────────────────────────────

def _fill_tag(cover, series_name):
    """封面 tag：去掉英文源名后缀"""
    tag = cover.get("tag", "")
    if not tag or "待填" in tag or ("·" in tag and any(x in tag for x in ["front_page", "show_hn"])):
        cover["tag"] = {"brief": "AI & Agent 简讯", "trend": "AI 趋势", "tool": "开源新工具"}.get(series_name, "行业资讯")
        return True
    return False

def _needs_candidates(s, series_name):
    """检查系列是否有有效候选 — 没有就填兜底文案"""
    has_any = bool(
        s.get("cover", {}).get("_candidates", [])
        or s.get("p2", {}).get("items", [])
        or s.get("p3", {}).get("_candidates", [])
    )
    if not has_any:
        s["cover"] = {
            "tag": {"brief": "AI & Agent 简讯", "trend": "AI 趋势", "tool": "开源新工具"}.get(series_name, ""),
            "title": {"pre": "暂无数据", "big2": "今天没有相关内容", "highlight": "请明日再来"},
            "subtitle": "数据源中暂无符合条件的条目",
            "footer": f"{datetime.now().strftime('%Y-%m-%d')} · {series_name}",
        }
        s["p2"] = {
            "tag": "暂无内容",
            "title": "今日暂缺",
            "type": "news-list",
            "items": [{"title": "数据不足", "desc": "没有达到最低分要求的条目"}],
        }
        s["p3"] = {
            "tag": "等待更新",
            "title": "明日继续",
            "type": "body-list",
            "items": [{"label": "提示", "text": "数据源中暂无符合主题和分数门槛的条目。"}],
            "closing": "明天会有新的信息。",
        }
        return True
    return False

def _fill_title(cover, series_name):
    """封面 title：填充占位"""
    title = cover.get("title", {})
    changed = False
    pre, big2, hl = title.get("pre", ""), title.get("big2", ""), title.get("highlight", "")
    candidates = cover.get("_candidates", [])

    if _is_hole(pre):
        title["pre"] = {"brief": "今日值得关注的", "trend": "今日关键信号", "tool": "开源利器"}.get(series_name, "今日")
        changed = True
    if _is_hole(big2) and candidates:
        raw = _trim(candidates[0].get("title", ""), 24)
        if raw != big2:  # 避免把一样的截断再写一遍
            title["big2"] = raw
            changed = True
    elif not re.search(r'[\u4e00-\u9fff]', big2) and len(big2) < 30 and candidates:
        # curate.py 截断到 20 字但不加 "…"，补成完整或更好的标题
        raw_title = candidates[0].get("title", "")
        if raw_title.startswith(big2.rstrip()) or not re.search(r'[\u4e00-\u9fff]', raw_title):
            title["big2"] = _trim(raw_title, 24)
            changed = True
    if _is_hole(hl):
        pts = candidates[0].get("points", "") if candidates else ""
        title["highlight"] = f"今日聚焦 · ↑{pts}" if pts else "今日聚焦"
        changed = True
    return changed

def _fill_subtitle(cover):
    """封面 subtitle：抓原文第一段"""
    sub = cover.get("subtitle", "")
    if not _is_hole(sub):
        return False
    candidates = cover.get("_candidates", [])
    if candidates and candidates[0].get("url"):
        text = fetch_text(candidates[0]["url"])
        if text:
            lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 20]
            if lines:
                cover["subtitle"] = lines[0][:80]
                return True
    return False

def _fill_p2(s, series_name):
    """P2 items：抓原文填充 desc/solution"""
    p2 = s.get("p2", {})
    layout = p2.get("type", "")
    changed = False

    if _is_hole(p2.get("title", "")):
        p2["title"] = {"trend": "关键数据", "tool": "为什么需要这个工具？", "brief": "三条动态 值得关注"}.get(series_name, "详情")
        changed = True

    for item in p2.get("items", []):
        url = item.get("_url", "")

        if layout == "news-list" and _is_hole(item.get("desc", "")):
            text = fetch_text(url) if url else ""
            if text:
                item["desc"] = _trim(text.strip()[:120], 100)
                changed = True
        elif layout == "data-list":
            if _is_hole(item.get("title", "")):
                item["title"] = "核心数据"
                changed = True
            if _is_hole(item.get("desc", "")):
                text = fetch_text(url) if url else ""
                if text:
                    item["desc"] = _trim(text.strip()[:120], 100)
                    changed = True
        elif layout == "pain-list":
            if _is_hole(item.get("problem", "")):
                item["problem"] = "传统方法效率低，需要大量人工干预和反复沟通"
                changed = True
            if _is_hole(item.get("solution", "")):
                item["solution"] = "开源方案 · 详见项目主页" if url else "开源方案"
                changed = True

    return changed

def _fill_p3(s, series_name):
    """P3 items：填充占位的 body-list 或 steps"""
    p3 = s.get("p3", {})
    p3_type = p3.get("type", "body-list")
    changed = False

    if _is_hole(p3.get("tag", "")):
        p3["tag"] = {"trend": "行业观察", "brief": "行业观察", "tool": "快速上手"}.get(series_name, "深入")
        changed = True
    if _is_hole(p3.get("title", "")):
        p3["title"] = {"trend": "关键洞察", "brief": "三条信号 一个趋势", "tool": "三步 用起来"}.get(series_name, "总结")
        changed = True

    if p3_type == "steps":
        for item in p3.get("items", []):
            code = item.get("code", "")
            if _is_hole(code) or "待填" in code:
                candidates = p3.get("_candidates", [])
                # 优先找 GitHub URL
                repo_url = ""
                for c in candidates:
                    u = c.get("url", "")
                    if "github.com" in u:
                        repo_url = u
                        break
                if not repo_url and candidates:
                    repo_url = candidates[0].get("url", "")
                if repo_url and "github.com" in repo_url:
                    repo = "/".join(repo_url.replace("https://github.com/", "").split("/")[:2])
                    item["code"] = f"git clone https://github.com/{repo}"
                elif repo_url:
                    item["code"] = f"访问 {repo_url.split('//')[-1][:30]}"
                else:
                    item["code"] = "README / 文档"
        if _is_hole(p3.get("footer", "")):
            p3["footer"] = "开源项目 · MIT"
            changed = True
    else:
        for i, item in enumerate(p3.get("items", [])):
            label, text = item.get("label", ""), item.get("text", "")
            if _is_hole(label) or _is_hole(text):
                # P3 candidates 可能为空，退到 cover/P2 的 URL
                url = ""
                candidates = p3.get("_candidates", [])
                if i < len(candidates) and candidates[i].get("url"):
                    url = candidates[i]["url"]
                if not url:
                    cover_cands = s.get("cover", {}).get("_candidates", [])
                    p2_urls = [it.get("_url", "") for it in s.get("p2", {}).get("items", [])]
                    all_urls = [c.get("url", "") for c in cover_cands] + p2_urls
                    all_urls = [u for u in all_urls if u]
                    if i < len(all_urls):
                        url = all_urls[i]
                if url:
                    t = fetch_text(url)
                    if t:
                        lines = [l.strip() for l in t.split("\n") if l.strip() and len(l.strip()) > 40]
                        if lines:
                            item["label"] = f"深入分析 {i+1}"
                            item["text"] = _trim(re.sub(r'\s+', ' ', lines[0]), 120)
                        else:
                            item["text"] = "详见原文资料。"
                elif not url:
                    item["text"] = "详见原文资料。"
                changed = True

        if _is_hole(p3.get("closing", "")):
            p3["closing"] = "信息的价值不在于获取，而在于判断。今天就到这里。"
            changed = True

    return changed


# ── 主流程 ────────────────────────────────────────────

def main():
    if not TEMPLATE_FILE.exists():
        print(f"[错误] 找不到 {TEMPLATE_FILE}", file=sys.stderr)
        sys.exit(1)

    with open(TEMPLATE_FILE) as f:
        data = json.load(f)

    print(f"\n{'='*50}")
    print(f"  Cardweave 自动编辑 — 填充占位符")
    print(f"{'='*50}\n")

    total = 0
    for sname in ["brief", "trend", "tool"]:
        s = data.get(sname, {})
        if not s:
            continue
        c = 0
        c += _needs_candidates(s, sname)
        c += _fill_tag(s.get("cover", {}), sname)
        c += _fill_title(s.get("cover", {}), sname)
        c += _fill_subtitle(s.get("cover", {}))
        c += _fill_p2(s, sname)
        c += _fill_p3(s, sname)
        print(f"  {sname:6s}: {c} 处填充" if c else f"  {sname:6s}: 无需改动")
        total += c

    with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n  ✅ template.json 已更新（共 {total} 处）\n")


if __name__ == "__main__":
    main()
