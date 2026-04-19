import requests
from config import NEWS_API_KEY

_BASE_URL = "https://newsapi.org/v2/everything"


def fetch_news(query: str, page_size: int = 20) -> list[dict]:
    """Fetch recent news articles from NewsAPI and return doc chunks."""
    if not NEWS_API_KEY:
        return []

    params = {
        "q": query,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
    }

    try:
        resp = requests.get(_BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
    except Exception:
        return []

    docs = []
    for art in articles:
        text = " ".join(
            filter(None, [art.get("title", ""), art.get("description", ""), art.get("content", "")])
        )
        if text.strip():
            docs.append(
                {
                    "source": f"NewsAPI/{art.get('source', {}).get('name', 'unknown')}",
                    "text": text[:1500],
                    "url": art.get("url", ""),
                    "published_at": art.get("publishedAt", ""),
                }
            )

    return docs
