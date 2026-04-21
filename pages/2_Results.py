import json
import streamlit as st
from tools.postgres_db import get_recent_runs, get_run_by_id

st.set_page_config(page_title="Results · Supply Chain Risk", layout="wide", page_icon="📊")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0f1117; }
    [data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }
    .page-header h1 { color: #e6edf3; font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; padding-top: 1.5rem; }
    .page-header p { color: #8b949e; margin: 0 0 1.5rem 0; }

    /* Score banner */
    .score-banner {
        border-radius: 12px;
        padding: 1.8rem 2rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 2rem;
        flex-wrap: wrap;
    }
    .score-banner .score-num {
        font-size: 4rem;
        font-weight: 800;
        line-height: 1;
    }
    .score-banner .score-meta { flex: 1; }
    .score-banner .score-label {
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .score-banner .score-query { color: #8b949e; font-size: 0.9rem; }

    /* Risk level colors */
    .risk-low    { background: #0d2818; border: 1px solid #2ea04326; }
    .risk-mod    { background: #271d06; border: 1px solid #d2992026; }
    .risk-high   { background: #2d1a06; border: 1px solid #f0883e26; }
    .risk-crit   { background: #2d0f0f; border: 1px solid #f8514926; }

    .risk-low .score-num    { color: #3fb950; }
    .risk-mod .score-num    { color: #d29922; }
    .risk-high .score-num   { color: #f0883e; }
    .risk-crit .score-num   { color: #f85149; }

    .risk-low .score-label  { color: #3fb950; }
    .risk-mod .score-label  { color: #d29922; }
    .risk-high .score-label { color: #f0883e; }
    .risk-crit .score-label { color: #f85149; }

    /* Action badge */
    .action-badge {
        display: inline-block;
        padding: 0.35rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    .action-watch    { background: #0d2818; color: #3fb950; border: 1px solid #3fb95044; }
    .action-monitor  { background: #271d06; color: #d29922; border: 1px solid #d2992244; }
    .action-escalate { background: #2d1a06; color: #f0883e; border: 1px solid #f0883e44; }
    .action-immediate{ background: #2d0f0f; color: #f85149; border: 1px solid #f8514944; }

    /* Cards */
    .card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 1.2rem;
        height: 100%;
    }
    .card h4 { color: #58a6ff; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 0.8rem 0; }
    .card ul { margin: 0; padding-left: 1.2rem; color: #c9d1d9; font-size: 0.9rem; line-height: 1.8; }

    /* Verdict box */
    .verdict-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff;
        border-radius: 8px;
        padding: 1.2rem 1.4rem;
        color: #c9d1d9;
        font-size: 0.95rem;
        line-height: 1.7;
        margin-bottom: 1.5rem;
    }

    /* Tabs */
    [data-testid="stTabs"] button { color: #8b949e !important; }
    [data-testid="stTabs"] button[aria-selected="true"] { color: #e6edf3 !important; border-bottom-color: #58a6ff !important; }
</style>
""", unsafe_allow_html=True)

# ── Run selector ──────────────────────────────────────────────────────────────
result = st.session_state.get("last_result")

@st.cache_data(ttl=30)
def _cached_recent_runs() -> list[dict]:
    try:
        return get_recent_runs(limit=15)
    except Exception:
        return []


with st.sidebar:
    st.markdown("### Load a past run")
    recent = _cached_recent_runs()
    if recent:
        options = {f"#{r['id']} — {r['query'][:45]}": r["id"] for r in recent}
        chosen = st.selectbox("Select run", list(options.keys()), label_visibility="collapsed")
        if st.button("Load run", use_container_width=True):
            result = get_run_by_id(options[chosen])
            if result and isinstance(result.get("final_output"), str):
                result["final_output"] = json.loads(result["final_output"])
            if result and isinstance(result.get("guardrail_report"), str):
                result["guardrail_report"] = json.loads(result["guardrail_report"])
            st.session_state["last_result"] = result
            st.rerun()
    else:
        st.caption("No past runs yet.")

st.markdown('<div class="page-header"><h1>📊 Analysis Results</h1><p>Judge verdict, analyst debate, and risk breakdown.</p></div>', unsafe_allow_html=True)

if not result:
    st.info("Run a query on the **Search** page, or load a past run from the sidebar.")
    st.stop()

# ── Score banner ──────────────────────────────────────────────────────────────
final = result.get("final_output") or {}
raw_score = result.get("risk_score") or final.get("risk_score", 0)
score = float(raw_score) if raw_score is not None else 0.0
label = final.get("risk_label", "Unknown")
action = final.get("recommended_action", "—")

risk_class = (
    "risk-low" if score < 21 else
    "risk-mod" if score < 41 else
    "risk-high" if score < 61 else
    "risk-crit"
)

action_class = {
    "Watch": "action-watch",
    "Monitor": "action-monitor",
    "Escalate": "action-escalate",
    "Immediate Action": "action-immediate",
}.get(action, "action-monitor")

meta = ""
if result.get("company"):
    meta += f"<strong>Company:</strong> {result['company']}&nbsp;&nbsp;"
if result.get("region"):
    meta += f"<strong>Region:</strong> {result['region']}&nbsp;&nbsp;"

st.markdown(f"""
<div class="score-banner {risk_class}">
    <div class="score-num">{score:.0f}</div>
    <div class="score-meta">
        <div class="score-label">{label} Risk</div>
        <div class="score-query">📌 {result.get('query', '')}</div>
        <div style="margin-top:0.3rem; color:#8b949e; font-size:0.85rem;">{meta}</div>
        <span class="action-badge {action_class}">⚡ {action}</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.progress(score / 100)

# ── Verdict ───────────────────────────────────────────────────────────────────
st.markdown(f'<div class="verdict-box"><strong style="color:#58a6ff;">⚖️ Judge Verdict</strong><br><br>{result.get("judge_verdict", "—")}</div>', unsafe_allow_html=True)

# ── Risks / Mitigants / Consensus ─────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    risks = "".join(f"<li>{r}</li>" for r in final.get("top_3_risks", []))
    st.markdown(f'<div class="card"><h4>🔴 Top Risks</h4><ul>{risks or "<li>—</li>"}</ul></div>', unsafe_allow_html=True)

with col2:
    mit = "".join(f"<li>{m}</li>" for m in final.get("top_3_mitigants", []))
    st.markdown(f'<div class="card"><h4>🟢 Top Mitigants</h4><ul>{mit or "<li>—</li>"}</ul></div>', unsafe_allow_html=True)

with col3:
    cons = "".join(f"<li>{c}</li>" for c in final.get("consensus_points", []))
    dis = "".join(f"<li>{d}</li>" for d in final.get("key_disagreements", []))
    st.markdown(f'<div class="card"><h4>🤝 Consensus</h4><ul>{cons or "<li>—</li>"}</ul><h4 style="margin-top:1rem;">⚡ Disagreements</h4><ul>{dis or "<li>—</li>"}</ul></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Analyst debate ────────────────────────────────────────────────────────────
st.markdown("### Analyst Debate")
tab_bear, tab_bull, tab_geo = st.tabs(["🐻 Bear Analyst", "🐂 Bull Analyst", "🌍 Geopolitical"])

with tab_bear:
    st.markdown(result.get("bear_analysis") or "_No output_")
with tab_bull:
    st.markdown(result.get("bull_analysis") or "_No output_")
with tab_geo:
    st.markdown(result.get("geopolitical_analysis") or "_No output_")
