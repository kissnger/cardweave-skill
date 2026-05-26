# Cardweave — 每日卡片海报生成器

一键生成 9 张 AI/Agent 新闻卡片海报（3 类 × 3 页），适配社交媒体分享和公众号配图。

## 安装

```bash
git clone https://github.com/kissnger/cardweave-skill
cd cardweave-skill/
```

无需 API Key。所有数据来自 Algolia HN Search 免费 API。

## 一键运行

```bash
python3 pipeline/step1_search.py     # 搜索 → 入库
python3 pipeline/step2_curate.py     # 出选题
python3 pipeline/step4_generate.py -o ../output   # 生成 9 页 HTML 到 ../output/{date}/
```

打开 `{日期}/trend/cover.html` 看效果。

## 可选：PNG 截图

需要 Playwright + Chromium：

```bash
npm install -g playwright
npx playwright install chromium
python3 pipeline/step4_generate.py -o ../output --screenshot
```

截图输出到 `{日期}/screenshots/`。

## 项目结构

```
assets/base.html        # CSS 母版（颜色变量体系）
pipeline/              # 管道脚本（按序号执行）
templates/template.json # 数据源（pipeline 目标文件）
lib/                    # 共享模块（hn_search + screenshot）
references/             # 字段文档 + 流程图
config/curation.yaml    # 策展规则（搜索源 · 筛选 · 布局）
```

完整文档见 [SKILL.md](SKILL.md)（给 AI Agent 读的详细操作手册）。

## 许可证

MIT
