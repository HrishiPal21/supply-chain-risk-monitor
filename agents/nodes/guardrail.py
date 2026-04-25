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

SYSTEM_PROMPT = """You are a Guardrail Meta-Agent responsible for quality control
of a multi-agent supply chain risk analysis system.

Your job:
1. Check each analyst's output for hallucinations (claims not grounded in the source docs).
2. Assign a trust score (0.0–1.0) to each analyst based on evidence quality.
3. Identify any flagged claims that appear fabricated or unsupported.
4. Compute an overall confidence band for the final verdict.

Output ONLY valid JSON in this exact schema:
{
  "trust_scores": {
    "bear": <float 0.0-1.0>,
    "bull": <float 0.0-1.0>,
    "geopolitical": <float 0.0-1.0>,
    "judge": <float 0.0-1.0>
  },
  "flagged_claims": [
    {"agent": "<agent_name>", "claim": "<quoted claim>", "issue": "<why flagged>"}
  ],
  "confidence_band": {
    "low": <integer 0-100>,
    "high": <integer 0-100>
  },
  "overall_confidence": "<Low | Medium | High>",
  "guardrail_notes": "<1-2 sentences on overall reliability>"
}
"""


def _doc_digest(docs: list[dict], max_docs: int = 6) -> str:
    lines = []
    for d in docs[:max_docs]:
        src = d.get("source", "unknown")
        snippet = (d.get("text") or "")[:120].replace("\n", " ")
        lines.append(f"[{src}] {snippet}")
    return "\n".join(lines) if lines else "(no source documents available)"


def guardrail(state: AgentState) -> AgentState:
    client = get_openai_client()
    digest = _doc_digest(state.get("retrieved_docs", []))

    response = chat_with_retry(client,
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"=== SOURCE DOCUMENT DIGEST (for grounding checks) ===\n{digest}\n\n"
                    f"=== BEAR ANALYST ===\n{state.get('bear_analysis', 'N/A')}\n\n"
                    f"=== BULL ANALYST ===\n{state.get('bull_analysis', 'N/A')}\n\n"
                    f"=== GEOPOLITICAL ANALYST ===\n{state.get('geopolitical_analysis', 'N/A')}\n\n"
                    f"=== JUDGE VERDICT ===\n{state.get('judge_verdict', 'N/A')}\n\n"
                    "Run guardrail checks and return JSON."
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
        logger.error("Guardrail: malformed JSON from model — %s | raw=%r", exc, raw[:200])
        report = _FALLBACK_REPORT

    logger.info(
        "Guardrail: confidence=%s trust=%s flagged=%d",
        report.get("overall_confidence", "?"),
        report.get("trust_scores", {}),
        len(report.get("flagged_claims", [])),
    )

    return {**state, "guardrail_report": report}
