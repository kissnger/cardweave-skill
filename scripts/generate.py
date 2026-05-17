#!/usr/bin/env python3
"""
每日卡片海报生成器
用法：
  cd cardweave-skill/
  python3 scripts/generate.py                     # 只生成 HTML
  python3 scripts/generate.py --screenshot        # 生成 HTML + 截图（需 Playwright + Chromium）
"""
import json, os, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # repo root

# 1. 读数据源
DATA_FILE = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else f"{HERE}/../templates/template.json"
with open(DATA_FILE) as f:
    data = json.load(f)

date_str = data.get("_meta", {}).get("date", "unknown")
OUT_DIR = f"{ROOT}/{date_str}"
os.makedirs(OUT_DIR, exist_ok=True)
for s in ("trend", "tool", "brief"):
    os.makedirs(f"{OUT_DIR}/{s}", exist_ok=True)

# 2. 读 base.css
with open(f"{HERE}/../assets/base.html") as f:
    base_html = f.read()
BASE_CSS = base_html.split("</style>")[0].split("<style>")[1] if "<style>" in base_html else ""

# 3. 生成全部 9 页
def write(slug, filename, body):
    path = f"{OUT_DIR}/{slug}/{filename}"
    with open(path, 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html data-series="{slug}"><head><meta charset="UTF-8"><style>
{BASE_CSS.strip()}
</style></head><body>
{body.strip()}
</body></html>
""")
    print(f"  {path}")

for slug in ("trend", "tool", "brief"):
    s = data[slug]
    c = s["brand"]
    d = s["cover"]

    # 封面
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

    # P2 — 根据 type 选择模板
    p2 = s["p2"]
    t = p2.get("type", "")
    if t == "data-list":
        items = "".join(f'<div class="d-item"><div class="num">{i["num"]}</div><div class="info"><div class="t">{i["title"]}</div><div class="d">{i["desc"]}</div></div></div>' for i in p2["items"])
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
        items = "".join(f'<div class="t-item"><div class="prob"><span class="mark">\u25c6</span> {i["problem"]}</div><div class="sol">{i["solution"]}</div></div>' for i in p2["items"])
        write(slug, "p2.html", f"""<div class="card">
<div class="bg-text">PAIN</div>
<div class="card-inner">
<div class="page-tag" style="text-align:left">{p2['tag']}</div>
<div class="page-title" style="text-align:left">{p2['title']}</div>
<div class="t-list">{items}</div>
</div>
</div>""")
    elif t == "news-list":
        badges = ["\u2460","\u2461","\u2462"]
        items = "".join(f'<div class="n-item"><div class="n-badge">{badges[i]}</div><div class="n-content"><div class="n-t">{item["title"]}</div><div class="n-d">{item["desc"]}</div></div></div>' for i,item in enumerate(p2["items"]))
        write(slug, "p2.html", f"""<div class="card">
<div class="bg-text">NEWS</div>
<div class="card-inner">
<div class="page-tag">{p2['tag']}</div>
<div class="page-title">{p2['title']}</div>
<div class="news-list">{items}</div>
</div>
</div>""")

    # P3
    p3 = s["p3"]
    t3 = p3.get("type", "")
    if t3 == "steps":
        steps = "".join(f'<div class="step-c"><span class="step-num">{str(i+1).zfill(2)}</span><div class="t"><span class="hl">$</span> {item["code"]}</div></div>' for i,item in enumerate(p3["items"]))
        write(slug, "p3.html", f"""<div class="card">
<div class="bg-text">SETUP</div>
<div class="card-inner">
<div class="page-tag">{p3['tag']}</div>
<div class="page-title">{p3['title']}</div>
<div class="steps">{steps}</div>
<div class="footer">{p3.get('footer','')}</div>
</div>
</div>""")
    else:
        # body-list (默认)
        items = "".join(f'<div class="b-item"><div class="b-l">{i["label"]}</div><div class="b-t">{i["text"]}</div></div>' for i in p3["items"])
        write(slug, "p3.html", f"""<div class="card">
<div class="bg-text">{'INSIGHT' if slug=='trend' else 'VIEW'}</div>
<div class="card-inner">
<div class="page-tag">{p3['tag']}</div>
<div class="page-title">{p3['title']}</div>
<div class="body-list">{items}</div>
<div class="closing-wrap"><div class="closing-line"></div><div class="closing">{p3['closing']}</div></div>
</div>
</div>""")

print(f"\n\u5df2\u751f\u6210 9 \u9875 HTML \u2192 {OUT_DIR}/")

# 4. 截图（可选）
if "--screenshot" in sys.argv:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n\u9700\u8981\u5b89\u88c5 Playwright: pip3 install --break-system-packages playwright && playwright install chromium")
        sys.exit(1)

    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    SCR_OUT = f"{ROOT}/{date_str}/screenshots"
    os.makedirs(SCR_OUT, exist_ok=True)
    labels = {
        ("trend","cover"): "01_P1_商业趋势",
        ("trend","p2"):    "01_P2_趋势数据",
        ("trend","p3"):    "01_P3_趋势结论",
        ("tool","cover"):  "02_P1_工具教程",
        ("tool","p2"):     "02_P2_工具痛点",
        ("tool","p3"):     "02_P3_工具上手",
        ("brief","cover"): "03_P1_每日简讯",
        ("brief","p2"):    "03_P2_简讯详情",
        ("brief","p3"):    "03_P3_简讯观察",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 540, "height": 960}, device_scale_factor=2)

        for slug in ("trend","tool","brief"):
            for page_name in ("cover","p2","p3"):
                html_path = f"{OUT_DIR}/{slug}/{page_name}.html"
                png_path = f"{SCR_OUT}/{labels[(slug,page_name)]}_{ts}.png"
                page.goto(f"file://{html_path}", wait_until="networkidle")
                page.screenshot(path=png_path, full_page=False)
                print(f"  \u2713 {labels[(slug,page_name)]}")

        browser.close()

    print(f"\n9 \u5f20 PNG \u2192 {SCR_OUT}/")
