import json
import streamlit as st
from tools.postgres_db import get_recent_runs, get_run_by_id

st.set_page_config(page_title="Results · Supply Chain Risk", layout="wide")
st.title("📊 Analysis Results")

# ── Run selector ──────────────────────────────────────────────────────────────
result = st.session_state.get("last_result")

@st.cache_data(ttl=30)
def _cached_recent_runs() -> list[dict]:
    return get_recent_runs(limit=15)


with st.sidebar:
    st.subheader("Load a past run")
    recent = _cached_recent_runs()
    if recent:
        options = {f"#{r['id']} — {r['query'][:50]}": r["id"] for r in recent}
        chosen = st.selectbox("Select run", list(options.keys()))
        if st.button("Load"):
            result = get_run_by_id(options[chosen])
            if result and isinstance(result.get("final_output"), str):
                result["final_output"] = json.loads(result["final_output"])
            if result and isinstance(result.get("guardrail_report"), str):
                result["guardrail_report"] = json.loads(result["guardrail_report"])
            st.session_state["last_result"] = result

if not result:
    st.info("Run a query on the **Search** page, or load a past run from the sidebar.")
    st.stop()

# ── Risk score banner ─────────────────────────────────────────────────────────
final = result.get("final_output") or {}
raw_score = result.get("risk_score") or final.get("risk_score", 0)
score = float(raw_score) if raw_score is not None else 0.0
label = final.get("risk_label", "Unknown")

score_color = (
    "🟢" if score < 21 else
    "🟡" if score < 41 else
    "🟠" if score < 61 else
    "🔴" if score < 81 else
    "🚨"
)

st.markdown(f"## {score_color} Risk Score: **{score:.0f} / 100** — {label}")
st.progress(score / 100)

st.markdown(f"**Query:** {result.get('query', '')}")
if result.get("company"):
    st.markdown(f"**Company:** {result['company']}")
if result.get("region"):
    st.markdown(f"**Region:** {result['region']}")

st.divider()

# ── Judge verdict ─────────────────────────────────────────────────────────────
st.subheader("Judge Verdict")
st.write(result.get("judge_verdict", "—"))

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Top 3 Risks**")
    for r in final.get("top_3_risks", []):
        st.markdown(f"- {r}")
with col2:
    st.markdown("**Top 3 Mitigants**")
    for m in final.get("top_3_mitigants", []):
        st.markdown(f"- {m}")

st.markdown(f"**Recommended Action:** `{final.get('recommended_action', '—')}`")

st.divider()

# ── Analyst debate ────────────────────────────────────────────────────────────
tab_bear, tab_bull, tab_geo = st.tabs(["🐻 Bear Analyst", "🐂 Bull Analyst", "🌍 Geopolitical"])

with tab_bear:
    st.markdown(result.get("bear_analysis") or "_No output_")

with tab_bull:
    st.markdown(result.get("bull_analysis") or "_No output_")

with tab_geo:
    st.markdown(result.get("geopolitical_analysis") or "_No output_")
