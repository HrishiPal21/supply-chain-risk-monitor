import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from agents.graph import run_pipeline
from tools.postgres_db import save_run, init_db

st.set_page_config(page_title="Search · Supply Chain Risk", layout="wide", page_icon="🔍")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    [data-testid="stAppViewContainer"] { background: #f0f4f8; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f2444 0%, #1a3a5c 100%); border-right: none; }
    [data-testid="stSidebar"] * { color: #e2edf7 !important; }
    [data-testid="stSidebarNav"] a { color: #a8c4e0 !important; }
    [data-testid="stSidebarNav"] a:hover { color: #fff !important; }
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] { background: rgba(255,255,255,0.08) !important; border-color: rgba(255,255,255,0.2) !important; }
    [data-testid="stSidebar"] button { background: rgba(255,255,255,0.12) !important; border-color: rgba(255,255,255,0.25) !important; color: #fff !important; }
    header[data-testid="stHeader"] { background: transparent; }

    .page-header {
        background: linear-gradient(135deg, #0f2444 0%, #1a5276 100%);
        border-radius: 12px; padding: 1.8rem 2rem; margin-bottom: 1.5rem;
    }
    .page-header h1 { color: #fff; font-size: 1.8rem; font-weight: 800; margin: 0 0 0.2rem 0; }
    .page-header p  { color: #a8c4e0; margin: 0; font-size: 0.9rem; }

    textarea, input[type="text"] {
        background: #fff !important; color: #0f2444 !important;
        border: 1.5px solid #c8daf0 !important; border-radius: 8px !important;
    }
    textarea:focus, input[type="text"]:focus { border-color: #1a5276 !important; }

    /* Pipeline banner */
    .status-box {
        background: #e8f0f9; border: 1px solid #c8daf0;
        border-left: 4px solid #1a5276;
        border-radius: 8px; padding: 0.9rem 1.2rem; margin-bottom: 1.2rem; font-size: 0.88rem;
    }
    .pipeline { display: flex; gap: 0.4rem; align-items: center; margin-top: 0.5rem; flex-wrap: wrap; }
    .step {
        background: #fff; border: 1px solid #c8daf0; border-radius: 6px;
        padding: 0.28rem 0.7rem; color: #1a3a5c; font-size: 0.76rem; font-weight: 500;
    }
    .arrow { color: #93b8d4; font-size: 0.8rem; }

    /* Section label */
    .section-label {
        color: #1a3a5c; font-size: 0.75rem; text-transform: uppercase;
        letter-spacing: 0.08em; margin-bottom: 0.6rem; font-weight: 700;
    }

    /* Streamlit buttons as scenario tiles */
    div[data-testid="stButton"] > button {
        background: #fff !important; border: 1.5px solid #e2e8f0 !important;
        color: #0f2444 !important; border-radius: 10px !important;
        padding: 0.8rem !important; text-align: left !important;
        font-size: 0.85rem !important; line-height: 1.5 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: border-color 0.15s, box-shadow 0.15s !important;
    }
    div[data-testid="stButton"] > button:hover {
        border-color: #1a5276 !important;
        box-shadow: 0 3px 10px rgba(26,82,118,0.12) !important;
    }

    /* Form submit button */
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #0f2444, #1a5276) !important;
        color: #fff !important; border: none !important;
        border-radius: 8px !important; font-weight: 600 !important;
        font-size: 0.95rem !important; padding: 0.6rem 1.5rem !important;
        box-shadow: 0 2px 8px rgba(15,36,68,0.25) !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        box-shadow: 0 4px 16px rgba(15,36,68,0.35) !important;
    }

    /* Radio */
    div[data-testid="stRadio"] label { color: #1a3a5c !important; font-weight: 500; }

    /* Selectbox */
    div[data-testid="stSelectbox"] label { color: #1a3a5c !important; font-weight: 600; }

    /* Divider */
    hr { border-color: #e2e8f0 !important; }
</style>

<div class="page-header">
    <h1>Supply Chain Risk Analysis</h1>
    <p>Pick a scenario, use the guided builder, or write your own — the 7-agent pipeline does the rest.</p>
</div>
""", unsafe_allow_html=True)


@st.cache_resource
def _init_db_once():
    init_db()

_init_db_once()

# ── Pipeline banner ────────────────────────────────────────────────────────────
st.markdown("""
<div class="status-box">
    <strong style="color:#58a6ff;">Pipeline</strong>
    <div class="pipeline">
        <span class="step">Data Retriever</span>
        <span class="arrow">→</span>
        <span class="step">Exposure Assessment</span>
        <span class="arrow">→</span>
        <span class="step">Bear</span>
        <span class="step">Bull</span>
        <span class="step">Geopolitical</span>
        <span class="arrow">→</span>
        <span class="step">Judge</span>
        <span class="arrow">→</span>
        <span class="step">GuardRail</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Session state defaults ─────────────────────────────────────────────────────
if "prefill_query" not in st.session_state:
    st.session_state["prefill_query"] = ""
if "prefill_company" not in st.session_state:
    st.session_state["prefill_company"] = ""
if "prefill_region" not in st.session_state:
    st.session_state["prefill_region"] = ""

# ── Mode toggle ────────────────────────────────────────────────────────────────
mode = st.radio(
    "Input mode",
    ["Quick Scenarios", "Guided Builder", "Custom Query"],
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# MODE 1 — Quick Scenarios
# ==============================================================================
SCENARIOS = [
    {
        "icon": "💾",
        "title": "Semiconductor shortage — Taiwan",
        "desc": "TSMC concentration risk, US-China tensions, and chip supply to consumer electronics.",
        "query": "semiconductor supply chain disruption from Taiwan geopolitical risk for consumer electronics",
        "company": "",
        "region": "Taiwan",
    },
    {
        "icon": "🚢",
        "title": "Port congestion — West Coast",
        "desc": "LA/Long Beach container backlogs and downstream inventory delays.",
        "query": "port congestion Los Angeles Long Beach freight delays inventory disruption",
        "company": "",
        "region": "United States",
    },
    {
        "icon": "🚗",
        "title": "Automotive chips — Europe",
        "desc": "EV transition supply risks and semiconductor shortages for European automakers.",
        "query": "automotive semiconductor shortage electric vehicle supply chain disruption Europe",
        "company": "",
        "region": "Europe",
    },
    {
        "icon": "💊",
        "title": "Pharma raw materials — India/China",
        "desc": "API sourcing concentration and regulatory risk for pharmaceutical supply chains.",
        "query": "pharmaceutical active pharmaceutical ingredient API supply chain risk India China",
        "company": "",
        "region": "India",
    },
    {
        "icon": "⚡",
        "title": "Rare earth minerals — China",
        "desc": "Lithium, cobalt, and rare earth export controls impacting battery and tech supply.",
        "query": "rare earth minerals lithium cobalt supply chain China export controls battery technology",
        "company": "",
        "region": "China",
    },
    {
        "icon": "🌾",
        "title": "Food supply — Black Sea",
        "desc": "Wheat and grain export disruptions from conflict and climate events.",
        "query": "wheat grain food supply chain disruption Black Sea Ukraine Russia export",
        "company": "",
        "region": "Ukraine",
    },
]

if mode == "Quick Scenarios":
    st.markdown('<div class="section-label">Choose a scenario to pre-fill the query</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, scenario in enumerate(SCENARIOS):
        with cols[i % 3]:
            if st.button(
                f"{scenario['title']}\n\n_{scenario['desc']}_",
                key=f"tile_{i}",
                use_container_width=True,
            ):
                st.session_state["prefill_query"] = scenario["query"]
                st.session_state["prefill_company"] = scenario["company"]
                st.session_state["prefill_region"] = scenario["region"]
                st.rerun()

    if st.session_state["prefill_query"]:
        st.success(f"**Selected:** {st.session_state['prefill_query'][:80]}…  _(edit below if needed)_")

# ==============================================================================
# MODE 2 — Guided Builder
# ==============================================================================
elif mode == "Guided Builder":
    st.markdown('<div class="section-label">Step 1 — Pick your focus</div>', unsafe_allow_html=True)

    INDUSTRIES = [
        "Semiconductors & Electronics",
        "Automotive & EV",
        "Pharmaceuticals & Healthcare",
        "Food & Agriculture",
        "Energy & Utilities",
        "Retail & Consumer Goods",
        "Aerospace & Defense",
        "Chemicals & Materials",
    ]
    REGIONS = [
        "Taiwan", "China", "Southeast Asia", "India",
        "Europe", "United States", "Middle East", "Latin America",
        "Black Sea / Eastern Europe", "Sub-Saharan Africa",
    ]
    RISK_TYPES = [
        "Geopolitical tension",
        "Trade tariffs & export controls",
        "Natural disaster / climate event",
        "Port congestion & logistics disruption",
        "Supplier concentration risk",
        "Regulatory & compliance risk",
        "Cyber attack on infrastructure",
        "Labor strike / workforce disruption",
    ]

    col1, col2, col3 = st.columns(3)
    industry  = col1.selectbox("Industry", INDUSTRIES)
    region    = col2.selectbox("Region", REGIONS)
    risk_type = col3.selectbox("Risk type", RISK_TYPES)

    st.markdown('<div class="section-label" style="margin-top:1rem;">Step 2 — Optional company focus</div>', unsafe_allow_html=True)
    guided_company = st.text_input("Company name or ticker (optional)", placeholder="e.g. Apple, Nike, AAPL, TSMC")

    if st.button("Build Query →", type="secondary"):
        composed = (
            f"{risk_type.lower()} impact on {industry.lower()} "
            f"supply chain in {region}"
        )
        st.session_state["prefill_query"]   = composed
        st.session_state["prefill_company"] = guided_company
        st.session_state["prefill_region"]  = region
        st.rerun()

    if st.session_state["prefill_query"]:
        st.success(f"**Built query:** {st.session_state['prefill_query']}")

# ==============================================================================
# MODE 3 — Custom Query (original blank form)
# ==============================================================================
else:
    st.markdown('<div class="section-label">Write your own scenario</div>', unsafe_allow_html=True)
    custom = st.text_area(
        "Scenario",
        placeholder="e.g. semiconductor supply from Taiwan for consumer electronics",
        height=90,
        label_visibility="collapsed",
    )
    if custom:
        st.session_state["prefill_query"] = custom

# ── Shared run form ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-label">Review & run</div>', unsafe_allow_html=True)

with st.form("query_form"):
    query = st.text_area(
        "Query",
        value=st.session_state.get("prefill_query", ""),
        height=100,
        label_visibility="collapsed",
        placeholder="Your scenario will appear here — or type directly.",
    )
    col1, col2 = st.columns(2)
    company = col1.text_input(
        "Company name or ticker (optional)",
        value=st.session_state.get("prefill_company", ""),
        placeholder="e.g. Apple, Nike, AAPL, TSMC",
    )
    region = col2.text_input(
        "Region (optional)",
        value=st.session_state.get("prefill_region", ""),
        placeholder="e.g. Taiwan, Southeast Asia",
    )
    submitted = st.form_submit_button("Run Analysis", use_container_width=True, type="primary")

# ── Pipeline execution ─────────────────────────────────────────────────────────
if submitted and query.strip():
    with st.status("Running pipeline...", expanded=True) as status:
        ph_data      = st.empty()
        ph_exposure  = st.empty()
        ph_analysts  = st.empty()
        ph_judge     = st.empty()
        ph_guardrail = st.empty()

        ph_data.write("Fetching news, RSS, HTML sources & EDGAR filings...")
        ph_exposure.write("Exposure assessment — queued")
        ph_analysts.write("Bear / Bull / Geopolitical analysts — queued")
        ph_judge.write("Judge — queued")
        ph_guardrail.write("GuardRail — queued")

        try:
            result = run_pipeline(query=query, company=company, region=region)

            doc_count = len(result.get("retrieved_docs", []))
            failed_sources = result.get("failed_sources", [])
            ph_data.write(f"Complete — {doc_count} docs" + (f" (failed: {', '.join(failed_sources)})" if failed_sources else ""))
            ph_exposure.write(f"Exposure assessment — {result.get('exposure_level') or 'Unknown'}")
            ph_analysts.write("Bear / Bull / Geopolitical analysts — complete")
            ph_judge.write(f"Judge — raw score {result.get('raw_risk_score', '?'):.0f} → adjusted {result.get('risk_score', '?'):.0f}")
            confidence = (result.get("guardrail_report") or {}).get("overall_confidence", "?")
            ph_guardrail.write(f"GuardRail — confidence {confidence}")

            run_id = save_run(result)
            st.session_state["last_result"] = result
            st.session_state["last_run_id"] = run_id
            st.session_state["prefill_query"]   = ""
            st.session_state["prefill_company"] = ""
            st.session_state["prefill_region"]  = ""
            run_label = f"run #{run_id}" if run_id else "session (DB offline)"
            status.update(label=f"Analysis complete — {run_label}", state="complete")

            score = result.get("risk_score") or 0
            label = (result.get("final_output") or {}).get("risk_label", "")
            st.success(f"**Risk Score: {score:.0f}/100 — {label}**  ·  View full breakdown on the Results page.")

            if result.get("partial_context"):
                failed = ", ".join(failed_sources)
                st.warning(f"Partial context — some sources failed: **{failed}**. Results may be incomplete.")

            usable_docs = [d for d in result.get("retrieved_docs", []) if (d.get("text") or "").strip()]
            if doc_count > 0 and not usable_docs:
                st.warning("All retrieved documents had empty text. Analysis is based on query alone — treat results with caution.")
            elif doc_count == 0:
                st.warning("No documents were retrieved. Analysis is based on query alone — treat results with caution.")

        except Exception as e:
            status.update(label="Pipeline error", state="error")
            st.error(f"{e}")
elif submitted:
    st.warning("Please enter a query.")
