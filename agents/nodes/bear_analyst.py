from agents.state import AgentState
from config import get_openai_client, OPENAI_MODEL
from tools.retry import chat_with_retry

SYSTEM_PROMPT = """You are a Bear Analyst specializing in supply chain risk.
Identify and articulate WORST-CASE risks, vulnerabilities, and threats in the
provided supply chain data. Be specific, cite evidence from the documents, and
assign severity labels (Critical / High / Medium).

Focus on:
- Geographic concentration risk and single-source dependencies
- Geopolitical exposure (tariffs, sanctions, conflict zones)
- Financial distress signals in supplier filings
- Regulatory / compliance threats
- Recent disruption events cited in news

Format your response as:
## Bear Case Risk Analysis
### Key Risks (bullet list with severity)
### Evidence (cited from source docs)
### Worst-Case Scenario
"""


def bear_analyst(state: AgentState) -> AgentState:
    client = get_openai_client()
    context = _format_docs(state["retrieved_docs"])

    response = chat_with_retry(client,
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
                    "Provide a structured bear-case risk analysis."
                ),
            },
        ],
        temperature=0.3,
    )
    return {**state, "bear_analysis": response.choices[0].message.content}


def _format_docs(docs: list[dict]) -> str:
    return "\n\n---\n\n".join(
        f"[{d.get('source', 'unknown')}] {d.get('text', '')}" for d in docs[:15]
    )
