from agents.state import AgentState
from config import get_openai_client, ANALYST_MODEL
from tools.retry import chat_with_retry
from tools.doc_sanitizer import format_docs_safe, DOCUMENT_TRUST_POLICY

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

CITATION REQUIREMENT: Every specific claim must cite its source document inline
using the format [DOC N] — e.g. "TSMC supplies 90% of advanced chips [DOC 2]."
If a claim has no supporting document, label it (inferred).

Format your response as:
## Bear Case Risk Analysis
### Key Risks (bullet list with severity and [DOC N] citations)
### Evidence (quoted snippets with [DOC N] references)
### Worst-Case Scenario
""" + DOCUMENT_TRUST_POLICY


def bear_analyst(state: AgentState) -> AgentState:
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
                    "Provide a structured bear-case risk analysis. "
                    "Tailor your severity to the company's actual exposure level above."
                ),
            },
        ],
        temperature=0.3,
    )
    return {"bear_analysis": response.choices[0].message.content}


