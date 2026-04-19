import json
from agents.state import AgentState
from config import get_openai_client, OPENAI_MODEL

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


def guardrail(state: AgentState) -> AgentState:
    client = get_openai_client()
    source_texts = "\n\n".join(
        f"[{d.get('source', 'unknown')}] {d.get('text', '')}"
        for d in state["retrieved_docs"][:10]
    )

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"=== SOURCE DOCUMENTS ===\n{source_texts}\n\n"
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
    report = json.loads(raw)

    return {**state, "guardrail_report": report}
