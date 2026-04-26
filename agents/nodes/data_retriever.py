import uuid
import logging
from agents.state import AgentState

logger = logging.getLogger(__name__)
from tools.edgar import fetch_edgar_filings
from tools.html_scraper import fetch_html_docs
from tools.news import fetch_news
from tools.rss_feed import fetch_rss
from tools.pinecone_client import search_pinecone, upsert_docs
from tools.gcs_client import upload_raw_docs
from tools.doc_ranker import rank_docs


def data_retriever(state: AgentState) -> AgentState:
    query = state["query"]
    company = state.get("company") or ""
    failed_sources: list[str] = []
    source_errors: dict[str, str] = {}

    try:
        news_docs = fetch_news(query)
    except Exception as e:
        news_docs = []
        failed_sources.append("NewsAPI")
        source_errors["NewsAPI"] = str(e)
        logger.warning("NewsAPI fetch failed: %s", e)

    try:
        rss_docs = fetch_rss(query)
    except Exception as e:
        rss_docs = []
        failed_sources.append("RSS")
        source_errors["RSS"] = str(e)
        logger.warning("RSS fetch failed: %s", e)

    try:
        html_docs = fetch_html_docs(query)
    except Exception as e:
        html_docs = []
        failed_sources.append("HTML Scraper")
        source_errors["HTML Scraper"] = str(e)
        logger.warning("HTML scraper failed: %s", e)

    if company:
        try:
            edgar_docs = fetch_edgar_filings(company)
        except Exception as e:
            edgar_docs = []
            failed_sources.append("EDGAR")
            source_errors["EDGAR"] = str(e)
            logger.warning("EDGAR fetch failed for %r: %s", company, e)
    else:
        edgar_docs = []

    raw_docs = news_docs + rss_docs + html_docs + edgar_docs
    for doc in raw_docs:
        doc.setdefault("id", uuid.uuid4().hex)

    try:
        upload_raw_docs(raw_docs, query)
    except Exception as e:
        source_errors["GCS"] = str(e)
        logger.info("GCS upload skipped (bucket not configured or unavailable): %s", e)

    # Upsert only authoritative sources — EDGAR filings + top news/RSS.
    # HTML scraper chunks are used locally for context but not indexed in Pinecone
    # (low signal, high volume, inflates embedding costs).
    upsert_candidates = edgar_docs + news_docs[:10] + rss_docs[:5]
    try:
        upsert_docs(upsert_candidates)
    except Exception as e:
        failed_sources.append("Pinecone/upsert")
        source_errors["Pinecone/upsert"] = str(e)
        logger.warning("Pinecone upsert failed: %s", e)

    try:
        pinecone_docs = search_pinecone(query, top_k=15)
    except Exception as e:
        pinecone_docs = []
        failed_sources.append("Pinecone/search")
        source_errors["Pinecone/search"] = str(e)
        logger.warning("Pinecone search failed: %s", e)

    pinecone_texts = {d["text"] for d in pinecone_docs}
    merged = pinecone_docs + [d for d in raw_docs if d.get("text") not in pinecone_texts]
    all_docs = rank_docs(merged)

    return {
        **state,
        "retrieved_docs": all_docs[:25],
        "partial_context": len(failed_sources) > 0,
        "failed_sources": failed_sources,
        "source_errors": source_errors,
    }
