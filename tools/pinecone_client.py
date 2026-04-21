from __future__ import annotations

from pinecone import Pinecone, ServerlessSpec
from config import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_ENVIRONMENT,
    EMBED_MODEL,
    EMBED_DIM,
    get_openai_client,
)
from tools.retry import embed_with_retry

_index_cache = None


def _get_index():
    global _index_cache
    if _index_cache is not None:
        return _index_cache
    pc = Pinecone(api_key=PINECONE_API_KEY)
    existing = [idx.name for idx in pc.list_indexes()]
    if PINECONE_INDEX_NAME not in existing:
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT),
        )
    _index_cache = pc.Index(PINECONE_INDEX_NAME)
    return _index_cache


def embed(text: str) -> list[float]:
    client = get_openai_client()
    return embed_with_retry(client, model=EMBED_MODEL, input=text)


def upsert_docs(docs: list[dict]) -> None:
    """Embed and upsert a list of {id, text, source} dicts into Pinecone."""
    index = _get_index()
    vectors = []
    for doc in docs:
        vec = embed(doc["text"])
        vectors.append({
            "id": doc["id"],
            "values": vec,
            "metadata": {"text": doc["text"][:500], "source": doc.get("source", "")},
        })
    if vectors:
        index.upsert(vectors=vectors)


def search_pinecone(query: str, top_k: int = 10) -> list[dict]:
    """Return top-k matching docs from Pinecone. Raises on failure so caller can track it."""
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
