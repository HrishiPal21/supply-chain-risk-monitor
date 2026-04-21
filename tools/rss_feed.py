import feedparser
import requests
from datetime import datetime

RSS_FEEDS = {
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    "FT Markets": "https://www.ft.com/rss/home/uk",
    "Supply Chain Dive": "https://www.supplychaindive.com/feeds/news/",
    "FreightWaves": "https://www.freightwaves.com/news/feed",
    "Trade Finance Global": "https://www.tradefinanceglobal.com/feed/",
}

_HEADERS = {"User-Agent": "SupplyChainRiskMonitor/1.0"}


def _fetch_feed(url: str) -> feedparser.FeedParserDict:
    resp = requests.get(url, timeout=8, headers=_HEADERS)
    resp.raise_for_status()
    return feedparser.parse(resp.content)


def fetch_rss(query: str, max_per_feed: int = 5) -> list[dict]:
    keywords = {w.lower() for w in query.split() if len(w) > 3}
    docs = []

    for feed_name, feed_url in RSS_FEEDS.items():
        try:
            feed = _fetch_feed(feed_url)
        except Exception:
            continue

        for entry in feed.entries[:20]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            combined = f"{title} {summary}".lower()

            if not keywords or any(kw in combined for kw in keywords):
                docs.append({
                    "source": f"RSS/{feed_name}",
                    "text": f"{title}. {summary}"[:1500],
                    "url": entry.get("link", ""),
                    "published_at": _parse_date(entry),
                })
                if len([d for d in docs if d["source"] == f"RSS/{feed_name}"]) >= max_per_feed:
                    break

    return docs


def _parse_date(entry) -> str:
    try:
        return datetime(*entry.published_parsed[:6]).isoformat()
    except Exception:
        return ""
