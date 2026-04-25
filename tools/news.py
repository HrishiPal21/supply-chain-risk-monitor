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
