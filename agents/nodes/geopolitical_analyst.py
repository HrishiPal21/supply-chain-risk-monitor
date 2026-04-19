from agents.state import AgentState
from config import get_openai_client, OPENAI_MODEL

SYSTEM_PROMPT = """You are a Geopolitical Analyst specializing in how political
events, conflicts, trade policy, and diplomatic relations affect global supply chains.

Analyze:
- Active conflicts or instability near key supply nodes
- Trade war escalations, tariffs, sanctions, export controls
- Bilateral relations between supplier and buyer countries
- Critical mineral / resource nationalism trends
- Historical precedents of disruption in this region/sector

Format your response as:
## Geopolitical Risk Analysis
### Active Threats (bullet list with region and risk type)
### Trade Policy Landscape
### Historical Precedents
### Geopolitical Risk Rating: [Low / Medium / High / Critical]
"""


def geopolitical_analyst(state: AgentState) -> AgentState:
    client = get_openai_client()
    context = _format_docs(state["retrieved_docs"])

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Query: {state['query']}\n"
                    f"Company: {state.get('company') or 'N/A'}\n"
                    f"Region: {state.get('region') or 'N/A'}\n\n"
                    f"Source Documents:\n{context}\n\n"
                    "Provide a geopolitical risk analysis of this supply chain."
                ),
            },
        ],
        temperature=0.3,
    )
    return {**state, "geopolitical_analysis": response.choices[0].message.content}


def _format_docs(docs: list[dict]) -> str:
    return "\n\n---\n\n".join(
        f"[{d.get('source', 'unknown')}] {d.get('text', '')}" for d in docs[:15]
    )
