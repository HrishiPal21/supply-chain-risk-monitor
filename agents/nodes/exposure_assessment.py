"""
Exposure Assessment Agent.

Runs after data_retriever and before the analysts.
Answers: "How directly is THIS company/industry exposed to THIS specific risk?"

If a company ticker is provided, it mines the EDGAR docs in retrieved_docs to
understand actual sourcing dependencies. If no company is given, it produces an
industry-level exposure estimate based on the query topic.

Outputs:
  exposure_level      — Critical / High / Moderate / Low / Minimal / Unknown
  exposure_multiplier — 0.0–1.0 scalar (applied to raw risk score by the judge)
  exposure_summary    — markdown explanation shown in the UI
  exposure_profile    — full structured dict
"""

from __future__ import annotations

import json
import logging

from agents.state import AgentState
from config import get_openai_client, OPENAI_MODEL
from tools.retry import chat_with_retry
from tools.doc_sanitizer import sanitize_doc_text, DOCUMENT_TRUST_POLICY

logger = logging.getLogger(__name__)

_MULTIPLIERS = {
    "Critical": 1.0,
    "High":     0.8,
    "Moderate": 0.5,
    "Low":      0.25,
    "Minimal":  0.1,
    "Unknown":  1.0,   # no company → full macro risk applies
}

SYSTEM_PROMPT = """You are a Supply Chain Exposure Analyst.

Your ONLY job is to assess how directly and significantly a specific company
(or industry sector, if no company is given) is exposed to the supply chain
risk described in the query.

This is NOT a general risk analysis — the macro risk level is handled by other
agents. You must focus purely on EXPOSURE: does this entity actually source
from, depend on, or operate in the affected region/sector?

Output ONLY valid JSON in this exact schema:
{
  "exposure_level": "<Critical | High | Moderate | Low | Minimal | Unknown>",
  "exposure_type": "<direct | indirect | minimal | unknown>",
  "key_dependencies": ["<specific sourcing relationship or dependency>", ...],
  "mitigation_on_file": ["<any diversification, hedging, or contingency found in docs>", ...],
  "no_company_note": "<if no company was given, describe which industries would be most exposed>",
  "exposure_reasoning": "<2-3 sentences explaining WHY this exposure level was assigned>",
  "exposure_summary_md": "<markdown paragraph for display in UI — plain English, no jargon>"
}

Exposure level definitions:
  Critical — Company is a PRIMARY direct customer/operator in the affected supply node.
             Disruption would immediately impact their core product or operations.
             (e.g. Apple asking about TSMC Taiwan chips)
  High     — Company has significant direct sourcing from the affected region/sector
             with limited alternatives identified.
  Moderate — Company has some direct exposure but also meaningful diversification
             or indirect dependency only.
  Low      — Exposure is mostly indirect (e.g. a supplier's supplier). Limited
             revenue impact expected.
  Minimal  — Company operates in a different sector/region with negligible exposure.
             (e.g. a bakery chain asking about semiconductor shortages)
  Unknown  — No company specified; provide industry-level exposure assessment instead.

CRITICAL RULES:
- Base your assessment ONLY on evidence in the provided documents.
- If EDGAR filings are present, prioritize them — they are the most authoritative source.
- If documents don't mention the company's sourcing, say so explicitly in reasoning.
- Never invent dependencies not supported by the documents.
""" + DOCUMENT_TRUST_POLICY


def _format_docs(docs: list[dict], max_docs: int = 20) -> str:
    lines = []
    for d in docs[:max_docs]:
        src = d.get("source", "unknown")
        text = sanitize_doc_text(d.get("text", ""))
        if text.strip():
            lines.append(f"[{src}]\n{text}")
    return "\n\n---\n\n".join(lines)


def exposure_assessment(state: AgentState) -> AgentState:
    client = get_openai_client()
    company = state.get("company") or ""
    query = state["query"]
    docs = state.get("retrieved_docs", [])

    # Separate EDGAR docs for emphasis
    edgar_docs = [d for d in docs if "EDGAR" in d.get("source", "")]
    other_docs = [d for d in docs if "EDGAR" not in d.get("source", "")]

    context_parts = []
    if edgar_docs:
        context_parts.append(
            f"=== SEC EDGAR FILINGS FOR {company.upper()} ===\n"
            + _format_docs(edgar_docs, max_docs=5)
        )
    context_parts.append(
        "=== NEWS / WEB SOURCES ===\n" + _format_docs(other_docs, max_docs=6)
    )
    context = "\n\n".join(context_parts)

    user_msg = (
        f"Risk Query: {query}\n"
        f"Company / Ticker: {company or 'NOT PROVIDED — assess at industry level'}\n"
        f"Region focus: {state.get('region') or 'N/A'}\n\n"
        f"Source Documents:\n{context}\n\n"
        "Assess the exposure level for this company/industry to the described risk."
    )

    try:
        response = chat_with_retry(
            client,
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        profile = json.loads(response.choices[0].message.content)
    except Exception as exc:
        logger.warning("Exposure assessment failed: %s", exc)
        profile = {
            "exposure_level": "Unknown",
            "exposure_type": "unknown",
            "key_dependencies": [],
            "mitigation_on_file": [],
            "no_company_note": "",
            "exposure_reasoning": "Exposure assessment could not be completed.",
            "exposure_summary_md": "Exposure data unavailable — full macro risk score applies.",
        }

    level = profile.get("exposure_level", "Unknown")
    multiplier = _MULTIPLIERS.get(level, 1.0)

    logger.info(
        "Exposure assessment: level=%s multiplier=%.2f company=%s",
        level, multiplier, company or "N/A",
    )

    return {
        **state,
        "exposure_level": level,
        "exposure_multiplier": multiplier,
        "exposure_summary": profile.get("exposure_summary_md", ""),
        "exposure_profile": profile,
    }
