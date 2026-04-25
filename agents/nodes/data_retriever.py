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


def data_retriever(state: AgentState) -> AgentState:
    query = state["query"]
    company = state.get("company") or ""
    failed_sources: list[str] = []

    try:
        news_docs = fetch_news(query)
    except Exception:
        news_docs = []
        failed_sources.append("NewsAPI")

    try:
        rss_docs = fetch_rss(query)
    except Exception:
        rss_docs = []
        failed_sources.append("RSS")

    try:
        html_docs = fetch_html_docs(query)
    except Exception:
        html_docs = []
        failed_sources.append("HTML Scraper")

    if company:
        try:
            edgar_docs = fetch_edgar_filings(company)
        except Exception:
            edgar_docs = []
            failed_sources.append("EDGAR")
    else:
        edgar_docs = []

    raw_docs = news_docs + rss_docs + html_docs + edgar_docs
    for doc in raw_docs:
        doc.setdefault("id", uuid.uuid4().hex)

    try:
        upload_raw_docs(raw_docs, query)
    except Exception:
        pass

    try:
        upsert_docs(raw_docs)
    except Exception as e:
        logger.warning("Pinecone upsert failed: %s", e)
        failed_sources.append("Pinecone/upsert")

    try:
        pinecone_docs = search_pinecone(query, top_k=15)
    except Exception as e:
        logger.warning("Pinecone search failed: %s", e)
        pinecone_docs = []
        failed_sources.append("Pinecone/search")

    pinecone_texts = {d["text"] for d in pinecone_docs}
    all_docs = pinecone_docs + [d for d in raw_docs if d.get("text") not in pinecone_texts]

    return {
        **state,
        "retrieved_docs": all_docs[:25],
        "partial_context": len(failed_sources) > 0,
        "failed_sources": failed_sources,
    }
