# 公众号文章写作指南

基于 Step 2b 生成的完整中文 .md 文件，为每个分类写一篇公众号长文。

```python
for 系列 in [brief, trend, tool]:
    md = read(f"{日期}/{系列}_01.md")  # 完整翻译好的中文参考
    # 3a. 写公众号文章
    article = compose_article(md)       # 1500-2500 字
    save(f"{日期}/{系列}_article.html")
    # 3b. 填 template.json（海报中文文案）
    fill_template(系列, md)
```

---

## 标题规范

标题决定打开率，占文章成功率的 50%。

**核心原则：** 悬念 + 热点 + 数字 + 冲突，控制在 15-28 字，关键词前置（前 15 字内）。

**各系列标题策略：**

| 系列 | 标题钩子 | 示例 |
|------|----------|------|
| brief | 数字+"信号/变化/真相" | "这周 HN 上的 3 个信号，拼出了 AI 行业最真实的切片" |
| trend | 冲突/对比/反差 | "同一个话题，一个被嘘下台，一个满堂喝彩" |
| tool | 痛点+方案+数字 | "你的 Claude Code 总跑偏？这个开源插件用一个思路解决了" |

**标题自检清单：**
- [ ] 15-28 字，手机端不被截断
- [ ] 核心词在前 15 字内
- [ ] 包含至少一个情绪触发词
- [ ] 目标读者一眼认出"这是写给我的"
- [ ] 标题和内容匹配（不标题党，否则完读率低→算法降权）

---

## 开头规范（前 3 行定生死）

读者在订阅号列表/朋友圈看到标题打开后，前 3 行决定是否继续读。

**可用开头手法（选一种）：**
1. **痛点切入** — 直接抛读者扎心的痛点
2. **悬念/冲突** — 制造信息缺口，激发好奇心
3. **数据冲击** — 用惊人数据抓住注意力
4. **故事开场** — 200 字内讲完一个小故事

**工具类文章推荐痛点切入**（"用 AI 编程代理的痛点，用过的人都懂"）

---

## 正文排版规范

| 要素 | 要求 |
|------|------|
| 保存格式 | `.html`（inline CSS，无 JS，可直接复制到公众号编辑器） |
| 字号 | 16px |
| 行距 | 1.75 倍 |
| 段长 | ≤5 行一段，不要大段文字 |
| 颜色 | 全文 3 色以内（主色+强调色+灰色） |
| 视觉锚点 | 每 300 字设一个（引用块/色块/分割线/表格） |

**视觉元素：**

```
强调区块：
<div style="background: #FFFBEB; border-left: 4px solid #F59E0B; padding: 10px 14px; margin: 16px 0; border-radius: 0 6px 6px 0;">
  <p style="margin: 0; font-size: 14px; color: #92400E;">强调内容</p>
</div>

引用块：
<blockquote style="border-left: 3px solid #D97706; margin: 16px 0; padding: 6px 14px; color: #888;">
  引用内容
</blockquote>

数字对比块（并排）：
<div style="display: flex; gap: 10px; margin: 16px 0;">
  <div style="flex: 1; background: #FEF2F2; border-radius: 8px; padding: 12px; text-align: center;">
    <p style="font-weight: 700; color: #dc2626; margin: 0;">恐吓框架</p>
    <p style="font-size: 12px; color: #991b1b; margin: 0;">"AI 将取代你"</p>
  </div>
  <div style="flex: 1; background: #ECFDF5; border-radius: 8px; padding: 12px; text-align: center;">
    <p style="font-weight: 700; color: #059669; margin: 0;">赋能框架</p>
    <p style="font-size: 12px; color: #065F46; margin: 0;">"你才是智能"</p>
  </div>
</div>
```

**各系列配色：**

| 系列 | 强调色 | 背景色块 | 标签色 |
|------|--------|----------|--------|
| brief | #D97706 / #F59E0B | #FFFBEB | 琥珀 #F59E0B |
| trend | #A855F7 / #7C3AED | #F5F3FF | 紫 #A855F7 |
| tool | #34D399 / #059669 | #ECFDF5 | 绿 #34D399 |

---

## 各系列文章结构

### brief（每日简讯）— 3 条独立新闻串联

```
封面图 → 标题 → 导语
  01 第一条（数据+故事+金句）
  02 第二条（数据+分析+洞察）
  03 第三条（对比+金句+启示）
  卡片海报（3 张）
  结尾串联 → 💬 互动钩子 → 关注引导
```

### trend（商业趋势）— 1-2 个深度分析

```
封面图 → 标题 → 导语
  讲事实（发生了什么）
  分析原因（为什么重要）
  更大信号（折射什么趋势）
  方法论（可复用的公式/框架）
  卡片海报（3 张）
  结尾金句 → 💬 互动钩子 → 关注引导
```

### tool（工具推荐）— 1 个工具深度评测

```
封面图 → 标题 → 导语
  问题（痛点描述）
  方案（工具怎么解决）
  机制（为什么有效）
  适用（谁该试试）
  快速上手（代码/命令）
  卡片海报（3 张）
  选择黄金法则 → 💬 互动钩子 → 关注引导
```

---

## 结尾规范

### 互动钩子

放在关注引导前：

```html
<p style="font-size: 14px; color: #888; margin: 8px 0;">💬 <strong>聊两句</strong>：这里写一个开放性问题引导评论</p>
```

- brief: "这三个信号里，哪个对你触动最大？"
- trend: "如果你是毕业典礼演讲者，会怎么跟学生聊 AI？"
- tool: "你平时用 AI 编程代理最头疼的问题是什么？"

### 关注引导

每篇文章底部统一格式：

```html
<div style="background: linear-gradient(135deg, {主色}, {深色}); border-radius: 10px; padding: 20px; margin: 24px 0; text-align: center;">
  <p style="font-size: 16px; font-weight: 700; color: #fff; margin: 0 0 6px 0;">{Slogan}</p>
  <p style="font-size: 13px; color: rgba(255,255,255,0.8); margin: 0 0 12px 0;">{副标题}</p>
  <p style="font-size: 12px; color: rgba(255,255,255,0.6); margin: 0;">⬇️ 长按识别关注 ⬇️</p>
  <p style="font-size: 12px; color: rgba(255,255,255,0.5); margin: 10px 0 0 0;">觉得不错？点个 <strong style="color: #fff;">在看</strong> 支持一下</p>
</div>
```

**各系列 Slogan：**

| 系列 | Slogan | 副标题 | 渐变色 |
|------|--------|--------|--------|
| brief | 每周三篇 AI 深度解读 | 从 HN 热榜到产业趋势，5 分钟看懂一周动态 | #F59E0B → #D97706 |
| trend | 每周三篇 AI 深度解读 | 从传播策略到产业趋势，帮你重新理解 AI | #A855F7 → #7C3AED |
| tool | 每周推荐一个开源好工具 | 从 HN Show 到 GitHub 热榜，帮你筛选值得用的 AI 工具 | #34D399 → #059669 |

### 参考链接

```html
<p style="font-size: 12px; color: #ccc; text-align: center; margin: 0;">参考资料</p>
<p style="font-size: 12px; color: #ccc; text-align: center; margin: 4px 0 0 0;">
  <a href="..." style="color: #ccc;">来源1</a> · <a href="..." style="color: #ccc;">来源2</a>
</p>
```

---

## 涨粉设计要点

- **每篇提供独立信息增量** — 看完有"学到了/被启发"的感觉，才能驱动转发
- **金句可复制分享** — 文中加粗/突出的句子要能独立传播（如 "AI 不会让你失业，但会用 AI 的同行会让你失业"）
- **互动钩子引发留言** — 留言数多 → 算法推荐权重高
- **海报卡片嵌入文中** — 每篇文章放对应分类的 3 张 9:16 海报截图，长按可保存转发
- **底部二维码位置** — 发布前替换为自己的公众号二维码
