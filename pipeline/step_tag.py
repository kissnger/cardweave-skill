#!/usr/bin/env python3
"""
Cardweave 标签生成 — step_tag.py

读取 working/01_selection.json（curate.py 产出），为每个系列封面生成话题标签。
标签格式：「前缀 · 后缀」，前缀来自 curation.yaml 的 layout.tag，
后缀根据选中条目的标题自动生成有意义的简短话题词。

用法：
  cd cardweave-skill/
  python3 pipeline/step_tag.py -o ../output                     # 生成标签到 working/01_tags.json
  python3 pipeline/step_tag.py -o ../output --update-template   # 同时更新 template.json 的 tag 字段
"""
import json, sys, re
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from config import get_output_dir
RULES_FILE = ROOT / "config" / "curation.yaml"


# ── 话题词提取规则 ──────────────────────────────────────
# 从英文标题中提取关键信息，映射为简短的中文话题词
# 格式: (regex_pattern, chinese_topic)
# 按优先级排列，命中最先匹配的规则

TOPIC_RULES = [
    # AI 能力 / 模型
    (r'(disproved|solved|proved|cracked|breakthrough|milestone|autonomously)', '能力跃进'),
    (r'(open[-\s]?source|github|mit|apache)', '开源项目'),
    (r'(model|LLM|GPT|Claude|Gemini|Mythos)', '模型突破'),

    # 安全
    (r'(attack|injection|evade|breach|hack|vulnerability|security|malicious|camouflaged|certificate)', '安全警示'),
    (r'(supply chain|poison|trojan|worm)', '供应链攻击'),

    # 成本 / 商业
    (r'(cost|expensive|budget|revenue|profit|IPO|layoff|cut|fire|restruct)', '成本警报'),
    (r'(price|pricing|token|inference|compute)', '定价博弈'),

    # 伦理 / 社会
    (r'(employee|track|surveillance|mouse|keystroke|privacy|monitor)', '伦理争议'),
    (r'(layoff|fire|cut.*job|reduc.*workforce)', '就业冲击'),

    # 工具 / 产品
    (r'(sandbox|agent|runtime|orchestrat|workflow)', 'Agent工具'),
    (r'(API|curl|SDK|CLI|package|extension)', 'API优先'),
    (r'(email|mail|inbox|message|communicat)', '效率工具'),
    (r'(database|model.*db|spec|catalog)', '数据基建'),
    (r'(coding|code|developer|program|PR|commit)', '编码效率'),

    # 趋势 / 行业
    (r'(paradigm|shift|transform|revolution|future|trend)', '行业变革'),
    (r'(regulation|executive order|policy|white house|government)', '政策监管'),

    # 通用 fallback：取标题中有意义的关键词
]

# 标题缩写规则：去掉 show/launch/ask/tell HN 前缀
TITLE_CLEAN_RULES = [
    (r'^(Show HN|Launch HN|Ask HN|Tell HN)\s*:\s*', ''),
    (r'\s*[–—].*$', ''),  # 去掉 em dash / 长 dash 后面的部分
]


def clean_title(title):
    """清理标题中的 HN 前缀等噪音"""
    for pat, repl in TITLE_CLEAN_RULES:
        title = re.sub(pat, repl, title)
    return title.strip()


def extract_topic(title):
    """从标题中提取简短话题词"""
    cleaned = clean_title(title)

    # 按规则匹配
    for pat, topic in TOPIC_RULES:
        if re.search(pat, cleaned, re.IGNORECASE):
            return topic

    # fallback: 提取标题前 2-3 个单词
    words = cleaned.split()[:3]
    if len(words) >= 2:
        topic = ' '.join(words[:2])
        if len(topic) > 12:
            topic = words[0]
        return topic
    return words[0] if words else '行业动态'


def generate_tags(date_str, topic_data, config_series):
    """
    为三个系列生成标签
    返回: { 'brief': '...', 'trend': '...', 'tool': '...' }
    """
    tags = {}

    for series_name in ['brief', 'trend', 'tool']:
        entries = topic_data.get(series_name, [])
        if not entries:
            tags[series_name] = None
            continue

        best = entries[0]  # 最高分条目
        title = best.get('title', '')

        # 从 curation.yaml 读取 tag prefix
        prefix = '未知'
        if series_name in config_series:
            tag_template = config_series[series_name].get('cover', {}).get('layout', {}).get('tag', '')
            if '·' in tag_template:
                prefix = tag_template.split('·')[0].strip()

        # 生成 suffix
        if series_name == 'brief':
            # brief 的 suffix 固定为日期
            suffix = date_str
        elif series_name == 'tool':
            # tool 的 suffix 从标题中提取工具名或类别
            suffix = extract_topic(title)
            # 对工具类，优先取工具名（首词，忽略前缀标签）
            words = clean_title(title).split()
            if words:
                first_word = words[0].rstrip(':,;.!?')
                # 项目名（含 . 或 /）或短于 12 字的名称都保留
                if len(first_word) <= 15 or '.' in first_word or '/' in first_word:
                    suffix = first_word
        else:
            # trend 的 suffix 从标题提取话题
            suffix = extract_topic(title)

        tags[series_name] = f"{prefix} · {suffix}"

    return tags


def main():
    update_template = '--update-template' in sys.argv
    output_dir = None

    i = 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a in ("--output-dir", "-o") and i + 1 < len(sys.argv):
            output_dir = Path(sys.argv[i + 1])
            i += 1
        i += 1

if output_dir is None:
    output_dir = get_output_dir()
    print(f"[config] 未指定 -o，从 rules 文件读取 output.base_dir → {output_dir}")
        sys.exit(1)

    # 安全门禁
    OUT_RESOLVED = output_dir.resolve()
    if OUT_RESOLVED == ROOT.resolve() or ROOT.resolve() in OUT_RESOLVED.parents:
        print(f"[错误] 输出路径 {output_dir} 在技能目录树内！", file=sys.stderr)
        print(f"  技能根目录: {ROOT}", file=sys.stderr)
        print(f"  请指定 -o 到技能目录之外", file=sys.stderr)
        sys.exit(1)

    # 确定日期（从 selection.json 或当前日期）
    date_str = datetime.now().strftime('%Y-%m-%d')

    # 查找最新的 selection.json
    topic_file = None
    candidates = sorted(output_dir.glob('*/tmp/01_selection.json'), reverse=True)
    for c in candidates:
        try:
            with open(c) as f:
                data = json.load(f)
            if data.get('date'):
                date_str = data['date']
                topic_file = c
                break
        except (json.JSONDecodeError, KeyError, IOError):
            continue

    if not topic_file or not topic_file.exists():
        print(f'[错误] 未找到 tmp/01_selection.json，先跑 curate.py -o {output_dir}', file=sys.stderr)
        sys.exit(1)

    with open(topic_file) as f:
        topic_data = json.load(f)

    # 读取 curation.yaml 获取 tag 模板
    config_series = {}
    if RULES_FILE.exists():
        try:
            with open(RULES_FILE) as f:
                import yaml
                rules = yaml.safe_load(f)
            config_series = rules.get('curation', {})
        except ImportError:
            pass

    if not config_series:
        config_series = {
            'brief': {'cover': {'layout': {'tag': 'AI & Agent 简讯 · 日期'}}},
            'trend': {'cover': {'layout': {'tag': 'AI 趋势 · 关键信号'}}},
            'tool': {'cover': {'layout': {'tag': '开源新工具 · 分类标签'}}},
        }

    tags = generate_tags(date_str, topic_data, config_series)

    # 写入 tmp/01_tags.json
    out_dir = output_dir / date_str / "tmp"
    out_dir.mkdir(parents=True, exist_ok=True)
    tags_file = out_dir / '01_tags.json'

    output = {
        'date': date_str,
        'tags': tags,
    }
    with open(tags_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'📄 01_tags.json → {tags_file}')
    print()
    for s in ['brief', 'trend', 'tool']:
        tag = tags.get(s)
        if tag:
            entries = topic_data.get(s, [])
            title = entries[0]['title'] if entries else '(无条目)'
            print(f'  {s:6s}: {tag}')
            print(f'         └─ {title[:50]}')
        else:
            print(f'  {s:6s}: (无条目)')
    print()

    # 可选：更新 template.json
    if update_template:
        tmpl_file = ROOT / 'templates/template.json'
        if tmpl_file.exists():
            with open(tmpl_file) as f:
                tmpl = json.load(f)
            for s in ['brief', 'trend', 'tool']:
                if s in tmpl and s in tags and tags[s]:
                    if 'cover' not in tmpl[s]:
                        tmpl[s]['cover'] = {}
                    tmpl[s]['cover']['tag'] = tags[s]
            with open(tmpl_file, 'w', encoding='utf-8') as f:
                json.dump(tmpl, f, ensure_ascii=False, indent=2)
            print('✅ 已更新 template.json 的 tag 字段')

    print()
    print(f'下一步: 读取 tmp/01_selection.json 获取正文 → 写中文')
    print(f'        然后 python3 pipeline/step4_generate.py -o ../output')


if __name__ == '__main__':
    main()
