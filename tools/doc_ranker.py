from __future__ import annotations

# Source type → authority weight, normalized to 0–1 (max = EDGAR = 1.0).
_SOURCE_WEIGHTS: dict[str, float] = {
    "EDGAR":   1.0,
    "NewsAPI": 0.667,
    "RSS":     0.333,
    "HTML":    0.0,
}

# Blend ratio: how much source authority vs. Pinecone similarity score matters.
# 50/50 means a highly-relevant NewsAPI doc (similarity≈0.9) can beat a
# mediocre EDGAR chunk (similarity≈0.2): 0.5*0.667+0.5*0.9=0.783 vs 0.5*1+0.5*0.2=0.6.
_AUTHORITY_WEIGHT = 0.5
_SIMILARITY_WEIGHT = 0.5
_DEFAULT_SIMILARITY = 0.5  # used when no Pinecone score is available


def _composite_score(doc: dict) -> float:
    src = doc.get("source", "")
    authority = next(
        (w for prefix, w in _SOURCE_WEIGHTS.items() if prefix in src),
        0.0,
    )
    similarity = float(doc.get("score") or _DEFAULT_SIMILARITY)
    return _AUTHORITY_WEIGHT * authority + _SIMILARITY_WEIGHT * similarity


def rank_docs(docs: list[dict]) -> list[dict]:
    """Sort docs by composite score (source authority + Pinecone similarity).

    Stable sort preserves retrieval order within equal-score ties.
    Docs without a Pinecone score get the default similarity of 0.5.
    """
    return sorted(docs, key=_composite_score, reverse=True)
