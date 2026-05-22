# Cardweave — 每日卡片海报生成器

一键生成 9 张社交媒体卡片海报，三类内容 × 三页。

## 快速使用

```bash
python3 scripts/generate.py          # 用默认模板生成 HTML
python3 scripts/generate.py --screenshot   # 生成 HTML + PNG 截图
```

打开 `{日期}/trend/cover.html` 查看效果。

## 一次性的

```bash
pip3 install --break-system-packages playwright
playwright install chromium
```

## 项目结构

```
assets/base.html        # 设计母版（CSS）
scripts/generate.py     # 生成脚本
templates/template.json # 数据源模板
references/             # 字段参考文档
```

详见 [SKILL.md](SKILL.md) 完整文档。
