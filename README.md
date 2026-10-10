# 🔥 热点聚合

每小时自动更新的热点聚合页：GitHub 周榜 / 全球热点 / 国内热点 / AI 行业，全中文界面，部署在 GitHub Pages，零服务器成本。

## 数据来源（全部免 Key）

| 板块 | 数据源 |
|---|---|
| 💻 GitHub 周榜 | github.com/trending?since=weekly |
| 🌍 全球热点 | Hacker News 官方 API |
| 🇨🇳 国内热点 | 百度热搜 API、今日头条热榜、抖音热点 |
| 🤖 AI 行业 | arXiv cs.AI、HuggingFace 模型榜、GitHub AI 项目 |

> 微博/知乎/B 站有反爬，暂未接入；单个源失败会自动降级，不影响其他板块。

## 上线步骤（共 3 步）

### 第 1 步：新建仓库并上传文件
1. 打开 github.com/new，新建一个**公开**仓库（名字随便，如 `trend-dash`），不要勾选 README
2. 把本目录所有文件上传到仓库（网页端 Add file → Upload files，或用 git push）

### 第 2 步：开启 GitHub Pages
1. 进仓库 → Settings → Pages
2. Build and deployment → Source 选 **Deploy from a branch**
3. Branch 选 `main`，目录选 `/(root)`，点 Save
4. 等 1-2 分钟，页面地址会显示在 Pages 设置页顶部（`https://你的用户名.github.io/仓库名/`）

### 第 3 步：开启每小时自动更新
1. 进仓库 → Actions 标签页，点 **I understand my workflows, go ahead and enable them**
2. 以后每小时整点自动抓取并更新 `data.json`；想立刻看到效果就进 Actions → "更新热点数据" → Run workflow 手动跑一次

## 本地预览

```bash
pip install requests beautifulsoup4
python fetch.py        # 生成 data.json
python -m http.server  # 浏览器打开 http://localhost:8000
```

## 文件说明

- `index.html` — 页面（全中文，四 tab）
- `fetch.py` — 抓取脚本，输出 `data.json`
- `data.json` — 数据文件（由 Actions 自动更新，不用手动管）
- `.github/workflows/update.yml` — 每小时定时任务
