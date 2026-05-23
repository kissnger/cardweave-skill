#!/usr/bin/env python3
"""
每日卡片海报生成器 — Cardweave

用法：
  cd cardweave-skill/
  python3 scripts/generate.py                                    # 生成 HTML
  python3 scripts/generate.py [data.json]                       # 用指定数据源
  python3 scripts/generate.py -o /path/to/output                # 输出到指定目录
  python3 scripts/generate.py --screenshot                      # + PNG 截图

参数：
  data.json          可选，数据源路径。省略则用 templates/template.json
  -o, --output-dir   输出目录。省略则在 skill 根目录下按日期新建文件夹
  --screenshot       生成后自动截图（需 Playwright + Chromium）
"""
import json, os, sys, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # repo root

# ── 1. 解析参数 ──────────────────────────────────────────────
data_path = None
output_dir = None
screenshot = False

i = 1
while i < len(sys.argv):
    a = sys.argv[i]
    if a == "--screenshot":
        screenshot = True
    elif a in ("--output-dir", "-o") and i + 1 < len(sys.argv):
        output_dir = Path(sys.argv[i + 1])
        i += 1
    elif not a.startswith("--") and data_path is None:
        data_path = Path(a)
    i += 1

DATA_FILE = data_path or (ROOT / "templates" / "template.json")
flags = ["--screenshot"] if screenshot else []

if not DATA_FILE.exists():
    print(f"[错误] 找不到数据源文件: {DATA_FILE}", file=sys.stderr)
    sys.exit(1)

with open(DATA_FILE) as f:
    data = json.load(f)

# ── 待填检查 ──────────────────────────────────────────
def _check_placeholder(obj, path=""):
    if isinstance(obj, str) and "待填" in obj:
        print(f"[错误] template.json 中存在\"待填\"占位符 ({path})", file=sys.stderr)
        print(f"  位置: {path} = \"{obj[:50]}\"", file=sys.stderr)
        return True
    if isinstance(obj, dict):
        return any(_check_placeholder(v, f"{path}.{k}") for k, v in obj.items())
    if isinstance(obj, list):
        return any(_check_placeholder(v, f"{path}[{i}]") for i, v in enumerate(obj))
    return False

if _check_placeholder(data):
    print("", file=sys.stderr)
    print("  先用 Tavily 搜原文写中文，填完 template.json 再 generate。", file=sys.stderr)
    sys.exit(1)

date_str = data.get("_meta", {}).get("date")
if not date_str or date_str == "unknown":
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"[提示] 数据源未设置日期，使用今日: {date_str}")

OUT_DIR = (output_dir / date_str) if output_dir else (ROOT / date_str)
if output_dir:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
for slug in ("trend", "tool", "brief"):
    (OUT_DIR / slug).mkdir(parents=True, exist_ok=True)

# ── 2. 读取 CSS ──────────────────────────────────────────────
BASE_FILE = ROOT / "assets" / "base.html"
if not BASE_FILE.exists():
    print(f"[错误] 找不到设计母版: {BASE_FILE}", file=sys.stderr)
    sys.exit(1)

with open(BASE_FILE) as f:
    base_html = f.read()
BASE_CSS = base_html.split("</style>")[0].split("<style>")[1] if "<style>" in base_html else ""


# ── 3. 生成函数 ──────────────────────────────────────────────
def write(slug, filename, body):
    path = OUT_DIR / slug / filename
    page = f"""<!DOCTYPE html>
<html data-series="{slug}"><head><meta charset="UTF-8"><style>
{BASE_CSS.strip()}
</style></head><body>
{body.strip()}
</body></html>
"""
    path.write_text(page)
    try:
        rel = path.relative_to(ROOT)
        print(f"  ✓ {rel}")
    except ValueError:
        print(f"  ✓ {path}")


# ── 4. 生成全部 9 页 ─────────────────────────────────────────
for slug in ("trend", "tool", "brief"):
    s = data[slug]
    c = s["brand"]

    # ── 封面 ──
    d = s["cover"]
    write(slug, "cover.html", f"""<div class="card">
<div class="bg-text">{c['bg_word']}</div>
<div class="card-inner">
<div class="tag">{d['tag']}</div>
<div class="title">{d['title']['pre']}<span class="big2">{d['title']['big2']}</span><br><span class="hl">{d['title']['highlight']}</span></div>
<div class="divider"></div>
<div class="sub">{d['subtitle']}</div>
<div class="footer">{d['footer']}</div>
</div>
</div>""")

    # ── P2 ──
    p2 = s["p2"]
    t = p2.get("type", "")
    if t == "data-list":
        items = "".join(
            f'<div class="d-item"><div class="num">{i["num"]}</div>'
            f'<div class="info"><div class="t">{i["title"]}</div>'
            f'<div class="d">{i["desc"]}</div></div></div>'
            for i in p2["items"]
        )
        write(slug, "p2.html", f"""<div class="card">
<div class="bg-text">DATA</div>
<div class="card-inner">
<div class="page-tag" style="text-align:left">{p2['tag']}</div>
<div class="page-title" style="text-align:left">{p2['title']}</div>
<div class="d-list">{items}</div>
<div class="data-foot-wrap"><div class="data-foot-line"></div><div class="data-foot">来源 · {p2.get('source','')}</div></div>
</div>
</div>""")
    elif t == "pain-list":
        items = "".join(
            f'<div class="t-item"><div class="prob"><span class="mark">◆</span> {i["problem"]}</div>'
            f'<div class="sol">{i["solution"]}</div></div>'
            for i in p2["items"]
        )
        write(slug, "p2.html", f"""<div class="card">
<div class="bg-text">PAIN</div>
<div class="card-inner">
<div class="page-tag" style="text-align:left">{p2['tag']}</div>
<div class="page-title" style="text-align:left">{p2['title']}</div>
<div class="t-list">{items}</div>
</div>
</div>""")
    elif t == "news-list":
        badges = ["①", "②", "③"]
        items = "".join(
            f'<div class="n-item"><div class="n-badge">{badges[i]}</div>'
            f'<div class="n-content"><div class="n-t">{item["title"]}</div>'
            f'<div class="n-d">{item["desc"]}</div></div></div>'
            for i, item in enumerate(p2["items"])
        )
        write(slug, "p2.html", f"""<div class="card">
<div class="bg-text">NEWS</div>
<div class="card-inner">
<div class="page-tag">{p2['tag']}</div>
<div class="page-title">{p2['title']}</div>
<div class="news-list">{items}</div>
</div>
</div>""")
    else:
        print(f"  [!] 未知 p2.type 值: {t}")

    # ── P3 ──
    p3 = s["p3"]
    t3 = p3.get("type", "")
    if t3 == "steps":
        steps = "".join(
            f'<div class="step-c"><span class="step-num">{str(i+1).zfill(2)}</span>'
            f'<div class="t"><span class="hl">$</span> {item["code"]}</div></div>'
            for i, item in enumerate(p3["items"])
        )
        write(slug, "p3.html", f"""<div class="card">
<div class="bg-text">SETUP</div>
<div class="card-inner">
<div class="page-tag">{p3['tag']}</div>
<div class="page-title">{p3['title']}</div>
<div class="steps">{steps}</div>
<div class="footer">{p3.get('footer','')}</div>
</div>
</div>""")
    else:  # body-list (默认)
        items = "".join(
            f'<div class="b-item"><div class="b-l">{i["label"]}</div>'
            f'<div class="b-t">{i["text"]}</div></div>'
            for i in p3["items"]
        )
        bg = "INSIGHT" if slug == "trend" else "VIEW"
        write(slug, "p3.html", f"""<div class="card">
<div class="bg-text">{bg}</div>
<div class="card-inner">
<div class="page-tag">{p3['tag']}</div>
<div class="page-title">{p3['title']}</div>
<div class="body-list">{items}</div>
<div class="closing-wrap"><div class="closing-line"></div><div class="closing">{p3['closing']}</div></div>
</div>
</div>""")

print(f"\n✅ 已生成 9 页 HTML → {OUT_DIR}/")


# ── 5. 截图（可选） ──────────────────────────────────────────
if "--screenshot" in flags:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n❌ 需要安装 Playwright:")
        print("   pip3 install --break-system-packages playwright")
        print("   playwright install chromium")
        sys.exit(1)

    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    SCR_OUT = OUT_DIR / "screenshots"
    SCR_OUT.mkdir(exist_ok=True)

    labels = {
        ("trend", "cover"): "01_P1_商业趋势",
        ("trend", "p2"):    "01_P2_趋势数据",
        ("trend", "p3"):    "01_P3_趋势结论",
        ("tool", "cover"):  "02_P1_工具教程",
        ("tool", "p2"):     "02_P2_工具痛点",
        ("tool", "p3"):     "02_P3_工具上手",
        ("brief", "cover"): "03_P1_每日简讯",
        ("brief", "p2"):    "03_P2_简讯详情",
        ("brief", "p3"):    "03_P3_简讯观察",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 540, "height": 960},
            device_scale_factor=2
        )

        for slug in ("trend", "tool", "brief"):
            for page_name in ("cover", "p2", "p3"):
                html_path = str(OUT_DIR / slug / f"{page_name}.html")
                png_path = str(SCR_OUT / f"{labels[(slug,page_name)]}_{ts}.png")
                page.goto(f"file://{html_path}", wait_until="networkidle")
                page.screenshot(path=png_path, full_page=False)
                print(f"  ✓ {labels[(slug,page_name)]}")

        browser.close()

    print(f"\n✅ 9 张 PNG → {SCR_OUT}/")
