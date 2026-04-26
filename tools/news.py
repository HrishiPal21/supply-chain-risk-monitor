from __future__ import annotations

import time
from datetime import datetime, timedelta
import requests
from typing import Optional
from config import NEWS_API_KEY

_BASE_URL = "https://newsapi.org/v2/everything"
_DELAYS = [2, 4, 8]
_NEWS_LOOKBACK_DAYS = 30


def fetch_news(query: str, page_size: int = 20) -> list[dict]:
    if not NEWS_API_KEY:
        return []

    from_date = (datetime.utcnow() - timedelta(days=_NEWS_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    params = {
        "q": query,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": page_size,
        "from": from_date,
        "apiKey": NEWS_API_KEY,
    }

    last_exc: Optional[Exception] = None
    for attempt, delay in enumerate(_DELAYS, 1):
        try:
            resp = requests.get(_BASE_URL, params=params, timeout=10)
            if resp.status_code == 429 or resp.status_code >= 500:
                last_exc = RuntimeError(f"NewsAPI HTTP {resp.status_code}")
                if attempt < len(_DELAYS):
                    time.sleep(delay)
                continue
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            break
        except requests.RequestException as e:
            last_exc = e
            if attempt < len(_DELAYS):
                time.sleep(delay)
    else:
        raise last_exc or RuntimeError("NewsAPI failed after retries")

    docs = []
    for art in articles:
        text = " ".join(filter(None, [art.get("title", ""), art.get("description", ""), art.get("content", "")]))
        if text.strip():
            docs.append({
                "source": f"NewsAPI/{art.get('source', {}).get('name', 'unknown')}",
                "text": text[:1500],
                "url": art.get("url", ""),
                "published_at": art.get("publishedAt", ""),
            })

    return docs


def fetch_trending_headlines(page_size: int = 6) -> list[dict]:
    """Return trending supply chain headlines.

    Tries NewsAPI first (works on localhost/dev plan). Falls back to RSS feeds
    when NewsAPI is unavailable (e.g. Cloud Run with a free-tier key).
    """
    results = _trending_from_newsapi(page_size)
    if results:
        return results
    return _trending_from_rss(page_size)


def _trending_from_newsapi(page_size: int) -> list[dict]:
    if not NEWS_API_KEY:
        return []
    from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    params = {
        "q": "supply chain disruption OR trade tariff OR logistics disruption OR port congestion OR semiconductor shortage",
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": page_size,
        "from": from_date,
        "apiKey": NEWS_API_KEY,
    }
    try:
        resp = requests.get(_BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [
            {
                "title": a.get("title", "")[:100],
                "desc": a.get("description", "")[:150] or "Recent supply chain news",
                "query": a.get("title", ""),
                "url": a.get("url", ""),
                "published_at": a.get("publishedAt", ""),
                "region": "",
                "company": "",
            }
            for a in articles
            if a.get("title") and "[Removed]" not in a.get("title", "")
        ]
    except Exception:
        return []


def _trending_from_rss(page_size: int) -> list[dict]:
    """Fall back to RSS feeds for trending headlines."""
    try:
        import feedparser
        FEEDS = [
            "https://www.supplychaindive.com/feeds/news/",
            "https://www.freightwaves.com/news/feed",
            "https://www.tradefinanceglobal.com/feed/",
            "https://feeds.reuters.com/reuters/businessNews",
        ]
        results = []
        for url in FEEDS:
            if len(results) >= page_size:
                break
            try:
                resp = requests.get(url, timeout=8, headers={"User-Agent": "SupplyChainRiskMonitor/1.0"})
                feed = feedparser.parse(resp.content)
                for entry in feed.entries[:3]:
                    title = entry.get("title", "")
                    desc = entry.get("summary", "")[:150] or "Recent supply chain news"
                    if title and "[Removed]" not in title:
                        results.append({
                            "title": title[:100],
                            "desc": desc,
                            "query": title,
                            "url": entry.get("link", ""),
                            "published_at": "",
                            "region": "",
                            "company": "",
                        })
                    if len(results) >= page_size:
                        break
            except Exception:
                continue
        return results
    except Exception:
        return []
