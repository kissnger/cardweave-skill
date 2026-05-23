#!/usr/bin/env python3
"""
将 template.json 中的英文内容翻译为中文。
在 curate.py 之后、generate.py 之前运行。

用法：
  python3 scripts/translate.py
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "template.json"

# 翻译表（英文 → 中文）
TRANSLATIONS = {
    # 封面标题
    "AI has a multiplying effect on existing technical skills": "AI 对现有技术技能具有倍增效应",
    "The current AI pricing was always going to go away": "当前 AI 定价模式终将消失",
    "Steve Wozniak cheered after telling students they have AI – actual intelligence": "沃兹尼亚克：学生们有了真正的 AI，值得欢呼",
    "Show HN: Agent.email – sign up via curl, claim with a human OTP": "Agent.email — 用 curl 注册，人工 OTP 认领",
    "Show HN: I Made a Claude Skill for Spec-Driven Development": "我做了一个 Claude Skill 用于规范驱动开发",
    "Show HN: Dari-docs – Optimize your docs using parallel LLM calls": "Dari-docs — 用并行 LLM 调用优化文档",
    "Show HN: Let agents run any analysis with Mixpanel data": "让 AI Agent 直接用 Mixpanel 数据做分析",
    "Show HN: CipherStash Stack – Data Level Access Control": "CipherStash — 数据级访问控制",
    "Show HN: TLS Certificate Management and PKI": "TLS 证书管理与 PKI",
    "Show HN: Spec-Driven Development Workflow for Claude Code": "规范驱动的 Claude Code 开发工作流",
    "Show HN: Prisma Next – data contracts, migration generation": "Prisma Next — 数据合约与迁移生成",
    "Show HN: I Dedicated 4 Years to Mastering Offline Password Manager": "我花了 4 年打造离线密码管理器",
    "Tell HN: I'm tired of AI-generated answers": "受够了 AI 生成的答案",
    "Show HN: Smithereen – an early-Facebook-style Fediverse": "Smithereen — 类 Facebook 的去中心化社交",
    "OpenAI Agents SDK Sandboxes: Which one should you use?": "OpenAI Agents SDK 沙箱对比：该用哪个？",
    "The memory shortage is causing a repricing of consumer electronics": "内存短缺导致消费电子重新定价",
    "Launch HN: Runtime (YC P26) – Sandboxed coding agents": "Runtime (YC P26) — 沙箱化编码 Agent",
    "Launch HN: Superset (YC P26) – IDE for the agents era": "Superset (YC P26) — Agent 时代的 IDE",
    "Ask HN: Failing interviews for mid-level SWE in UK": "英国中级软件工程师面试屡屡失败",
    # 截断标题匹配
    "AI has a multip": "AI 技能倍增",
    "AI has a multiplying effect on": "AI 对技术技能的倍增效应",
    "Steve Wozniak cheered after te": "沃兹尼亚克：AI 值得欢呼",
    "Steve Wozniak cheere": "沃兹尼亚克：AI",
    "Steve Wozniak cheered aft": "沃兹尼亚克演讲",
    "The current AI pricing was always going to": "AI 定价模式变革",
}

def main():
    if not TEMPLATE.exists():
        print(f"[错误] 找不到 {TEMPLATE}")
        return

    with open(TEMPLATE) as f:
        data = json.load(f)

    changed = 0

    def translate(text):
        """逐条翻译"""
        if not isinstance(text, str):
            return text
        # 精确匹配
        if text in TRANSLATIONS:
            return TRANSLATIONS[text]
        # 前缀匹配
        for en, zh in sorted(TRANSLATIONS.items(), key=lambda x: -len(x[0])):
            if text.startswith(en):
                tail = text[len(en):]
                return zh + tail
        return text

    def walk(obj, path=""):
        nonlocal changed
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")
        elif isinstance(obj, str):
            # 只翻译 display 字段，不翻译 url/_candidates 等
            skip_prefixes = ["https://", "http://", "↑", "_", "story_", "author_", "front_page", "show_hn", "dev_keyword", "ai_keyword"]
            if any(obj.startswith(p) for p in skip_prefixes):
                return
            # 只翻译纯英文（不含中文的字符串）
            if re.search(r'[\u4e00-\u9fff]', obj):
                return  # 已有中文
            if not re.search(r'[a-zA-Z]{3,}', obj):
                return  # 不是英文
            translated = translate(obj)
            if translated != obj:
                # 找到父级并修改
                pass

    # 简单粗暴：给已知字段翻译
    def translate_field(parent, field):
        nonlocal changed
        if field in parent and isinstance(parent[field], str):
            t = translate(parent[field])
            if t != parent[field]:
                #print(f"  {parent[field][:30]} → {t[:30]}")
                parent[field] = t
                changed += 1
        if field in parent and isinstance(parent[field], dict):
            for k in parent[field]:
                if isinstance(parent[field][k], str):
                    t = translate(parent[field][k])
                    if t != parent[field][k]:
                        parent[field][k] = t
                        changed += 1

    # 遍历三个系列
    for series in ["brief", "trend", "tool"]:
        s = data.get(series, {})
        # cover 标题
        cover = s.get("cover", {})
        translate_field(cover, "tag")
        translate_field(cover, "subtitle")
        translate_field(cover, "title")
        # p2 items
        p2 = s.get("p2", {})
        for item in p2.get("items", []):
            for k in ["title", "problem", "desc", "solution", "num"]:
                if k in item and isinstance(item[k], str):
                    t = translate(item[k])
                    if t != item[k]:
                        item[k] = t
                        changed += 1
        # p3 items
        p3 = s.get("p3", {})
        for item in p3.get("items", []):
            for k in ["label", "text"]:
                if k in item and isinstance(item[k], str):
                    t = translate(item[k])
                    if t != item[k]:
                        item[k] = t
                        changed += 1

    with open(TEMPLATE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  ✓ 翻译完成，{changed} 处修改")

if __name__ == "__main__":
    main()
