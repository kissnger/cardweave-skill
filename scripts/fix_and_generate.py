#!/usr/bin/env python3
"""Fix template.json: dedup brief P2, fix _meta.date, write articles + generate + screenshot"""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "template.json"
OUTPUT = Path("/Users/kai/workspace/02_hermes_workspace/004_task_card_design_20260517_1702/output")

with open(TEMPLATE) as f:
    data = json.load(f)

# Fix date
data["_meta"]["date"] = "2026-05-22"
d = data["_meta"]["date"]

# ── brief ──
b = data["brief"]
b["cover"]["tag"] = "AI & Agent 简讯 · 5月22日"
b["cover"]["title"] = {"pre": "三个信号", "big2": "看清今天的 AI 版图", "highlight": "开源模型库 · 安全攻防 · Agent 看板"}
b["cover"]["subtitle"] = "Models.dev 开源 AI 模型数据库上线 · 多 Agent 系统面临新型注入攻击 · KanBots 重新定义 Agent 协作"
b["p2"]["items"] = [
    {"title": "Models.dev 开源 AI 模型数据库", "desc": "社区驱动的 AI 模型规格、定价和能力数据库。涵盖 Anthropic、OpenAI、Google 等主流厂商。", "_url": "https://github.com/anomalyco/models.dev"},
    {"title": "域伪装注入攻击突破多 Agent 防线", "desc": "新研究揭示域伪装注入攻击可绕过多 Agent LLM 系统的检测机制。", "_url": "https://arxiv.org/abs/2605.22001"},
    {"title": "KanBots：每张卡片跑一个 Agent", "desc": "开源桌面看板，每张卡片调度 Claude Code 或 Codex 在独立工作目录运行。HN 首页 235 分。", "_url": "https://www.kanbots.dev/"}
]
b["p3"]["items"] = [
    {"label": "重要趋势", "text": "AI 生态正在快速成熟——模型信息透明化、安全防护升级、开发工具链重构，三个信号指向同一方向：AI 从实验走向工程化"},
    {"label": "关注焦点", "text": "「看板即 Agent 调度器」理念值得跟进——它可能是 AI 辅助开发从聊天窗口进化到工作流系统的关键一步"}
]
b["p3"]["closing"] = "今天的三个信号：开源生态加速成熟，安全战场悄然升级，开发工具正在被重新定义。"

# ── trend ──
t = data["trend"]
t["cover"]["tag"] = "AI 趋势 · 关键信号"
t["cover"]["title"] = {"pre": "KanBots 让 AI Agent", "big2": "从聊天变成看板系统", "highlight": "每张卡片并行运行 Agent"}
t["cover"]["subtitle"] = "KanBots 是一个开源看板应用，每张卡片可调度 Claude Code 或 Codex 在独立工作目录中并行运行 Agent。支持自动驾驶模式。"
t["p2"]["title"] = "KanBots 核心指标"
t["p2"]["items"] = [
    {"num": "↑235", "title": "HN 热度", "desc": "Hacker News 首页 235 分"},
    {"num": "4", "title": "并行 Agent", "desc": "最多 4 个 Agent 同时在独立分支工作"},
    {"num": "MIT", "title": "完全开源", "desc": "免费使用，本地运行，零遥测"}
]
t["p2"]["source"] = "kanbots.dev"
t["p3"]["items"] = [
    {"label": "趋势信号 1", "text": "Agent 协作从串行转向并行——KanBots 让多个 Agent 在不同工作目录各自为战"},
    {"label": "趋势信号 2", "text": "「看板即界面」正在成为 Agent 时代的新范式——Agent 调度变得可视化"}
]
t["p3"]["closing"] = "Agent 的下一站不是更强的单兵，而是更好的协作系统。"

# ── tool ──
to = data["tool"]
to["cover"]["tag"] = "开源新工具 · 模型数据库"
to["cover"]["title"] = {"pre": "Models.dev", "big2": "开源 AI 模型大全", "highlight": "查模型 · 比价格 · 看能力"}
to["cover"]["subtitle"] = "社区驱动的 AI 模型数据库，覆盖数百个模型规格、定价和能力信息。SST 团队出品。"
to["p2"]["items"] = [
    {"problem": "AI 模型信息碎片化，比价靠人工", "solution": "Models.dev 把各厂商的模型规格、定价、能力统一到 TOML 数据库，API 查询秒出"}
]
to["p3"]["items"] = [
    {"code": "git clone https://github.com/anomalyco/models.dev"},
    {"code": "ls providers/  # 查看已收录厂商"},
    {"code": "cat providers/anthropic/models/claude-sonnet-4.toml"}
]
to["p3"]["footer"] = "开源项目 · MIT · SST 团队"

with open(TEMPLATE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("✓ template.json 修复完成")

# ── Generate ──
OUTPUT.mkdir(parents=True, exist_ok=True)
os.system(f"cd {ROOT} && python3 scripts/generate.py -o {OUTPUT}")