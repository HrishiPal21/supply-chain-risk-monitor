from typing import TypedDict, Optional


class AgentState(TypedDict):
    query: str                        # e.g. "semiconductor supply from Taiwan"
    company: Optional[str]            # e.g. "Apple" or None
    region: Optional[str]             # e.g. "Taiwan" or None
    retrieved_docs: list[dict]        # raw docs from Pinecone + EDGAR + news
    # Exposure assessment (runs before analysts)
    exposure_level: Optional[str]     # Critical / High / Moderate / Low / Minimal / Unknown
    exposure_multiplier: Optional[float]  # 0.0–1.0 scalar applied to raw risk score
    exposure_summary: Optional[str]   # markdown explanation of company-specific exposure
    exposure_profile: Optional[dict]  # full structured JSON from the exposure agent
    # Analyst outputs
    bear_analysis: Optional[str]
    bull_analysis: Optional[str]
    geopolitical_analysis: Optional[str]
    judge_verdict: Optional[str]
    risk_score: Optional[float]       # 0-100, higher = more risk (post-exposure adjustment)
    raw_risk_score: Optional[float]   # 0-100 before exposure multiplier
    guardrail_report: Optional[dict]  # trust scores + flagged claims
    final_output: Optional[dict]
    partial_context: bool             # True if any data source failed
    failed_sources: list[str]         # names of sources that errored
    source_errors: Optional[dict]     # {source_name: error_message} for debuggability
