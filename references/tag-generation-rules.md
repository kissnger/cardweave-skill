# Tag Generation Rules (step_tag.py)

Automatically generates Chinese topic tags for card series covers by matching the top entry's title against keyword rules.

## Tag Format

`[prefix] · [suffix]`

- **Prefix**: from `curation.yaml` → `series.cover.layout.tag` (first part before `·`)
- **Suffix**: auto-generated per series rules

## Per-Series Logic

| Series | Suffix Strategy |
|--------|----------------|
| brief | Always `{date}` (e.g. `2026-05-23`) |
| trend | Extract from first 2-3 keywords of cleaned title |
| tool | First word of cleaned title if ≤15 chars or contains `.`/`/`; otherwise keyword match |

## Topic Rule Priority (trend/tool fallback)

Rules checked in order; first match wins. Rules capture the most salient topic for card readers.

| Keyword Pattern | Chinese Topic | Example |
|-----------------|---------------|---------|
| `disproved/solved/proved/cracked/breakthrough/milestone/autonomously` | 能力跃进 | OpenAI model disproves conjecture |
| `open-source/github/mit/apache` | 开源项目 | |
| `model/LLM/GPT/Claude/Gemini/Mythos` | 模型突破 | |
| `attack/injection/evade/breach/hack/vulnerability` | 安全警示 | Domain-camouflaged injection |
| `supply chain/poison/trojan/worm` | 供应链攻击 | TeamPCP worm |
| `cost/expensive/budget/revenue/profit/IPO/layoff` | 成本警报 | Microsoft AI cost problem |
| `employee/track/surveillance/mouse/keystroke/privacy` | 伦理争议 | Meta tracking employees |
| `sandbox/agent/runtime/orchestrat/workflow` | Agent工具 | Runtime sandboxed agents |
| `API/curl/SDK/CLI/package/extension` | API优先 | Agent.email |
| `email/mail/inbox` | 效率工具 | |
| `database/model.*db/spec/catalog` | 数据基建 | Models.dev |
| `coding/code/developer/PR/commit` | 编码效率 | |
| `paradigm/shift/transform/revolution` | 行业变革 | |
| `regulation/executive order/policy/white house` | 政策监管 | White House AI EO |
| (no match) | First 2-3 title words | Fallback |

## Title Cleaning

Before matching, titles are cleaned:
1. Strip `Show HN:`, `Launch HN:`, `Ask HN:`, `Tell HN:` prefixes
2. Strip content after em dash / long dash (`–`/`—`)
