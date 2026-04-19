from agents.state import AgentState
from tools.edgar import fetch_edgar_filings
from tools.news import fetch_news
from tools.rss_feed import fetch_rss
from tools.pinecone_client import search_pinecone, upsert_docs
from tools.gcs_client import upload_raw_docs
import uuid


def data_retriever(state: AgentState) -> AgentState:
    query = state["query"]
    company = state.get("company") or ""

    news_docs = fetch_news(query)
    rss_docs = fetch_rss(query)
    edgar_docs = fetch_edgar_filings(company) if company else []

    raw_docs = news_docs + rss_docs + edgar_docs

    # Tag each doc with a unique id for upsert
    for doc in raw_docs:
        doc.setdefault("id", uuid.uuid4().hex)

    # Store raw docs in GCS for audit trail
    try:
        upload_raw_docs(raw_docs, query)
    except Exception:
        pass  # Non-fatal; don't block the pipeline

    # Embed and upsert new docs into Pinecone
    try:
        upsert_docs(raw_docs)
    except Exception:
        pass

    # Retrieve semantically relevant docs from Pinecone
    pinecone_docs = search_pinecone(query, top_k=15)

    # Merge: prefer Pinecone results (ranked by relevance), then append raw docs
    # whose text content wasn't already returned by Pinecone
    pinecone_texts = {d["text"] for d in pinecone_docs}
    all_docs = pinecone_docs + [d for d in raw_docs if d.get("text") not in pinecone_texts]

    return {**state, "retrieved_docs": all_docs[:25]}
