#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热点聚合数据抓取脚本 → 生成 data.json
数据源（全部免 Key）：
  GitHub 周榜 : github.com/trending?since=weekly（抓取）
  全球热点   : Hacker News 官方 API
  国内热点   : 百度热搜 API / 今日头条热榜 API / 抖音热点 API
  AI 行业    : arXiv cs.AI RSS / HuggingFace 模型榜 / GitHub AI 项目搜索
单个源失败只降级该源，不影响整体。GitHub Actions 每小时运行一次。
"""
import json
import os
import re
import time
import urllib.parse
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
BJ = timezone(timedelta(hours=8))
S = requests.Session()
S.headers.update(UA)
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def get_json(url, headers=None, timeout=20):
    r = S.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()


def get_text(url, headers=None, timeout=25):
    r = S.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text


# ---------------- GitHub 周榜 ----------------
def fetch_github_trending():
    items = []
    try:
        html = get_text("https://github.com/trending?since=weekly")
        soup = BeautifulSoup(html, "html.parser")
        for art in soup.select("article.Box-row")[:25]:
            a = art.select_one("h2 a")
            if not a:
                continue
            name = a["href"].strip("/")
            desc_tag = art.select_one("p")
            desc = desc_tag.get_text(strip=True) if desc_tag else ""
            lang_tag = art.select_one("[itemprop=programmingLanguage]")
            lang = lang_tag.get_text(strip=True) if lang_tag else ""
            stars_tag = art.select_one('a[href$="/stargazers"]')
            stars = stars_tag.get_text(strip=True).replace(",", "") if stars_tag else ""
            gain = ""
            m = re.search(r"([\d,]+)\s+stars?\s+this\s+week", art.get_text(" "))
            if m:
                gain = "+" + m.group(1)
            items.append({"name": name, "url": f"https://github.com/{name}",
                          "desc": desc, "lang": lang, "stars": stars, "gain": gain})
    except Exception as e:
        print("github trending failed:", e)
    return items


# ---------------- 全球热点（Hacker News） ----------------
def fetch_hn():
    items = []
    try:
        ids = get_json("https://hacker-news.firebaseio.com/v0/topstories.json")[:30]
        for i in ids:
            try:
                it = get_json(f"https://hacker-news.firebaseio.com/v0/item/{i}.json", timeout=10)
            except Exception:
                continue
            if not it or it.get("type") not in ("story",):
                continue
            url = it.get("url") or f"https://news.ycombinator.com/item?id={i}"
            try:
                site = urllib.parse.urlparse(url).netloc.replace("www.", "")
            except Exception:
                site = ""
            items.append({"title": it.get("title", ""), "url": url,
                          "site": site, "points": it.get("score", 0),
                          "source": "Hacker News"})
    except Exception as e:
        print("hn failed:", e)
    return items


# ---------------- 国内热点 ----------------
def fetch_baidu():
    items = []
    try:
        data = get_json("https://top.baidu.com/api/board?platform=pc&tab=realtime")
        for c in data["data"]["cards"][0]["content"][:30]:
            word = c.get("word", "")
            items.append({"title": word,
                          "url": "https://www.baidu.com/s?wd=" + urllib.parse.quote(word),
                          "hot": c.get("hotScore", ""), "source": "百度热搜"})
    except Exception as e:
        print("baidu failed:", e)
    return items


def fetch_toutiao():
    items = []
    try:
        data = get_json("https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
                        headers={"Referer": "https://www.toutiao.com/"})
        for d in data.get("data", [])[:30]:
            title = d.get("Title", "")
            items.append({"title": title,
                          "url": "https://so.toutiao.com/search?keyword=" + urllib.parse.quote(title),
                          "hot": str(d.get("HotValue", "")), "source": "今日头条"})
    except Exception as e:
        print("toutiao failed:", e)
    return items


def fetch_douyin():
    items = []
    try:
        data = get_json("https://www.douyin.com/aweme/v1/web/hot/search/list/"
                        "?device_platform=webapp&aid=6383&channel=channel_pc_web")
        for w in data.get("data", {}).get("word_list", [])[:30]:
            word = w.get("word", "")
            items.append({"title": word,
                          "url": "https://www.douyin.com/search/" + urllib.parse.quote(word),
                          "hot": str(w.get("hot_value", "")), "source": "抖音热点"})
    except Exception as e:
        print("douyin failed:", e)
    return items


# ---------------- AI 行业 ----------------
def fetch_arxiv():
    items = []
    try:
        import xml.etree.ElementTree as ET
        xml = get_text("https://rss.arxiv.org/rss/cs.AI", timeout=25)
        root = ET.fromstring(xml)
        for it in list(root.iter("item"))[:15]:
            title = (it.findtext("title") or "").strip().replace("\n", " ")
            link = (it.findtext("link") or "").strip()
            pub = (it.findtext("pubDate") or "").strip()
            items.append({"title": title, "url": link, "meta": pub[:16], "source": "arXiv"})
    except Exception as e:
        print("arxiv failed:", e)
    return items


def fetch_hf():
    items = []
    try:
        data = get_json("https://huggingface.co/api/models?sort=likes&direction=-1&limit=15")
        for m in data:
            mid = m.get("id", "")
            items.append({"title": mid, "url": f"https://huggingface.co/{mid}",
                          "meta": f"❤ {m.get('likes', 0)}", "source": "HuggingFace"})
    except Exception as e:
        print("hf failed:", e)
    return items


def fetch_github_ai():
    items = []
    try:
        headers = {"Accept": "application/vnd.github+json"}
        if GH_TOKEN:
            headers["Authorization"] = "Bearer " + GH_TOKEN
        q = urllib.parse.quote("topic:machine-learning created:>2026-08-01")
        data = get_json(f"https://api.github.com/search/repositories?q={q}"
                        f"&sort=stars&order=desc&per_page=15", headers=headers)
        for r in data.get("items", []):
            items.append({"title": r["full_name"], "url": r["html_url"],
                          "meta": f"⭐ {r['stargazers_count']} · {r.get('language') or ''}",
                          "source": "GitHub"})
    except Exception as e:
        print("github ai failed:", e)
    return items


def main():
    now = datetime.now(BJ).strftime("%Y-%m-%d %H:%M")
    data = {
        "updated_at": now + "（北京时间）",
        "github": fetch_github_trending(),
        "world": fetch_hn(),
        "china": fetch_baidu() + fetch_toutiao() + fetch_douyin(),
        "ai": fetch_arxiv() + fetch_hf() + fetch_github_ai(),
        "stats": {},
    }
    data["stats"] = {k: len(v) for k, v in data.items() if isinstance(v, list)}
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("wrote", out, data["stats"])


if __name__ == "__main__":
    main()
