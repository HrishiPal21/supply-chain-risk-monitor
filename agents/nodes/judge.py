import json
import logging
from agents.state import AgentState
from config import get_openai_client, OPENAI_MODEL
from tools.retry import chat_with_retry

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Chief Risk Officer adjudicating a structured debate
between three analysts (Bear, Bull, Geopolitical) about a supply chain risk query.

Your job:
1. Weigh each analyst's argument on its merits and evidence quality.
2. Identify where analysts agree (consensus risk) vs. where they diverge.
3. Produce a final risk verdict with a numeric score.
4. The score you produce is the RAW macro risk score (0-100).
   An exposure multiplier will be applied automatically after your scoring
   to produce the final company-adjusted score.

Risk Score 0-100 (macro level — not adjusted for company exposure):
  0-20  = Very Low Risk
  21-40 = Low Risk
  41-60 = Moderate Risk
  61-80 = High Risk
  81-100 = Critical Risk

Output ONLY valid JSON in this exact schema:
{
  "verdict": "<2-3 sentence executive summary>",
  "risk_score": <integer 0-100>,
  "risk_label": "<Very Low | Low | Moderate | High | Critical>",
  "consensus_points": ["<point>", ...],
  "key_disagreements": ["<point>", ...],
  "top_3_risks": ["<risk>", ...],
  "top_3_mitigants": ["<mitigant>", ...],
  "recommended_action": "<Watch | Monitor | Escalate | Immediate Action>"
}
"""

_LABEL_FOR_SCORE = [
    (20,  "Very Low"),
    (40,  "Low"),
    (60,  "Moderate"),
    (80,  "High"),
    (100, "Critical"),
]

_ACTION_FOR_SCORE = [
    (20,  "Watch"),
    (40,  "Monitor"),
    (60,  "Monitor"),
    (80,  "Escalate"),
    (100, "Immediate Action"),
]


def _label(score: float, mapping: list) -> str:
    for threshold, label in mapping:
        if score <= threshold:
            return label
    return mapping[-1][1]


def judge(state: AgentState) -> AgentState:
    client = get_openai_client()
    exposure_level = state.get("exposure_level") or "Unknown"
    exposure_summary = state.get("exposure_summary") or "Not assessed"
    multiplier = state.get("exposure_multiplier")
    if multiplier is None:
        multiplier = 1.0

    response = chat_with_retry(client,
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Query: {state['query']}\n"
                    f"Company: {state.get('company') or 'N/A'}\n"
                    f"Exposure Level: {exposure_level}\n"
                    f"Exposure Context: {exposure_summary}\n\n"
                    f"=== BEAR ANALYST ===\n{state.get('bear_analysis', 'N/A')}\n\n"
                    f"=== BULL ANALYST ===\n{state.get('bull_analysis', 'N/A')}\n\n"
                    f"=== GEOPOLITICAL ANALYST ===\n{state.get('geopolitical_analysis', 'N/A')}\n\n"
                    "Synthesize the above and return your verdict as JSON."
                ),
            },
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        verdict_dict = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Judge: malformed JSON from model — %s | raw=%r", exc, raw[:200])
        verdict_dict = {
            "verdict": "Judge could not produce a structured verdict (JSON parse error).",
            "risk_score": 50,
            "risk_label": "Moderate",
            "consensus_points": [],
            "key_disagreements": [],
            "top_3_risks": [],
            "top_3_mitigants": [],
            "recommended_action": "Monitor",
        }

    raw_score = float(verdict_dict.get("risk_score", 50))
    adjusted_score = round(raw_score * multiplier, 1)

    # Store both scores explicitly — never overwrite the LLM's raw output
    verdict_dict["risk_score_raw"] = raw_score
    verdict_dict["risk_score_adjusted"] = adjusted_score
    # Keep risk_score as the adjusted value for backward-compat with anything reading final_output
    verdict_dict["risk_score"] = adjusted_score
    verdict_dict["risk_label"] = _label(adjusted_score, _LABEL_FOR_SCORE)
    verdict_dict["recommended_action"] = _label(adjusted_score, _ACTION_FOR_SCORE)

    logger.info(
        "Judge: raw=%.1f × multiplier=%.2f → adjusted=%.1f  label=%s  action=%s",
        raw_score, multiplier, adjusted_score,
        verdict_dict["risk_label"],
        verdict_dict["recommended_action"],
    )

    return {
        **state,
        "judge_verdict": verdict_dict.get("verdict", ""),
        "raw_risk_score": raw_score,
        "risk_score": adjusted_score,
        "final_output": verdict_dict,
    }
