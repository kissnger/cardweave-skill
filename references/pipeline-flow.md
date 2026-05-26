# Pipeline Flow Reference

## 5 步管道

| Step | 脚本 | Input | Rule | Output |
|------|------|-------|------|--------|
| 0 | step0_setup.py | 无 | _meta.date = datetime.now() | templates/template.json（空骨架） |
| 1 | step1_search.py | config/curation.yaml | 4源OR合并, story_id去重, 48h窗口 | cardweave_db.json |
| 2 | step2_curate.py | DB + config/curation.yaml + template._meta.date | min_points + max_candidates分系列；跨源去重 | output/{date}/选题.json |
| 3 | Agent手动 | 选题.json | 正文≤500字；中文标题/描述/金句 | 正文.md + template.json(中文) + 3篇公众号文章 |
| 4 | step4_generate.py -o ../output | template.json + base.html | 递归检查"待填"门禁；-o 必选 + 技能树外检测 | ../output/{_meta.date}/ 9页HTML |
| 5 | generate.py --screenshot / Playwright | 9页HTML | 540×960@2x | 9张PNG |
| 5b | Agent手动patch | 3篇公众号文章 | img src从HTML改为实际PNG路径 | 文章图片可正常显示 |

## 日期传递

setup.py → template.json._meta.date = 今天
curate.py 只读这个日期（不改）
generate.py 用这个日期做输出子目录名

## 产出物关系

选题.json（原始条目+URL）
  → Agent获取正文 → 正文/{series}_{n}.md（≤500字）
  → Agent填写 → template.json（中文三段式标题 + 中文p2/p3 + 三步命令）
  → Agent写文章 → {series}_article.html（3篇）
  → generate.py → 9页HTML
  → Playwright → 9张PNG
