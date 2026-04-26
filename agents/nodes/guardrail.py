from __future__ import annotations

import json
import logging
from agents.state import AgentState
from config import get_openai_client, OPENAI_MODEL
from tools.retry import chat_with_retry

logger = logging.getLogger(__name__)

_FALLBACK_REPORT = {
    "trust_scores": {"bear": 0.5, "bull": 0.5, "geopolitical": 0.5, "judge": 0.5},
    "flagged_claims": [],
    "confidence_band": {"low": 30, "high": 70},
    "overall_confidence": "Low",
    "guardrail_notes": "Guardrail could not complete quality checks (JSON parse error).",
}

# Token budget: 15 docs × 400 chars ≈ 6,000 chars ≈ ~1,500 tokens — well within GPT-4o's window
_MAX_GROUNDING_DOCS  = 15
_CHARS_PER_DOC       = 400
_TOTAL_CHAR_BUDGET   = _MAX_GROUNDING_DOCS * _CHARS_PER_DOC

SYSTEM_PROMPT = """You are a Guardrail Meta-Agent responsible for quality control
of a multi-agent supply chain risk analysis system.

You are given:
1. GROUNDING SOURCES — the actual retrieved documents the analysts had access to.
   Each source is labelled with its origin (NewsAPI, RSS, EDGAR, HTML, etc.).
2. The outputs of four agents: Bear Analyst, Bull Analyst, Geopolitical Analyst, Judge.

Your job:
1. For each analyst, identify specific claims and check whether they are supported
   by text in the Grounding Sources. Quote the relevant source snippet when grounding
   a claim, or mark the claim as UNSUPPORTED if no evidence exists.
2. Assign a trust score (0.0–1.0) to each analyst:
   - 0.9–1.0: all major claims traceable to source documents
   - 0.7–0.8: most claims grounded, minor unsupported details
   - 0.5–0.6: mixed — some grounded, some fabricated
   - below 0.5: significant hallucination or unsupported claims
3. Flag specific claims that appear fabricated, contradicted, or unverifiable.
4. Compute a confidence band for the final risk score based on source quality
   and analyst agreement.

Output ONLY valid JSON in this exact schema:
{
  "trust_scores": {
    "bear": <float 0.0-1.0>,
    "bull": <float 0.0-1.0>,
    "geopolitical": <float 0.0-1.0>,
    "judge": <float 0.0-1.0>
  },
  "flagged_claims": [
    {
      "agent": "<agent_name>",
      "claim": "<quoted claim from analyst output>",
      "issue": "<UNSUPPORTED | CONTRADICTED | OVERSTATED>",
      "detail": "<why flagged, or which source contradicts it>"
    }
  ],
  "confidence_band": {
    "low": <integer 0-100>,
    "high": <integer 0-100>
  },
  "overall_confidence": "<Low | Medium | High>",
  "guardrail_notes": "<2-3 sentences on overall reliability and grounding quality>"
}
"""


def _grounding_context(docs: list[dict]) -> str:
    """Build a token-budgeted grounding context from retrieved docs.

    Uses up to _MAX_GROUNDING_DOCS docs, each truncated to _CHARS_PER_DOC chars,
    prioritising EDGAR filings (most authoritative) then others by order.
    """
    if not docs:
        return "(no source documents available)"

    # Prioritise EDGAR first, then the rest in original retrieval order
    edgar = [d for d in docs if "EDGAR" in d.get("source", "")]
    others = [d for d in docs if "EDGAR" not in d.get("source", "")]
    ordered = edgar + others

    lines = []
    total_chars = 0
    for i, doc in enumerate(ordered):
        if i >= _MAX_GROUNDING_DOCS:
            break
        src = doc.get("source", "unknown")
        text = (doc.get("text") or "").replace("\n", " ").strip()
        snippet = text[:_CHARS_PER_DOC]
        if not snippet:
            continue
        entry = f"[DOC {i+1} | {src}]\n{snippet}"
        total_chars += len(entry)
        if total_chars > _TOTAL_CHAR_BUDGET:
            break
        lines.append(entry)

    return "\n\n".join(lines) if lines else "(no source documents available)"


def guardrail(state: AgentState) -> AgentState:
    client = get_openai_client()
    grounding = _grounding_context(state.get("retrieved_docs", []))

    response = chat_with_retry(client,
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"=== GROUNDING SOURCES ({len(state.get('retrieved_docs', []))} docs retrieved, "
                    f"top {_MAX_GROUNDING_DOCS} shown) ===\n{grounding}\n\n"
                    f"=== BEAR ANALYST ===\n{state.get('bear_analysis', 'N/A')}\n\n"
                    f"=== BULL ANALYST ===\n{state.get('bull_analysis', 'N/A')}\n\n"
                    f"=== GEOPOLITICAL ANALYST ===\n{state.get('geopolitical_analysis', 'N/A')}\n\n"
                    f"=== JUDGE VERDICT ===\n{state.get('judge_verdict', 'N/A')}\n\n"
                    "Trace each analyst's key claims back to the Grounding Sources above. "
                    "Flag any claim you cannot find support for. Return JSON."
                ),
            },
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        report = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Guardrail: malformed JSON — %s | raw=%r", exc, raw[:200])
        report = _FALLBACK_REPORT

    logger.info(
        "Guardrail: confidence=%s trust=%s flagged=%d grounding_docs=%d",
        report.get("overall_confidence", "?"),
        report.get("trust_scores", {}),
        len(report.get("flagged_claims", [])),
        len(state.get("retrieved_docs", [])),
    )

    return {**state, "guardrail_report": report}
