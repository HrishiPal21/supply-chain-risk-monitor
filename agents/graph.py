from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

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


def run_analysts(state: AgentState) -> AgentState:
    """Run all three analysts in parallel via threads, then merge into state."""
    analyst_fns = {
        "bear": bear_analyst,
        "bull": bull_analyst,
        "geo": geopolitical_analyst,
    }

    results: dict[str, AgentState] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fn, state): key for key, fn in analyst_fns.items()}
        for future in as_completed(futures):
            key = futures[future]
            results[key] = future.result()

    return {
        **state,
        "bear_analysis": results["bear"].get("bear_analysis"),
        "bull_analysis": results["bull"].get("bull_analysis"),
        "geopolitical_analysis": results["geo"].get("geopolitical_analysis"),
    }


def _logged(name: str, fn):
    def wrapper(state: AgentState) -> AgentState:
        result = fn(state)
        _log_step(name, result)
        return result
    return wrapper


def build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    g.add_node("data_retriever",     _logged("data_retriever",     data_retriever))
    g.add_node("exposure_assessment", _logged("exposure_assessment", exposure_assessment))
    g.add_node("analysts",            _logged("analysts",            run_analysts))
    g.add_node("judge",               _logged("judge",               judge))
    g.add_node("guardrail",           _logged("guardrail",           guardrail))

    g.set_entry_point("data_retriever")
    g.add_edge("data_retriever", "exposure_assessment")
    g.add_edge("exposure_assessment", "analysts")
    g.add_edge("analysts", "judge")
    g.add_edge("judge", "guardrail")
    g.add_edge("guardrail", END)

    return g.compile()


pipeline = build_graph()


def _log_step(name: str, state: AgentState) -> None:
    doc_count = len(state.get("retrieved_docs", []))
    failed = state.get("failed_sources", [])
    exposure = state.get("exposure_level")
    raw_score = state.get("raw_risk_score")
    adj_score = state.get("risk_score")
    logger.info(
        "Step %-22s | docs=%d failed=%s exposure=%s raw_score=%s adj_score=%s",
        name, doc_count, failed or "[]", exposure or "-", raw_score, adj_score,
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
    }
    logger.info("Pipeline start: query=%r company=%r region=%r", query, company or None, region or None)
    return pipeline.invoke(initial_state)
