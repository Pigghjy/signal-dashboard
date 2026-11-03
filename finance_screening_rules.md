# SIGNAL · 综合财经情报筛选规范 v1.0

## 定位与兼容性

覆盖宏观（macro）、股票及上市公司（equity）、创投与私募融资（venture）。与原科技新闻链路兼容：`score` 仍只取数字 0 或 1；新增 `priority`（0–3）、`category`、`event_type`、`assets`、`impact_direction`、`reason` 等财经字段。现有基于 `score == 1` 的 Firecrawl 抓取脚本无需修改。不要将重要度编码为 `score=2`。

## 判断顺序

1. **有效性**：是否有可核验的具体事件、明确主体和时间？纯观点、旧闻复述、标题党、无实质事实的预测 → 0。
2. **新颖性**：是否有新增数据、决定、公告、交易或可辨识的重大变化？纯行情复盘、无解释的涨跌、把同一消息换标题重发 → 0。
3. **赛道**：按核心事件划为 `macro`、`equity`、`venture`；交叉事件用一个主分类，可在 `tags` 标记其他赛道。
4. **实质性**：事件是否足以改变对经济、企业基本面、融资环境或行业格局的判断？基于已知信息合理判断，不用价格涨跌幅作唯一依据。
5. **可信度**：区分正式公告/官方数据、可靠媒体报道、未经证实的传闻。重要但未证实的传闻默认 0，除非有足够明确且可核验的事件价值；如保留应注明未证实。
6. **重要度**：保留事件按影响范围和新信息强度给 `priority` 1、2、3。

## 宏观 macro

**保留**：央行利率、资产购买及流动性工具的实质变化；CPI/PCE、就业、GDP、PMI 等重要新数据与显著预期差；重大财政预算、税制、关税或贸易措施的实际决定；信用或流动性系统性风险；影响跨市场定价的重要汇率与资本流动机制变化。

**过滤**：仅预告经济数据日历、官员重复措辞、普通观点评论、无新信息的盘面走势、模糊政策传闻。

## 股票 equity

**保留**：显著超/低预期的经营业绩与业绩指引变动；重大并购或资产出售；核心产品订单/商业模式转变；IPO、退市或重大再融资；影响持续经营的重大违约、会计问题或已确认的监管措施；行业性供需/价格冲击。

**过滤**：仅股价涨跌、机构目标价微调、例行分红/回购（除非规模或政策具结构性影响）、无实质变化的季度业绩新闻、普通人事消息。

## 创投 venture

**保留**：种子轮至后期轮融资且披露业务方向、金额、领投方或关键产品；重要收购/退出；揭示新赛道、新商业模式或技术路线的融资；影响创业生态的有实质内容的新基金或融资平台。

**过滤**：无具体事实的“某赛道很热”、融资传闻未获确认、宣传性创业者采访、普通招聘扩张、无法判断业务方向的模糊融资快讯。

## 评分及优先级

- `score=0, priority=0`：过滤。
- `score=1, priority=1`：值得存档、对某公司或细分赛道有明确增量。
- `score=1, priority=2`：可能显著影响行业、重要资产或宏观预期。
- `score=1, priority=3`：重大政策意外、系统性风险、极具影响的企业/交易事件，适合优先推送。

优先级不是交易建议，也不能由股价波动机械推导。`impact_direction` 仅可为 `positive`、`negative`、`mixed`、`unclear`；表示**可能影响的方向**，并应注明是事实还是分析判断。

## LLM 逐条筛选 Prompt

你是一名严格的综合财经新闻筛选分析师，仅根据输入的一条 RSS 新闻 `title` 与 `summary` 判定。先判断有无可核验的新事件，再按 macro / equity / venture 分类，最后按上方规则给出 score 与 priority。禁止假设文章正文内容；信息不足时 score=0。不要将普通涨跌新闻当成重大催化剂；勿把传闻写成已确认事实。

输入：`{{item_json}}`

仅输出合法 JSON，不要代码围栏或解释：

```json
{
  "item_id": "<原样返回>",
  "score": 0,
  "priority": 0,
  "category": "macro",
  "event_type": "other",
  "assets": [],
  "impact_direction": "unclear",
  "reason": "一句中文理由"
}
```

约束：`score` ∈ {0,1}；`priority` ∈ {0,1,2,3}；score=0 时 priority=0；score=1 时 priority≥1。`category` 仅取 `macro`、`equity`、`venture`、`other`；`event_type` 用简短 snake_case，例如 `rate_decision`、`inflation_release`、`earnings_guidance`、`merger_acquisition`、`funding_round`；`assets` 是明确提及或直接相关的资产/市场字符串数组，不能凭空生成 ticker。无法判断方向用 `unclear`。

## 正文提取 Prompt（仅对 score=1）

你是财经事件信息抽取分析师。只根据给定文章 Markdown 正文提取事实和分析，准确区分两者，保留原文数值、币种、时间、同比/环比口径、市场预期与实际值，不制造预期差、影响方向或投资结论。

输入：`{{article_json}}`

仅输出合法 JSON：

```json
{
  "item_id": "<原样返回>",
  "company": [],
  "brief": "一句中文事实摘要",
  "details": "简介：...\n要点：①**发生了什么**：...②**关键数字**：...③**市场关联**：..."
}
```

宏观事件允许 `company=[]`；政府/央行等直接参与组织可列入公司/组织数组，标准化名称。若没有足够事实，诚实写明；不得填补缺失数字。详情最后若分析潜在影响，明确用“可能”措辞。每篇文章独立调用一次模型。

## 数据整合约定

1. RSS item 的 ID 沿用 `news_` + SHA1(`source_url + "\n" + link`) 前 12 位；从头到尾不重新编号。
2. 保留 `source_url/title/link/pub_date/summary`，按 `item_id` 合并 score 与正文提取结果。
3. `score=0` 不进入最终精选数据。相同 link 的跨 RSS 条目可在抓取层按 link 去重，保留全部 item_id 映射；不能在合并时丢失来源。
4. Dashboard 通用字段：`item_id`, `channel`, `source_url`, `title`, `link`, `pub_date`, `summary`, `company`, `brief`, `details`, `score`。财经额外使用 `priority`, `category`, `event_type`, `assets`, `impact_direction`, `reason`。
5. 严格区分 RSS 发布时间和新闻事件发生时间；筛选日期一律按 `pub_date`，如指定时间段。
