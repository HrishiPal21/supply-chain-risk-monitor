from agents.state import AgentState
from config import get_openai_client, OPENAI_MODEL as ANALYST_MODEL
from tools.retry import chat_with_retry
from tools.doc_sanitizer import format_docs_safe, DOCUMENT_TRUST_POLICY

SYSTEM_PROMPT = """You are a Geopolitical Analyst specializing in how political
events, conflicts, trade policy, and diplomatic relations affect global supply chains.

Analyze:
- Active conflicts or instability near key supply nodes
- Trade war escalations, tariffs, sanctions, export controls
- Bilateral relations between supplier and buyer countries
- Critical mineral / resource nationalism trends
- Historical precedents of disruption in this region/sector

CITATION REQUIREMENT: Every specific claim must cite its source document inline
using the format [DOC N] — e.g. "Export controls were tightened in Q1 [DOC 3]."
If a claim has no supporting document, label it (inferred).

Format your response as:
## Geopolitical Risk Analysis
### Active Threats (bullet list with region, risk type, and [DOC N] citations)
### Trade Policy Landscape
### Historical Precedents
### Geopolitical Risk Rating: [Low / Medium / High / Critical]
""" + DOCUMENT_TRUST_POLICY


def geopolitical_analyst(state: AgentState) -> AgentState:
    client = get_openai_client()
    context = format_docs_safe(state["retrieved_docs"], max_docs=5)

    response = chat_with_retry(client,
        model=ANALYST_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Query: {state['query']}\n"
                    f"Company: {state.get('company') or 'N/A'}\n"
                    f"Region: {state.get('region') or 'N/A'}\n"
                    f"Exposure Level: {state.get('exposure_level') or 'Unknown'}\n"
                    f"Exposure Context: {state.get('exposure_summary') or 'Not assessed'}\n\n"
                    f"Source Documents:\n{context}\n\n"
                    "Provide a geopolitical risk analysis of this supply chain. "
                    "Consider how the company's exposure level affects their specific vulnerability."
                ),
            },
        ],
        temperature=0.3,
    )
    return {"geopolitical_analysis": response.choices[0].message.content}


