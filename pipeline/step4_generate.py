#!/usr/bin/env python3
"""
卡片生成器 — step4_generate.py

用法：
  cd cardweave-skill/
  python3 pipeline/step4_generate.py -o ../output                # 生成 HTML 到 ../output/{date}/cards/
  python3 pipeline/step4_generate.py [data.json] -o ../output    # 用指定数据源
  python3 pipeline/step4_generate.py -o ../output --screenshot   # 生成 HTML + PNG 截图

必选参数：
  -o, --output-dir   输出基目录（必须在技能目录树外）。产物放在 {output_dir}/{日期}/ 下

可选参数：
  data.json          数据源路径。省略则用 templates/template.json
  --screenshot       生成后自动截图（需 Playwright + Chromium）
"""
import json, os, sys, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from config import get_output_dir  # repo root

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

if output_dir is None:
    output_dir = get_output_dir()
    print(f"[config] 未指定 -o，从 rules 文件读取 output.base_dir → {output_dir}")

OUT_RESOLVED = output_dir.resolve()

# ── 安全门禁：禁止输出到技能目录树内 ────────────────────
if OUT_RESOLVED == ROOT.resolve() or ROOT.resolve() in OUT_RESOLVED.parents:
    print(f"[错误] 输出路径 {output_dir} 在技能目录树内！", file=sys.stderr)
    print(f"  技能根目录: {ROOT}", file=sys.stderr)
    print(f"  请指定 -o 到技能目录之外，例如:", file=sys.stderr)
    print(f"    python3 pipeline/step4_generate.py -o ../output", file=sys.stderr)
    sys.exit(1)

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

# ── 输出目录结构 ────────────────────────────────────────
OUT_DIR = output_dir / date_str
OUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR = OUT_DIR / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)
CARDS_DIR = TMP_DIR / "cards"
CARDS_DIR.mkdir(parents=True, exist_ok=True)
SCR_DIR = OUT_DIR / "screenshots"
SCR_DIR.mkdir(parents=True, exist_ok=True)

SLUG_SEQ = {"trend": "01", "tool": "02", "brief": "03"}
PAGE_LABEL = {"cover": "cover", "p2": "detail", "p3": "insight"}

# ── 2. 读取 CSS ──────────────────────────────────────────────
BASE_FILE = ROOT / "assets" / "base.html"
if not BASE_FILE.exists():
    print(f"[错误] 找不到设计母版: {BASE_FILE}", file=sys.stderr)
    sys.exit(1)

with open(BASE_FILE) as f:
    base_html = f.read()
BASE_CSS = base_html.split("</style>")[0].split("<style>")[1] if "<style>" in base_html else ""


# ── 3. 生成函数 ──────────────────────────────────────────────
def write(slug, page, body):
    """slug: trend/tool/brief, page: cover/p2/p3"""
    card_name = f"{SLUG_SEQ[slug]}_{slug}_{PAGE_LABEL[page]}.html"
    path = CARDS_DIR / card_name
    html = f"""<!DOCTYPE html>
<html data-series="{slug}"><head><meta charset="UTF-8"><style>
{BASE_CSS.strip()}
</style></head><body>
{body.strip()}
</body></html>
"""
    path.write_text(html)
    print(f"  \u2713 cards/{card_name}")


# ── 4. 生成全部 9 页 ─────────────────────────────────────────
for slug in ("trend", "tool", "brief"):
    s = data[slug]
    c = s["brand"]

    # ── 封面 ──
    d = s["cover"]
    write(slug, "cover", f"""<div class=\"card\">
<div class=\"bg-text\">{c['bg_word']}</div>
<div class=\"card-inner\">
<div class=\"tag\">{d['tag']}</div>
<div class=\"title\">{d['title']['pre']}<span class=\"big2\">{d['title']['big2']}</span><br><span class=\"hl\">{d['title']['highlight']}</span></div>
<div class=\"divider\"></div>
<div class=\"sub\">{d['subtitle']}</div>
<div class=\"footer\">{d['footer']}</div>
</div>
</div>""")

    # ── P2 ──
    p2 = s["p2"]
    t = p2.get("type", "")
    if t == "data-list":
        items = "".join(
            f'<div class=\"d-item\"><div class=\"num\">{i["num"]}</div>'
            f'<div class=\"info\"><div class=\"t\">{i["title"]}</div>'
            f'<div class=\"d\">{i["desc"]}</div></div></div>'
            for i in p2["items"]
        )
        write(slug, "p2", f"""<div class=\"card\">
<div class=\"bg-text\">DATA</div>
<div class=\"card-inner\">
<div class=\"page-tag\" style=\"text-align:left\">{p2['tag']}</div>
<div class=\"page-title\" style=\"text-align:left\">{p2['title']}</div>
<div class=\"d-list\">{items}</div>
<div class=\"data-foot-wrap\"><div class=\"data-foot-line\"></div><div class=\"data-foot\">\u6765\u6e90 &middot; {p2.get('source','')}</div></div>
</div>
</div>""")
    elif t == "pain-list":
        items = "".join(
            f'<div class=\"t-item\"><div class=\"prob\"><span class=\"mark\">\u25c6</span> {i["problem"]}</div>'
            f'<div class=\"sol\">{i["solution"]}</div></div>'
            for i in p2["items"]
        )
        write(slug, "p2", f"""<div class=\"card\">
<div class=\"bg-text\">PAIN</div>
<div class=\"card-inner\">
<div class=\"page-tag\" style=\"text-align:left\">{p2['tag']}</div>
<div class=\"page-title\" style=\"text-align:left\">{p2['title']}</div>
<div class=\"t-list\">{items}</div>
</div>
</div>""")
    elif t == "news-list":
        badges = ["\u2460", "\u2461", "\u2462"]
        items = "".join(
            f'<div class=\"n-item\"><div class=\"n-badge\">{badges[i]}</div>'
            f'<div class=\"n-content\"><div class=\"n-t\">{item["title"]}</div>'
            f'<div class=\"n-d\">{item["desc"]}</div></div></div>'
            for i, item in enumerate(p2["items"])
        )
        write(slug, "p2", f"""<div class=\"card\">
<div class=\"bg-text\">NEWS</div>
<div class=\"card-inner\">
<div class=\"page-tag\">{p2['tag']}</div>
<div class=\"page-title\">{p2['title']}</div>
<div class=\"news-list\">{items}</div>
</div>
</div>""")
    else:
        print(f"  [!] \u672a\u77e5 p2.type \u503c: {t}")

    # ── P3 ──
    p3 = s["p3"]
    t3 = p3.get("type", "")
    if t3 == "steps":
        steps = "".join(
            f'<div class=\"step-c\"><span class=\"step-num\">{str(i+1).zfill(2)}</span>'
            f'<div class=\"t\"><span class=\"hl\">$</span> {item["code"]}</div></div>'
            for i, item in enumerate(p3["items"])
        )
        write(slug, "p3", f"""<div class=\"card\">
<div class=\"bg-text\">SETUP</div>
<div class=\"card-inner\">
<div class=\"page-tag\">{p3['tag']}</div>
<div class=\"page-title\">{p3['title']}</div>
<div class=\"steps\">{steps}</div>
<div class=\"footer\">{p3.get('footer','')}</div>
</div>
</div>""")
    else:  # body-list (默认)
        items = "".join(
            f'<div class=\"b-item\"><div class=\"b-l\">{i["label"]}</div>'
            f'<div class=\"b-t\">{i["text"]}</div></div>'
            for i in p3["items"]
        )
        bg = "INSIGHT" if slug == "trend" else "VIEW"
        write(slug, "p3", f"""<div class=\"card\">
<div class=\"bg-text\">{bg}</div>
<div class=\"card-inner\">
<div class=\"page-tag\">{p3['tag']}</div>
<div class=\"page-title\">{p3['title']}</div>
<div class=\"body-list\">{items}</div>
<div class=\"closing-wrap\"><div class=\"closing-line\"></div><div class=\"closing\">{p3['closing']}</div></div>
</div>
</div>""")

print(f"\n\u2705 \u5df2\u751f\u6210 9 \u9875 HTML \u2192 {CARDS_DIR}/")


# ── 5. 截图（可选） ──────────────────────────────────────────
if "--screenshot" in flags:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n\u274c \u9700\u8981\u5b89\u88c5 Playwright:")
        print("   pip3 install --break-system-packages playwright")
        print("   playwright install chromium")
        sys.exit(1)

    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    labels = {
        ("trend", "cover"): "01_trend_cover",
        ("trend", "p2"):    "01_trend_detail",
        ("trend", "p3"):    "01_trend_insight",
        ("tool", "cover"):  "02_tool_cover",
        ("tool", "p2"):     "02_tool_detail",
        ("tool", "p3"):     "02_tool_insight",
        ("brief", "cover"): "03_brief_cover",
        ("brief", "p2"):    "03_brief_detail",
        ("brief", "p3"):    "03_brief_insight",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 540, "height": 960},
            device_scale_factor=2
        )

        for slug in ("trend", "tool", "brief"):
            for page_name in ("cover", "p2", "p3"):
                card_name = f"{SLUG_SEQ[slug]}_{slug}_{PAGE_LABEL[page_name]}.html"
                html_path = str(CARDS_DIR / card_name)
                png_name = f"{labels[(slug,page_name)]}_{ts}.png"
                png_path = str(SCR_DIR / png_name)
                page.goto(f"file://{Path(html_path).resolve()}", wait_until="networkidle")
                page.screenshot(path=png_path, full_page=False)
                print(f"  \u2713 {png_name}")

        browser.close()

    print(f"\n\u2705 9 \u5f20 PNG \u2192 {SCR_DIR}/")
