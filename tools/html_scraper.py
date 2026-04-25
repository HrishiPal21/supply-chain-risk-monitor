"""
HTML scraper using BeautifulSoup.

Sources scraped:
  - Wikipedia      (query-driven search API -> article paragraphs)
  - Supply Chain Dive  (search results -> article bodies)
  - Logistics Management   (search results -> paragraph extraction)

Each returned doc matches the shared format used by all tools:
  {"source": str, "text": str, "url": str, "published_at": str}
"""

from __future__ import annotations

import logging
import re
import time
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
_TIMEOUT = 12
_RETRY_DELAYS = (2, 6)
_MAX_TEXT_CHARS = 1500
_POLITE_DELAY = 1.2


# ---------------------------------------------------------------------------
# HTTP with retry
# ---------------------------------------------------------------------------

def _get(url: str) -> requests.Response:
    last_exc: Exception = RuntimeError(f"No attempts for {url}")
    for delay in (0, *_RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
            if resp.status_code == 429:
                last_exc = RuntimeError(f"Rate limited: {url}")
                continue
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
    raise last_exc


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def _clean_soup(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "header", "footer",
                     "aside", "form", "noscript", "iframe", "button"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()


def _clean_paragraphs(tags) -> str:
    text = " ".join(t.get_text(separator=" ") for t in tags)
    text = re.sub(r"\[\d+\]", "", text)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Wikipedia
# ---------------------------------------------------------------------------

def _fetch_wikipedia(query: str, max_results: int = 3) -> list[dict]:
    search_url = (
        "https://en.wikipedia.org/w/api.php"
        f"?action=query&list=search&srsearch={quote_plus(query)}"
        f"&srlimit={max_results}&format=json&utf8=1"
    )
    resp = _get(search_url)
    hits = resp.json().get("query", {}).get("search", [])

    docs: list[dict] = []
    for hit in hits:
        title: str = hit["title"]
        page_url = f"https://en.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
        try:
            page_resp = _get(page_url)
            soup = BeautifulSoup(page_resp.text, "html.parser")
            content = soup.find("div", {"id": "mw-content-text"})
            if not content:
                continue
            for tag in content.find_all("span", class_="mw-editsection"):
                tag.decompose()
            for tag in content.find_all("sup"):
                tag.decompose()
            paragraphs = content.find_all("p", limit=12)
            text = _clean_paragraphs(paragraphs)
            if len(text) < 150:
                continue
            docs.append({
                "source": "HTML/Wikipedia",
                "text": text[:_MAX_TEXT_CHARS],
                "url": page_url,
                "published_at": "",
            })
            logger.debug("Wikipedia: fetched '%s'", title)
        except Exception as exc:
            logger.debug("Wikipedia page failed (%s): %s", title, exc)

    return docs


# ---------------------------------------------------------------------------
# Supply Chain Dive
# ---------------------------------------------------------------------------

def _fetch_supplychaindive(query: str, max_articles: int = 3) -> list[dict]:
    search_url = f"https://www.supplychaindive.com/search/?q={quote_plus(query)}"
    try:
        resp = _get(search_url)
    except Exception as exc:
        logger.debug("Supply Chain Dive search failed: %s", exc)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    seen: set[str] = set()
    article_urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href: str = a["href"]
        if "/news/" not in href:
            continue
        full = href if href.startswith("http") else f"https://www.supplychaindive.com{href}"
        if full not in seen:
            seen.add(full)
            article_urls.append(full)
        if len(article_urls) >= max_articles:
            break

    docs: list[dict] = []
    for url in article_urls:
        try:
            time.sleep(_POLITE_DELAY)
            page_resp = _get(url)
            page_soup = BeautifulSoup(page_resp.text, "html.parser")

            title_tag = page_soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else ""

            body = (
                page_soup.find("div", class_="article-body")
                or page_soup.find("article")
                or page_soup.find("div", class_=re.compile(r"article-body|post-content", re.I))
            )
            if not body:
                continue

            text = _clean_soup(body)
            if title:
                text = f"{title}. {text}"
            if len(text) < 150:
                continue

            docs.append({
                "source": "HTML/SupplyChainDive",
                "text": text[:_MAX_TEXT_CHARS],
                "url": url,
                "published_at": "",
            })
            logger.debug("SupplyChainDive: fetched '%s'", url)
        except Exception as exc:
            logger.debug("Supply Chain Dive article failed (%s): %s", url, exc)

    return docs


# ---------------------------------------------------------------------------
# Logistics Management
# ---------------------------------------------------------------------------

def _fetch_logisticsmgmt(query: str, max_articles: int = 2) -> list[dict]:
    search_url = f"https://www.logisticsmgmt.com/search?q={quote_plus(query)}"
    try:
        resp = _get(search_url)
    except Exception as exc:
        logger.debug("LogisticsMgmt search failed: %s", exc)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    seen: set[str] = set()
    article_urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href: str = a["href"]
        if not ("/article/" in href or "/news/" in href):
            continue
        full = href if href.startswith("http") else f"https://www.logisticsmgmt.com{href}"
        if full not in seen:
            seen.add(full)
            article_urls.append(full)
        if len(article_urls) >= max_articles:
            break

    docs: list[dict] = []
    for url in article_urls:
        try:
            time.sleep(_POLITE_DELAY)
            page_resp = _get(url)
            page_soup = BeautifulSoup(page_resp.text, "html.parser")

            title_tag = page_soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else ""

            paragraphs = [
                p.get_text(strip=True)
                for p in page_soup.find_all("p")
                if len(p.get_text(strip=True)) > 60
            ]
            text = " ".join(paragraphs)
            text = re.sub(r"\s+", " ", text).strip()
            if title:
                text = f"{title}. {text}"
            if len(text) < 150:
                continue

            docs.append({
                "source": "HTML/LogisticsMgmt",
                "text": text[:_MAX_TEXT_CHARS],
                "url": url,
                "published_at": "",
            })
            logger.debug("LogisticsMgmt: fetched '%s'", url)
        except Exception as exc:
            logger.debug("LogisticsMgmt article failed (%s): %s", url, exc)

    return docs


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def fetch_html_docs(query: str, max_per_source: int = 3) -> list[dict]:
    """Scrape HTML sources for supply-chain context relevant to *query*."""
    docs: list[dict] = []

    try:
        wiki = _fetch_wikipedia(query, max_results=max_per_source)
        docs.extend(wiki)
        logger.info("HTML scraper — Wikipedia: %d docs", len(wiki))
    except Exception as exc:
        logger.warning("Wikipedia scrape failed entirely: %s", exc)

    try:
        scd = _fetch_supplychaindive(query, max_articles=max_per_source)
        docs.extend(scd)
        logger.info("HTML scraper — SupplyChainDive: %d docs", len(scd))
    except Exception as exc:
        logger.warning("Supply Chain Dive scrape failed entirely: %s", exc)

    try:
        lm = _fetch_logisticsmgmt(query, max_articles=max_per_source - 1)
        docs.extend(lm)
        logger.info("HTML scraper — LogisticsMgmt: %d docs", len(lm))
    except Exception as exc:
        logger.warning("LogisticsMgmt scrape failed entirely: %s", exc)

    return docs
