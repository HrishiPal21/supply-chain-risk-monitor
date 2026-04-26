from agents.state import AgentState
from config import get_openai_client, ANALYST_MODEL
from tools.retry import chat_with_retry
from tools.doc_sanitizer import format_docs_safe, DOCUMENT_TRUST_POLICY

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

CITATION REQUIREMENT: Every specific claim must cite its source document inline
using the format [DOC N] — e.g. "The company holds 6 months of inventory [DOC 1]."
If a claim has no supporting document, label it (inferred).

Format your response as:
## Bull Case Resilience Analysis
### Key Strengths (bullet list with [DOC N] citations)
### Evidence (quoted snippets with [DOC N] references)
### Best-Case Scenario
""" + DOCUMENT_TRUST_POLICY


def bull_analyst(state: AgentState) -> AgentState:
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
                    "Provide a structured bull-case resilience analysis. "
                    "Factor in the company's actual exposure level and any mitigations on file."
                ),
            },
        ],
        temperature=0.3,
    )
    return {"bull_analysis": response.choices[0].message.content}


