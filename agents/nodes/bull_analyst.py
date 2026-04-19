from agents.state import AgentState
from config import get_openai_client, OPENAI_MODEL

SYSTEM_PROMPT = """You are a Bull Analyst specializing in supply chain resilience.
Identify mitigating factors, strengths, and best-case scenarios in the provided
supply chain data. Be specific and cite evidence from the documents.

Focus on:
- Supplier diversification and multi-sourcing strategies
- Inventory buffers and strategic stockpiles
- Long-term contracts and pricing protections
- Nearshoring / friendshoring initiatives
- Company financial strength and capex commitments
- Positive regulatory tailwinds

Format your response as:
## Bull Case Resilience Analysis
### Key Strengths (bullet list)
### Evidence (cited from source docs)
### Best-Case Scenario
"""


def bull_analyst(state: AgentState) -> AgentState:
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
                    "Provide a structured bull-case resilience analysis."
                ),
            },
        ],
        temperature=0.3,
    )
    return {**state, "bull_analysis": response.choices[0].message.content}


def _format_docs(docs: list[dict]) -> str:
    return "\n\n---\n\n".join(
        f"[{d.get('source', 'unknown')}] {d.get('text', '')}" for d in docs[:15]
    )
