from __future__ import annotations

import logging
from typing import Optional
from pinecone import Pinecone, ServerlessSpec
from config import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_ENVIRONMENT,
    EMBED_MODEL,
    EMBED_DIM,
    get_openai_client,
)
from tools.retry import embed_with_retry, embed_batch_with_retry

logger = logging.getLogger(__name__)

_index_cache: Optional[object] = None
_UPSERT_BATCH = 100
_EMBED_BATCH  = 100


def ensure_index() -> None:
    """Create the Pinecone index if it doesn't exist. Call at app startup only."""
    global _index_cache
    if not PINECONE_API_KEY:
        return
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        existing = [idx.name for idx in pc.list_indexes()]
        if PINECONE_INDEX_NAME not in existing:
            logger.info("Creating Pinecone index %r", PINECONE_INDEX_NAME)
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=EMBED_DIM,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT),
            )
        _index_cache = pc.Index(PINECONE_INDEX_NAME)
        logger.info("Pinecone index %r ready", PINECONE_INDEX_NAME)
    except Exception as exc:
        logger.warning("ensure_index failed: %s", exc)


def _get_index():
    global _index_cache
    if _index_cache is not None:
        return _index_cache
    # ensure_index creates the index if missing and always populates _index_cache
    ensure_index()
    if _index_cache is None:
        raise RuntimeError("Pinecone index unavailable — check PINECONE_API_KEY and index name")
    return _index_cache


def embed(text: str) -> list[float]:
    client = get_openai_client()
    return embed_with_retry(client, model=EMBED_MODEL, input=text)


def upsert_docs(docs: list[dict]) -> None:
    """Dedupe, batch-embed, and upsert docs into Pinecone."""
    if not docs:
        return

    # Dedupe by text content — skip empty or already-seen texts
    seen: set[str] = set()
    unique: list[dict] = []
    for doc in docs:
        text = (doc.get("text") or "").strip()
        if text and text not in seen:
            seen.add(text)
            unique.append(doc)

    if not unique:
        return

    client = get_openai_client()
    index = _get_index()

    # Embed in batches — single API call per batch instead of one per doc
    all_embeddings: list[list[float]] = []
    texts = [doc["text"] for doc in unique]
    for i in range(0, len(texts), _EMBED_BATCH):
        batch = texts[i : i + _EMBED_BATCH]
        embeddings = embed_batch_with_retry(client, model=EMBED_MODEL, inputs=batch)
        all_embeddings.extend(embeddings)

    vectors = [
        {
            "id": doc["id"],
            "values": vec,
            "metadata": {"text": doc["text"][:500], "source": doc.get("source", "")},
        }
        for doc, vec in zip(unique, all_embeddings)
    ]

    # Upsert in batches of 100 (Pinecone recommended limit)
    for i in range(0, len(vectors), _UPSERT_BATCH):
        index.upsert(vectors=vectors[i : i + _UPSERT_BATCH])

    logger.info("Upserted %d vectors (%d dupes skipped)", len(unique), len(docs) - len(unique))


def search_pinecone(query: str, top_k: int = 10) -> list[dict]:
    """Return top-k matching docs from Pinecone."""
    if not PINECONE_API_KEY:
        return []
    index = _get_index()
    query_vec = embed(query)
    results = index.query(vector=query_vec, top_k=top_k, include_metadata=True)
    return [
        {
            "source": match.metadata.get("source", "Pinecone"),
            "text": match.metadata.get("text", ""),
            "score": match.score,
        }
        for match in results.matches
    ]
