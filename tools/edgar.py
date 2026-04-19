import os
import re
from sec_edgar_downloader import Downloader


_DL_DIR = "data/edgar_cache"


def fetch_edgar_filings(company_ticker: str, form_type: str = "10-K", limit: int = 3) -> list[dict]:
    """Download recent EDGAR filings and return chunked text docs."""
    if not company_ticker:
        return []

    os.makedirs(_DL_DIR, exist_ok=True)
    dl = Downloader("SupplyChainRiskMonitor", "pal.h@northeastern.edu", _DL_DIR)

    try:
        dl.get(form_type, company_ticker, limit=limit)
    except Exception:
        return []

    docs = []
    ticker_dir = os.path.join(_DL_DIR, "sec-edgar-filings", company_ticker.upper(), form_type)
    if not os.path.isdir(ticker_dir):
        return []

    for root, _, files in os.walk(ticker_dir):
        for fname in files:
            if not fname.endswith(".txt"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                for chunk in _chunk_text(text, max_chars=1500):
                    docs.append({"source": f"EDGAR/{company_ticker}/{form_type}", "text": chunk})
            except Exception:
                continue

    return docs[:20]


def _chunk_text(text: str, max_chars: int = 1500) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
