import json
import streamlit as st

st.set_page_config(page_title="GuardRail · Supply Chain Risk", layout="wide", page_icon="🛡️")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0f1117; }
    [data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }
    .page-header { padding-top: 1.5rem; margin-bottom: 1.5rem; }
    .page-header h1 { color: #e6edf3; font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; }
    .page-header p { color: #8b949e; margin: 0; }

    /* Trust card */
    .trust-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 1.4rem;
        text-align: center;
    }
    .trust-card .agent-name { color: #8b949e; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.6rem; }
    .trust-card .trust-score { font-size: 2.4rem; font-weight: 800; line-height: 1; }
    .trust-card .trust-bar { margin-top: 0.6rem; background: #21262d; border-radius: 4px; height: 6px; overflow: hidden; }
    .trust-card .trust-fill { height: 100%; border-radius: 4px; }
    .trust-high { color: #3fb950; }
    .trust-med  { color: #d29922; }
    .trust-low  { color: #f85149; }
    .fill-high  { background: #3fb950; }
    .fill-med   { background: #d29922; }
    .fill-low   { background: #f85149; }

    /* Confidence banner */
    .conf-banner {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 1.4rem 1.8rem;
        display: flex;
        align-items: center;
        gap: 3rem;
        flex-wrap: wrap;
        margin: 1.5rem 0;
    }
    .conf-metric { text-align: center; }
    .conf-metric .label { color: #8b949e; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; }
    .conf-metric .value { color: #e6edf3; font-size: 1.8rem; font-weight: 700; }

    /* Flag card */
    .flag-card {
        background: #2d1a06;
        border: 1px solid #f0883e33;
        border-left: 4px solid #f0883e;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .flag-card .flag-agent { color: #f0883e; font-size: 0.78rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; }
    .flag-card .flag-claim { color: #e6edf3; font-size: 0.9rem; margin: 0.4rem 0; }
    .flag-card .flag-issue { color: #8b949e; font-size: 0.85rem; }

    /* Notes box */
    .notes-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff;
        border-radius: 8px;
        padding: 1rem 1.4rem;
        color: #c9d1d9;
        font-size: 0.9rem;
        line-height: 1.7;
        margin-top: 1.5rem;
    }
</style>

<div class="page-header">
    <h1>🛡️ GuardRail Monitor</h1>
    <p>Agent trust scores, hallucination flags, and confidence bands from the meta-agent.</p>
</div>
""", unsafe_allow_html=True)

result = st.session_state.get("last_result")
if not result:
    st.info("Run a query on the **Search** page first.")
    st.stop()

report = result.get("guardrail_report")
if isinstance(report, str):
    try:
        report = json.loads(report)
    except Exception:
        report = None

if not report:
    st.warning("No guardrail report available for this run.")
    st.stop()

# ── Trust scores ──────────────────────────────────────────────────────────────
st.markdown("### Agent Trust Scores")
trust = report.get("trust_scores", {})
agents = [("bear", "🐻 Bear"), ("bull", "🐂 Bull"), ("geopolitical", "🌍 Geo"), ("judge", "⚖️ Judge")]
cols = st.columns(4)

for col, (key, display) in zip(cols, agents):
    val = float(trust.get(key, 0.0))
    pct = int(val * 100)
    if val >= 0.7:
        score_cls, fill_cls = "trust-high", "fill-high"
    elif val >= 0.5:
        score_cls, fill_cls = "trust-med", "fill-med"
    else:
        score_cls, fill_cls = "trust-low", "fill-low"

    col.markdown(f"""
    <div class="trust-card">
        <div class="agent-name">{display}</div>
        <div class="trust-score {score_cls}">{val:.2f}</div>
        <div class="trust-bar"><div class="trust-fill {fill_cls}" style="width:{pct}%"></div></div>
    </div>
    """, unsafe_allow_html=True)

# ── Confidence band ───────────────────────────────────────────────────────────
band = report.get("confidence_band", {})
overall = report.get("overall_confidence", "—")
overall_color = {"High": "#3fb950", "Medium": "#d29922", "Low": "#f85149"}.get(overall, "#8b949e")

st.markdown(f"""
<div class="conf-banner">
    <div class="conf-metric">
        <div class="label">Low Bound</div>
        <div class="value">{band.get('low', '—')}</div>
    </div>
    <div class="conf-metric">
        <div class="label">High Bound</div>
        <div class="value">{band.get('high', '—')}</div>
    </div>
    <div class="conf-metric">
        <div class="label">Overall Confidence</div>
        <div class="value" style="color:{overall_color}">{overall}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Flagged claims ────────────────────────────────────────────────────────────
flagged = report.get("flagged_claims", [])
st.markdown(f"### Flagged Claims &nbsp;<span style='background:#21262d;border:1px solid #30363d;border-radius:20px;padding:0.15rem 0.6rem;font-size:0.8rem;color:#8b949e'>{len(flagged)}</span>", unsafe_allow_html=True)

if flagged:
    for flag in flagged:
        st.markdown(f"""
        <div class="flag-card">
            <div class="flag-agent">⚠️ {flag.get('agent', '?').upper()}</div>
            <div class="flag-claim">"{flag.get('claim', '—')}"</div>
            <div class="flag-issue">↳ {flag.get('issue', '—')}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.success("No flagged claims — all analyst outputs appear grounded in source documents.")

notes = report.get("guardrail_notes", "")
if notes:
    st.markdown(f'<div class="notes-box"><strong style="color:#58a6ff;">📋 Guardrail Notes</strong><br><br>{notes}</div>', unsafe_allow_html=True)
