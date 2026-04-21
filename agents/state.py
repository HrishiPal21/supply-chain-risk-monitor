from typing import TypedDict, Optional


class AgentState(TypedDict):
    query: str                        # e.g. "semiconductor supply from Taiwan"
    company: Optional[str]            # e.g. "Apple" or None
    region: Optional[str]             # e.g. "Taiwan" or None
    retrieved_docs: list[dict]        # raw docs from Pinecone + EDGAR + news
    bear_analysis: Optional[str]
    bull_analysis: Optional[str]
    geopolitical_analysis: Optional[str]
    judge_verdict: Optional[str]
    risk_score: Optional[float]       # 0-100, higher = more risk
    guardrail_report: Optional[dict]  # trust scores + flagged claims
    final_output: Optional[dict]
    partial_context: bool             # True if any data source failed
    failed_sources: list[str]         # names of sources that errored
