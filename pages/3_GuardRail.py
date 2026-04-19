import json
import streamlit as st

st.set_page_config(page_title="GuardRail · Supply Chain Risk", layout="wide")
st.title("🛡️ GuardRail Monitor")
st.caption("Trust scores, hallucination flags, and confidence bands from the meta-agent.")

result = st.session_state.get("last_result")

if not result:
    st.info("Run a query on the **Search** page first.")
    st.stop()

report = result.get("guardrail_report")
if isinstance(report, str):
    report = json.loads(report)

if not report:
    st.warning("No guardrail report available for this run.")
    st.stop()

# ── Trust scores ──────────────────────────────────────────────────────────────
st.subheader("Agent Trust Scores")
trust = report.get("trust_scores", {})
cols = st.columns(4)
agents = ["bear", "bull", "geopolitical", "judge"]
for col, agent in zip(cols, agents):
    score = trust.get(agent, 0.0)
    color = "🟢" if score >= 0.7 else "🟡" if score >= 0.5 else "🔴"
    col.metric(label=f"{color} {agent.capitalize()}", value=f"{score:.2f}")

st.divider()

# ── Confidence band ───────────────────────────────────────────────────────────
band = report.get("confidence_band", {})
overall = report.get("overall_confidence", "—")
st.subheader("Confidence Band")
col1, col2, col3 = st.columns(3)
col1.metric("Low Bound", f"{band.get('low', '—')}")
col2.metric("High Bound", f"{band.get('high', '—')}")
col3.metric("Overall Confidence", overall)

st.divider()

# ── Flagged claims ────────────────────────────────────────────────────────────
flagged = report.get("flagged_claims", [])
st.subheader(f"Flagged Claims ({len(flagged)})")
if flagged:
    for flag in flagged:
        with st.expander(f"⚠️ [{flag.get('agent', '?').upper()}] {flag.get('claim', '')[:80]}…"):
            st.markdown(f"**Agent:** {flag.get('agent', '—')}")
            st.markdown(f"**Claim:** {flag.get('claim', '—')}")
            st.markdown(f"**Issue:** {flag.get('issue', '—')}")
else:
    st.success("No flagged claims — all analyst outputs appear grounded in source documents.")

st.divider()
st.info(report.get("guardrail_notes", ""))
