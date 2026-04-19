import json
from agents.state import AgentState
from config import get_openai_client, OPENAI_MODEL

SYSTEM_PROMPT = """You are a Chief Risk Officer adjudicating a structured debate
between three analysts (Bear, Bull, Geopolitical) about a supply chain risk query.

Your job:
1. Weigh each analyst's argument on its merits and evidence quality.
2. Identify where analysts agree (consensus risk) vs. where they diverge.
3. Produce a final risk verdict with a numeric score.

Risk Score 0-100:
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


def judge(state: AgentState) -> AgentState:
    client = get_openai_client()

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Query: {state['query']}\n\n"
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
    verdict_dict = json.loads(raw)

    return {
        **state,
        "judge_verdict": verdict_dict.get("verdict", ""),
        "risk_score": float(verdict_dict.get("risk_score", 50)),
        "final_output": verdict_dict,
    }
