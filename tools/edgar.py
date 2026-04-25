from __future__ import annotations

import os
import re
import shutil
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import logging
from typing import Optional

from sec_edgar_downloader import Downloader

logger = logging.getLogger(__name__)

_DL_DIR = "data/edgar_cache"
_EDGAR_UA = "SupplyChainRiskMonitor pal.h@northeastern.edu"
_CACHE_TTL_SECONDS = 7 * 24 * 3600  # re-download after 7 days


def _looks_like_ticker(s: str) -> bool:
    return bool(s) and len(s) <= 5 and re.match(r"^[A-Za-z0-9.\-]+$", s)


def _resolve_company_to_identifier(name_or_ticker: str) -> Optional[str]:
    """
    Given a company name or ticker, return the best identifier for EDGAR.
    - If it already looks like a ticker, return it unchanged.
    - Otherwise, search SEC EDGAR by company name and return the CIK.
    Returns None if nothing is found.
    """
    if _looks_like_ticker(name_or_ticker):
        return name_or_ticker.upper()

    encoded = urllib.parse.quote(name_or_ticker)
    url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        f"?company={encoded}&CIK=&type=10-K&dateb=&owner=include"
        "&count=5&search_text=&action=getcompany&output=atom"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _EDGAR_UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_text = resp.read().decode("utf-8")

        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            entry_id = entry.findtext("atom:id", namespaces=ns) or ""
            m = re.search(r"CIK=0*(\d+)", entry_id)
            if m:
                cik = m.group(1)
                company_title = entry.findtext("atom:title", namespaces=ns) or name_or_ticker
                logger.info("Resolved %r → CIK %s (%s)", name_or_ticker, cik, company_title)
                return cik
    except Exception as exc:
        logger.warning("EDGAR company name resolution failed for %r: %s", name_or_ticker, exc)

    return None


def fetch_edgar_filings(
    company_name_or_ticker: str,
    form_type: str = "10-K",
    limit: int = 3,
) -> list[dict]:
    """Download recent EDGAR filings and return chunked text docs.

    Accepts either a ticker symbol (AAPL) or a plain company name (Apple).
    """
    if not company_name_or_ticker:
        return []

    identifier = _resolve_company_to_identifier(company_name_or_ticker.strip())
    if not identifier:
        logger.warning("Could not resolve %r to an EDGAR identifier", company_name_or_ticker)
        return []

    os.makedirs(_DL_DIR, exist_ok=True)

    ticker_dir = os.path.join(_DL_DIR, "sec-edgar-filings", identifier.upper(), form_type)

    # Evict stale cache so we always fetch recent filings
    if os.path.isdir(ticker_dir):
        newest = max((os.path.getmtime(os.path.join(r, f)) for r, _, fs in os.walk(ticker_dir) for f in fs), default=0)
        if time.time() - newest > _CACHE_TTL_SECONDS:
            logger.info("EDGAR cache for %s expired — clearing and re-downloading", identifier)
            shutil.rmtree(ticker_dir, ignore_errors=True)

    dl = Downloader("SupplyChainRiskMonitor", "pal.h@northeastern.edu", _DL_DIR)

    try:
        dl.get(form_type, identifier, limit=limit)
    except Exception as exc:
        logger.warning("EDGAR download failed for %r: %s", identifier, exc)
        return []
    if not os.path.isdir(ticker_dir):
        return []

    docs = []
    for root, _, files in os.walk(ticker_dir):
        for fname in files:
            if not fname.endswith(".txt"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                for chunk in _chunk_text(text, max_chars=1500):
                    docs.append({
                        "source": f"EDGAR/{company_name_or_ticker}/{form_type}",
                        "text": chunk,
                    })
            except Exception:
                continue

    return docs[:20]


def _chunk_text(text: str, max_chars: int = 1500) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
