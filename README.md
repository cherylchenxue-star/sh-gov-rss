# 上海政策 RSS 聚合器

自动抓取上海市政府部门政策通知，聚合为 **RSS 2.0** 和 **交互式 HTML 预览页**，并支持自动识别政策所属行业标签。

---

## 在线访问

- **预览页**: https://cherylchenxue-star.github.io/sh-gov-rss/
- **RSS 订阅**: https://cherylchenxue-star.github.io/sh-gov-rss/上海政策rss.xml

---

## 数据来源

| 部门 | 页面地址 | 说明 |
|------|---------|------|
| 上海市经信委 | https://www.sheitc.sh.gov.cn/zcfg/ | 政策法规 |
| 上海市经信委专项资金 | https://www.sheitc.sh.gov.cn/zxzjtzgg/index.html | 专项资金通知公告 |
| 上海市发改委 | https://fgw.sh.gov.cn/fgw_zcwj/index.html | 政策文件 |
| 上海市科委 | https://stcsm.sh.gov.cn/zwgk/ | 政务公开 |

---

## 核心特性

- **自动抓取**: 基于 `curl` + `BeautifulSoup` 绕过 Python SSL 问题，稳定抓取政府站点
- **摘要提取**: 自动进入详情页提取正文摘要，在 RSS 和 HTML 中展示
- **行业标签**: 基于 22 个行业关键词自动为政策打上行业标签（集成电路、人工智能、生物医药、新能源等）
- **交互式页面**: 单文件 `index.html`，支持来源筛选、标签筛选、日期范围筛选、搜索排序、手动刷新
- **自动部署**: GitHub Actions 每日定时抓取并部署到 GitHub Pages

---

## 项目结构

```
.
├── sh_policy_rss.py              # 主入口：运行所有抓取器并生成 RSS + HTML
├── requirements.txt              # Python 依赖
├── index.html                    # 生成的交互式预览页（GitHub Pages 入口）
├── 上海政策rss.xml                # 生成的 RSS 文件
├── .github/workflows/build-rss.yml  # GitHub Actions 自动抓取部署
│
└── sh_policy_rss/                # 核心模块
    ├── models.py                 # 数据模型：PolicyItem, FetchResult
    ├── utils.py                  # 工具函数：curl_fetch, 日期解析, 行业标签提取
    ├── fetcher_base.py           # 抓取器基类：含详情页摘要提取与标签自动标注
    ├── build_rss.py              # RSS 2.0 生成器
    ├── build_index.py            # 交互式 HTML 生成器
    └── fetchers/                 # 各站点抓取器
        ├── sh_sheitc_zcfg_fetcher.py   # 上海市经信委 - 政策法规
        ├── sh_sheitc_zxzj_fetcher.py   # 上海市经信委 - 专项资金
        ├── sh_fgw_fetcher.py           # 上海市发改委
        └── sh_stcsm_fetcher.py         # 上海市科委
```

---

## 运行逻辑

1. **抓取列表页**: 每个 `fetcher` 负责解析对应政府部门的列表页，提取标题、链接、发布日期
2. **详情页 enrichment**: `BaseFetcher.enrich_items()` 进入详情页，基于 CSS 选择器提取正文摘要
3. **自动标签**: 根据标题+摘要文本，通过 `extract_industry_tags()` 匹配 22 个行业的关键词，自动打上 `<category>` 标签
4. **生成 RSS**: `build_rss.py` 聚合所有条目，输出标准 RSS 2.0 XML（含 `pubDate`、`source`、`category`）
5. **生成 HTML**: `build_index.py` 输出单文件 `index.html`，内嵌 `window.POLICY_DATA` JSON，前端用原生 JS 实现筛选/排序/刷新
6. **部署**: GitHub Actions 在 Ubuntu 环境下安装依赖后执行 `sh_policy_rss.py -v`，通过 `actions/deploy-pages` 发布到 GitHub Pages

---

## 本地运行

### 环境要求
- Python 3.10+
- 系统已安装 `curl`（Windows/macOS/Linux 通常自带）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行抓取

```bash
python sh_policy_rss.py -v
```

运行后会生成：
- `上海政策rss.xml`
- `index.html`

### 本地预览

```bash
# Python 3
python -m http.server 8080

# 浏览器打开
# http://localhost:8080/index.html
```

---

## GitHub Actions 自动部署

工作流文件：`.github/workflows/build-rss.yml`

触发方式：
- `push` 到 `master` 分支
- 每日北京时间 **10:00** 自动定时运行（`cron: '0 2 * * *'`）
- 手动触发（`workflow_dispatch`）

部署步骤：
1. Checkout 代码
2. Setup Python 3.12
3. 安装依赖（`beautifulsoup4`, `lxml`, `requests`）并安装 Playwright Chromium
4. 运行 `python sh_policy_rss.py -v` 生成最新数据
5. 通过 `actions/configure-pages` + `actions/deploy-pages` 部署到 GitHub Pages

---

## 标签说明

当前支持自动识别的行业标签包括：

生物医药、集成电路、人工智能、新能源汽车、汽车、航空航天、新材料、新能源、智能制造、数字经济、金融科技、节能环保、房地产、教育、农业、商贸消费、文化旅游、科技创新、中小企业、能源电力、交通物流、养老服务

---

## License

MIT
