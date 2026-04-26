from __future__ import annotations

import logging
from typing import Optional

from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.nodes.data_retriever import data_retriever
from agents.nodes.exposure_assessment import exposure_assessment
from agents.nodes.bear_analyst import bear_analyst
from agents.nodes.bull_analyst import bull_analyst
from agents.nodes.geopolitical_analyst import geopolitical_analyst
from agents.nodes.judge import judge
from agents.nodes.guardrail import guardrail

logger = logging.getLogger(__name__)


def _safe_analyst(output_key: str, fn):
    """Wrap an analyst so a failure returns a degraded state instead of crashing the graph."""
    def wrapper(state: AgentState) -> AgentState:
        try:
            return fn(state)
        except Exception as exc:
            logger.error("Analyst %s failed: %s", output_key, exc, exc_info=True)
            return {output_key: f"_Analysis unavailable ({exc})_"}
    return wrapper


def _logged(name: str, fn):
    def wrapper(state: AgentState) -> AgentState:
        result = fn(state)
        _log_step(name, result)
        return result
    return wrapper


def build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    g.add_node("data_retriever",        _logged("data_retriever",        data_retriever))
    g.add_node("exposure_assessment",   _logged("exposure_assessment",   exposure_assessment))
    g.add_node("bear_analyst",          _logged("bear_analyst",          _safe_analyst("bear_analysis",          bear_analyst)))
    g.add_node("bull_analyst",          _logged("bull_analyst",          _safe_analyst("bull_analysis",          bull_analyst)))
    g.add_node("geopolitical_analyst",  _logged("geopolitical_analyst",  _safe_analyst("geopolitical_analysis",  geopolitical_analyst)))
    g.add_node("judge",                 _logged("judge",                 judge))
    g.add_node("guardrail",             _logged("guardrail",             guardrail))

    g.set_entry_point("data_retriever")
    g.add_edge("data_retriever",       "exposure_assessment")

    # Fan-out: exposure_assessment → three analysts in parallel
    g.add_edge("exposure_assessment",  "bear_analyst")
    g.add_edge("exposure_assessment",  "bull_analyst")
    g.add_edge("exposure_assessment",  "geopolitical_analyst")

    # Fan-in: all three analysts → judge (judge waits for all three)
    g.add_edge("bear_analyst",         "judge")
    g.add_edge("bull_analyst",         "judge")
    g.add_edge("geopolitical_analyst", "judge")

    g.add_edge("judge",    "guardrail")
    g.add_edge("guardrail", END)

    return g.compile()


pipeline = build_graph()


def _log_step(name: str, state: AgentState) -> None:
    doc_count = len(state.get("retrieved_docs", []))
    failed = state.get("failed_sources", [])
    errors = state.get("source_errors") or {}
    exposure = state.get("exposure_level")
    raw_score = state.get("raw_risk_score")
    adj_score = state.get("risk_score")
    logger.info(
        "Step %-22s | docs=%d failed=%s exposure=%s raw=%-5s adj=%s%s",
        name, doc_count, failed or "[]", exposure or "-", raw_score, adj_score,
        f" errors={list(errors.keys())}" if errors else "",
    )


def run_pipeline(query: str, company: str = "", region: str = "") -> AgentState:
    initial_state: AgentState = {
        "query": query,
        "company": company or None,
        "region": region or None,
        "retrieved_docs": [],
        "exposure_level": None,
        "exposure_multiplier": None,
        "exposure_summary": None,
        "exposure_profile": None,
        "bear_analysis": None,
        "bull_analysis": None,
        "geopolitical_analysis": None,
        "judge_verdict": None,
        "risk_score": None,
        "raw_risk_score": None,
        "guardrail_report": None,
        "final_output": None,
        "partial_context": False,
        "failed_sources": [],
        "source_errors": {},
    }
    logger.info("Pipeline start: query=%r company=%r region=%r", query, company or None, region or None)
    return pipeline.invoke(initial_state)
