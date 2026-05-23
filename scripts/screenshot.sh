#!/usr/bin/env bash
# 截图 9 张卡片海报
# 用 npx playwright（npm 全局安装的 playwright）

DIR="/Users/kai/workspace/02_hermes_workspace/004_task_card_design_20260517_1702/cardweave-skill/2026-05-22"
OUT="$DIR/screenshots"
mkdir -p "$OUT"

# 编号: 01=trend, 02=tool, 03=brief
# 页码: P1=cover, P2=details, P3=closing

declare -A PAGES
PAGES[1]="trend:01_商业趋势"
PAGES[2]="tool:02_工具推荐"
PAGES[3]="brief:03_每日简讯"

for i in 1 2 3; do
  IFS=':' read -r dir prefix <<< "${PAGES[$i]}"
  for page in cover p2 p3; do
    case $page in
      cover) suffix="P1_封面" ;;
      p2) suffix="P2_详情" ;;
      p3) suffix="P3_金句" ;;
    esac
    html="$DIR/$dir/$page.html"
    png="$OUT/${prefix}_${suffix}.png"
    echo "📸 $html → $png"
    npx playwright screenshot --device-scale-factor=2 "$html" "$png" 2>/dev/null
  done
done

echo ""
echo "✅ 截图完成 → $OUT"
ls -1 "$OUT"/*.png
