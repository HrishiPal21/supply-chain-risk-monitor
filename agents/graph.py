from concurrent.futures import ThreadPoolExecutor, as_completed

from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.nodes.data_retriever import data_retriever
from agents.nodes.bear_analyst import bear_analyst
from agents.nodes.bull_analyst import bull_analyst
from agents.nodes.geopolitical_analyst import geopolitical_analyst
from agents.nodes.judge import judge
from agents.nodes.guardrail import guardrail


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


def build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    g.add_node("data_retriever", data_retriever)
    g.add_node("analysts", run_analysts)          # parallel fan-out inside one node
    g.add_node("judge", judge)
    g.add_node("guardrail", guardrail)

    g.set_entry_point("data_retriever")
    g.add_edge("data_retriever", "analysts")
    g.add_edge("analysts", "judge")
    g.add_edge("judge", "guardrail")
    g.add_edge("guardrail", END)

    return g.compile()


pipeline = build_graph()


def run_pipeline(query: str, company: str = "", region: str = "") -> AgentState:
    initial_state: AgentState = {
        "query": query,
        "company": company or None,
        "region": region or None,
        "retrieved_docs": [],
        "bear_analysis": None,
        "bull_analysis": None,
        "geopolitical_analysis": None,
        "judge_verdict": None,
        "risk_score": None,
        "guardrail_report": None,
        "final_output": None,
    }
    return pipeline.invoke(initial_state)
