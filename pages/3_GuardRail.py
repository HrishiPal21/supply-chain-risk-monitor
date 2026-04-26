import json
import html as _html
import streamlit as st
from ui.theme import apply_theme
from ui.sidebar import render_sidebar

def _e(text: str) -> str:
    return _html.escape(str(text or ""))

st.set_page_config(page_title="GuardRail · Supply Chain Risk", layout="wide", page_icon="🛡️")

apply_theme("""
    /* Trust score cards */
    .trust-card {
        background: #ffffff; border: 1px solid #e2e8f0;
        border-radius: 12px; padding: 1.4rem; text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .trust-card .agent-name {
        color: #64748b; font-size: 0.75rem; text-transform: uppercase;
        letter-spacing: 0.07em; margin-bottom: 0.6rem; font-weight: 600;
    }
    .trust-card .trust-score { font-size: 2.4rem; font-weight: 800; line-height: 1; }
    .trust-card .trust-bar { margin-top: 0.7rem; background: #e2e8f0; border-radius: 4px; height: 7px; overflow: hidden; }
    .trust-card .trust-fill { height: 100%; border-radius: 4px; }
    .trust-high { color: #16a34a; }
    .trust-med  { color: #b45309; }
    .trust-low  { color: #dc2626; }
    .fill-high  { background: #16a34a; }
    .fill-med   { background: #f59e0b; }
    .fill-low   { background: #dc2626; }

    /* Confidence band */
    .conf-banner {
        background: #ffffff; border: 1px solid #e2e8f0;
        border-radius: 12px; padding: 1.4rem 2rem;
        display: flex; align-items: center; gap: 3rem;
        flex-wrap: wrap; margin: 1.2rem 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .conf-metric { text-align: center; }
    .conf-metric .label {
        color: #64748b; font-size: 0.75rem; text-transform: uppercase;
        letter-spacing: 0.06em; font-weight: 600;
    }
    .conf-metric .value { color: #0f2444; font-size: 1.8rem; font-weight: 700; }

    /* Flagged claim cards */
    .flag-card {
        background: #fff7ed; border: 1px solid #fdba74;
        border-left: 4px solid #c2410c; border-radius: 8px;
        padding: 1rem 1.2rem; margin-bottom: 0.8rem;
    }
    .flag-card .flag-agent { color: #c2410c; font-size: 0.75rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; }
    .flag-card .flag-claim { color: #1a2744; font-size: 0.9rem; margin: 0.4rem 0; }
    .flag-card .flag-issue { color: #64748b; font-size: 0.84rem; }

    /* Notes */
    .notes-box {
        background: #ffffff; border: 1px solid #e2e8f0;
        border-left: 4px solid #1a5276; border-radius: 8px;
        padding: 1rem 1.4rem; color: #374151;
        font-size: 0.9rem; line-height: 1.75; margin-top: 1.2rem;
    }
""")

st.markdown("""
<div class="page-header">
    <h1>GuardRail Monitor</h1>
    <p>Agent trust scores, hallucination flags, and confidence bands from the meta-agent.</p>
</div>
""", unsafe_allow_html=True)

render_sidebar()

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
    st.warning("No GuardRail report available for this run.")
    st.stop()

# ── Trust scores ──────────────────────────────────────────────────────────────
st.markdown("### Agent Trust Scores")
trust = report.get("trust_scores", {})
agents = [("bear", "Bear"), ("bull", "Bull"), ("geopolitical", "Geopolitical"), ("judge", "Judge")]
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
overall_color = {"High": "#16a34a", "Medium": "#b45309", "Low": "#dc2626"}.get(overall, "#64748b")

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
        issue  = _e(flag.get('issue', '—'))
        detail = _e(flag.get('detail', ''))
        detail_html = f"<div class='flag-issue' style='margin-top:0.3rem;'>Detail: {detail}</div>" if detail else ""
        st.markdown(f"""
        <div class="flag-card">
            <div class="flag-agent">{_e(flag.get('agent', '?')).upper()} &mdash; {issue}</div>
            <div class="flag-claim">"{_e(flag.get('claim', '—'))}"</div>
            {detail_html}
        </div>
        """, unsafe_allow_html=True)
else:
    st.success("No flagged claims — all analyst outputs appear grounded in source documents.")

notes = report.get("guardrail_notes", "")
if notes:
    st.markdown(f'<div class="notes-box"><strong>GuardRail Notes</strong><br><br>{_e(notes)}</div>', unsafe_allow_html=True)
