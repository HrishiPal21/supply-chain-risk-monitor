import streamlit as st
from agents.graph import run_pipeline
from tools.postgres_db import save_run, init_db

st.set_page_config(page_title="Search · Supply Chain Risk", layout="wide", page_icon="🔍")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0f1117; }
    [data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }
    .page-header { padding: 1.5rem 0 0.5rem 0; }
    .page-header h1 { color: #e6edf3; font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; }
    .page-header p { color: #8b949e; margin: 0; }

    /* Form card */
    .form-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 2rem;
        margin-top: 1.5rem;
    }

    /* Override Streamlit textarea */
    textarea { background: #0d1117 !important; color: #e6edf3 !important; border: 1px solid #30363d !important; border-radius: 8px !important; }
    input[type="text"] { background: #0d1117 !important; color: #e6edf3 !important; border: 1px solid #30363d !important; border-radius: 8px !important; }

    /* Status box */
    .status-box {
        background: #161b22;
        border: 1px solid #388bfd44;
        border-left: 4px solid #58a6ff;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-top: 1rem;
        color: #8b949e;
        font-size: 0.9rem;
    }

    /* Pipeline steps */
    .pipeline {
        display: flex;
        gap: 0.4rem;
        align-items: center;
        margin-top: 0.8rem;
        flex-wrap: wrap;
    }
    .step {
        background: #21262d;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 0.3rem 0.7rem;
        color: #8b949e;
        font-size: 0.78rem;
    }
    .arrow { color: #30363d; font-size: 0.8rem; }
</style>

<div class="page-header">
    <h1>🔍 Risk Query</h1>
    <p>Describe a supply chain scenario to trigger the 6-agent analysis pipeline.</p>
</div>
""", unsafe_allow_html=True)


@st.cache_resource
def _init_db_once():
    init_db()


_init_db_once()

st.markdown("""
<div class="status-box">
    <strong style="color:#58a6ff;">Pipeline</strong>
    <div class="pipeline">
        <span class="step">📡 Data Retriever</span>
        <span class="arrow">→</span>
        <span class="step">🐻 Bear</span>
        <span class="step">🐂 Bull</span>
        <span class="step">🌍 Geopolitical</span>
        <span class="arrow">→</span>
        <span class="step">⚖️ Judge</span>
        <span class="arrow">→</span>
        <span class="step">🛡️ GuardRail</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.form("query_form"):
    query = st.text_area(
        "Describe the supply chain scenario",
        placeholder="e.g. semiconductor supply from Taiwan for consumer electronics",
        height=110,
    )
    col1, col2 = st.columns(2)
    company = col1.text_input("Company / Ticker (optional)", placeholder="e.g. AAPL")
    region = col2.text_input("Region (optional)", placeholder="e.g. Taiwan, Southeast Asia")
    submitted = st.form_submit_button("▶  Run Analysis", use_container_width=True, type="primary")

if submitted and query.strip():
    with st.status("Running 6-agent pipeline…", expanded=True) as status:
        st.write("📡 Fetching news, EDGAR filings, and RSS feeds…")
        try:
            result = run_pipeline(query=query, company=company, region=region)
            st.write("🐻 🐂 🌍 Analysts complete")
            st.write("⚖️ Judge synthesizing verdict…")
            st.write("🛡️ GuardRail running checks…")
            run_id = save_run(result)
            st.session_state["last_result"] = result
            st.session_state["last_run_id"] = run_id
            status.update(label=f"✅ Analysis complete — run #{run_id}", state="complete")
            score = result.get("risk_score") or 0
            label = (result.get("final_output") or {}).get("risk_label", "")
            st.success(f"**Risk Score: {score:.0f}/100 — {label}**  ·  View full breakdown on the Results page.")
            if result.get("partial_context"):
                failed = ", ".join(result.get("failed_sources", []))
                st.warning(f"⚠️ Partial context — some sources failed: **{failed}**. Results may be incomplete.")
        except Exception as e:
            status.update(label="❌ Pipeline error", state="error")
            st.error(f"{e}")
elif submitted:
    st.warning("Please enter a query.")
