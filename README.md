# SIGNAL Dashboard

公开的科技、财经与 GitHub Skills 新闻情报台。使用 GitHub Actions 定时采集公开 RSS 和 GitHub API 数据，通过 GitHub Pages 自动发布。

## 启用（网页操作）

1. 上传本项目的全部文件到 `Pigghjy/signal-dashboard` 仓库的 `main` 分支，保留 `.github/workflows/daily.yml` 目录结构。**不要上传 `.env`。**
2. 进入 **Settings → Pages → Build and deployment → Source**，选择 **GitHub Actions**。
3. 打开 **Actions → Update and publish SIGNAL → Run workflow**，手动运行一次。
4. 完成后访问：**https://pigghjy.github.io/signal-dashboard/** 。
5. 可选：在 **Settings → Secrets and variables → Actions → New repository secret** 中添加 `OPENAI_API_KEY`，以启用基于标题和 RSS 摘要的 AI 筛选及中文简介；未经配置时，使用关键词初筛并保留 RSS 原文语言。

## 数据说明

- `Link.md`：科技 RSS 源（兼容 `{ url: "..." }` 行或纯 URL 行）
- `Finance_Link.md`：财经 RSS 来源（需要检查各源是否支持公开抓取）
- `public/tech_news.json` / `public/finance_dashboard.json` / `public/github_skills.json`：网页直接读取的自动生成数据
- `scripts/update.py`：采集、日期过滤、去重、评分、GitHub 仓库搜索；不提取新闻正文
- `scripts/prepare_site.py`：从既有的三频道 HTML 模板生成生产首页
- `.github/workflows/daily.yml`：每天北京时间约 08:17 更新并部署；GitHub 定时任务可能延迟

### 关于准确性与能力边界

- 新闻按近 4 天滚动收集；部分 RSS 只展示最新有限篇目，并不能保证全量覆盖。
- 无 `OPENAI_API_KEY` 时 `review_status=keyword_only`，表示**关键词筛选**而非严格 AI 精筛；公司和详情字段为空，不会伪造。
- 有 `OPENAI_API_KEY` 时仅对本轮前 35 条候选调用模型，其他候选走关键词规则。请检查成本与额度。
- GitHub 每天发现最多 3 个公开且标注许可证的候选仓库，不代表都具有可安装的 `SKILL.md`，也不代表已经安全审计。
- `FIRECRAWL_API_KEY` 并非初始自动部署的必要项。正文抓取 / 提取是独立的后续增强功能，不要误以为本仓库已启用。
- 默认不接微信公众号或 X API。需有合规稳定的数据源才能再增加。
- GitHub Pages 免费公开站点，数据公开；勿上传 token、`.env` 或非公开资料。

## 本地运行

```bash
python -m pip install -r requirements.txt
python scripts/prepare_site.py
python scripts/update.py
python -m http.server --directory public 8000
```

浏览器打开 http://localhost:8000 。
