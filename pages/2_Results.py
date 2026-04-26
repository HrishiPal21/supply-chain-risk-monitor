import json
import html as _html
import streamlit as st
from tools.postgres_db import get_recent_runs, get_run_by_id
from ui.theme import apply_theme, source_badge, confidence_badge
from ui.sidebar import render_sidebar

def _e(text: str) -> str:
    """HTML-escape dynamic LLM text before injecting into markup."""
    return _html.escape(str(text or ""))

st.set_page_config(page_title="Results · Supply Chain Risk", layout="wide", page_icon="📊")

apply_theme("""
    /* Score banner */
    .score-banner {
        border-radius: 14px; padding: 1.8rem 2rem;
        margin-bottom: 1.2rem; display: flex;
        align-items: center; gap: 2rem; flex-wrap: wrap;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .score-banner .score-num  { font-size: 4.5rem; font-weight: 800; line-height: 1; }
    .score-banner .score-meta { flex: 1; }
    .score-banner .score-label { font-size: 1.3rem; font-weight: 700; margin-bottom: 0.3rem; }
    .score-banner .score-query { font-size: 0.88rem; opacity: 0.75; }

    /* Risk colour variants */
    .risk-low  { background: #f0faf4; border: 1.5px solid #86efac; }
    .risk-mod  { background: #fffbeb; border: 1.5px solid #fcd34d; }
    .risk-high { background: #fff7ed; border: 1.5px solid #fdba74; }
    .risk-crit { background: #fef2f2; border: 1.5px solid #fca5a5; }

    .risk-low  .score-num, .risk-low  .score-label { color: #16a34a; }
    .risk-mod  .score-num, .risk-mod  .score-label { color: #b45309; }
    .risk-high .score-num, .risk-high .score-label { color: #c2410c; }
    .risk-crit .score-num, .risk-crit .score-label { color: #dc2626; }

    /* Partial-context badge */
    .partial-badge {
        display: inline-block; padding: 0.2rem 0.65rem;
        border-radius: 10px; font-size: 0.7rem; font-weight: 600;
        background: #fff7ed; color: #c2410c; border: 1px solid #fdba74;
        vertical-align: middle; margin-left: 0.4rem;
    }

    /* Source doc expander header badges inline */
    .src-row { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.3rem; }
""")

# ── Run selector ──────────────────────────────────────────────────────────────
result = st.session_state.get("last_result")

@st.cache_data(ttl=30)
def _cached_recent_runs() -> list[dict]:
    try:
        return get_recent_runs(limit=15)
    except Exception:
        return []


render_sidebar()

with st.sidebar:
    st.markdown("""
    <div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:0.9rem; margin-top:0.5rem;">
        <div style="font-size:0.68rem; text-transform:uppercase; letter-spacing:0.09em;
                    color:#a8c4e0; font-weight:600; margin-bottom:0.6rem;">Load Past Run</div>
    </div>
    """, unsafe_allow_html=True)
    recent = _cached_recent_runs()
    if recent:
        options = {f"#{r['id']} — {r['query'][:40]}": r["id"] for r in recent}
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

st.markdown('<div class="page-header"><h1>Analysis Results</h1><p>Judge verdict, analyst debate, and risk breakdown.</p></div>', unsafe_allow_html=True)

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

# Confidence badge
gr = result.get("guardrail_report") or {}
conf_level = gr.get("overall_confidence", "")
conf_html = confidence_badge(conf_level) if conf_level else ""

# Partial context badge
partial_html = '<span class="partial-badge">Partial Context</span>' if result.get("partial_context") else ""

# Run ID and elapsed — shown as caption below banner, not inside HTML
run_id = st.session_state.get("last_run_id")
elapsed = st.session_state.get("last_elapsed")

meta = ""
if result.get("company"):
    meta += f"<strong>Company:</strong> {_e(result['company'])}&nbsp;&nbsp;"
if result.get("region"):
    meta += f"<strong>Region:</strong> {_e(result['region'])}&nbsp;&nbsp;"

st.html(f"""
<style>
  .score-banner {{
    border-radius:14px; padding:1.8rem 2rem; margin-bottom:1.2rem;
    display:flex; align-items:center; gap:2rem; flex-wrap:wrap;
    box-shadow:0 2px 8px rgba(0,0,0,0.08); font-family:'Inter',sans-serif;
  }}
  .risk-low  {{ background:#f0faf4; border:1.5px solid #86efac; }}
  .risk-mod  {{ background:#fffbeb; border:1.5px solid #fcd34d; }}
  .risk-high {{ background:#fff7ed; border:1.5px solid #fdba74; }}
  .risk-crit {{ background:#fef2f2; border:1.5px solid #fca5a5; }}
  .score-num {{ font-size:4.5rem; font-weight:800; line-height:1; }}
  .risk-low  .score-num, .risk-low  .score-label {{ color:#16a34a; }}
  .risk-mod  .score-num, .risk-mod  .score-label {{ color:#b45309; }}
  .risk-high .score-num, .risk-high .score-label {{ color:#c2410c; }}
  .risk-crit .score-num, .risk-crit .score-label {{ color:#dc2626; }}
  .score-meta {{ flex:1; }}
  .score-label {{ font-size:1.3rem; font-weight:700; margin-bottom:0.3rem; }}
  .score-query {{ font-size:0.88rem; opacity:0.75; }}
  .action-badge {{
    display:inline-block; padding:0.3rem 1rem; border-radius:20px;
    font-size:0.82rem; font-weight:600; margin-top:0.5rem;
  }}
  .action-watch     {{ background:#dcfce7; color:#15803d; border:1px solid #86efac; }}
  .action-monitor   {{ background:#fef9c3; color:#854d0e; border:1px solid #fcd34d; }}
  .action-escalate  {{ background:#ffedd5; color:#c2410c; border:1px solid #fdba74; }}
  .action-immediate {{ background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5; }}
  .conf-badge {{
    display:inline-block; padding:0.25rem 0.8rem;
    border-radius:12px; font-size:0.75rem; font-weight:600;
  }}
  .conf-high   {{ background:#dcfce7; color:#15803d; border:1px solid #86efac; }}
  .conf-medium {{ background:#fef9c3; color:#854d0e; border:1px solid #fcd34d; }}
  .conf-low    {{ background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5; }}
  .partial-badge {{
    display:inline-block; padding:0.2rem 0.65rem; border-radius:10px;
    font-size:0.7rem; font-weight:600; background:#fff7ed;
    color:#c2410c; border:1px solid #fdba74; vertical-align:middle; margin-left:0.4rem;
  }}
</style>
<div class="score-banner {risk_class}">
    <div class="score-num">{score:.0f}</div>
    <div class="score-meta">
        <div class="score-label">{_e(label)} Risk</div>
        <div class="score-query">{_e(result.get('query', ''))}</div>
        <div style="margin-top:0.3rem; color:#64748b; font-size:0.85rem;">{meta}</div>
        <div style="margin-top:0.5rem; display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;">
            <span class="action-badge {action_class}">{_e(action)}</span>
            {conf_html}
            {partial_html}
        </div>
    </div>
</div>
""")

st.progress(score / 100)

# Run ID + elapsed as caption below banner
_meta_parts = []
if run_id:
    _meta_parts.append(f"Run #{run_id}")
if elapsed:
    _meta_parts.append(f"{elapsed:.1f}s")
if _meta_parts:
    st.caption(" · ".join(_meta_parts))

# ── Export buttons ────────────────────────────────────────────────────────────
with st.expander("Export / Download", expanded=False):
    export_data = {
        "query": result.get("query"),
        "company": result.get("company"),
        "region": result.get("region"),
        "risk_score": result.get("risk_score"),
        "exposure_level": result.get("exposure_level"),
        "final_output": result.get("final_output"),
        "guardrail_report": result.get("guardrail_report"),
        "exposure_profile": result.get("exposure_profile"),
    }
    col_j, col_m = st.columns(2)

    col_j.download_button(
        label="Download JSON",
        data=json.dumps(export_data, indent=2, default=str),
        file_name="supply_chain_risk_report.json",
        mime="application/json",
        use_container_width=True,
    )

    def _build_markdown() -> str:
        fo = result.get("final_output") or {}
        lines = [
            f"# Supply Chain Risk Report",
            f"",
            f"**Query:** {result.get('query', '')}",
        ]
        if result.get("company"):
            lines.append(f"**Company:** {result['company']}")
        if result.get("region"):
            lines.append(f"**Region:** {result['region']}")
        lines += [
            f"",
            f"## Risk Score: {score:.0f}/100 — {label}",
            f"**Recommended Action:** {action}",
            f"**Confidence:** {conf_level or '—'}",
            f"",
            f"## Judge Verdict",
            result.get("judge_verdict") or "—",
            f"",
            f"## Top Risks",
        ]
        for r in fo.get("top_3_risks", []):
            lines.append(f"- {r}")
        lines += ["", "## Top Mitigants"]
        for m in fo.get("top_3_mitigants", []):
            lines.append(f"- {m}")
        lines += ["", "## Exposure", f"**Level:** {result.get('exposure_level', '—')}",
                  result.get("exposure_summary") or "—"]
        return "\n".join(lines)

    col_m.download_button(
        label="Download Markdown",
        data=_build_markdown(),
        file_name="supply_chain_risk_report.md",
        mime="text/markdown",
        use_container_width=True,
    )

# ── Main tabs ─────────────────────────────────────────────────────────────────
tab_overview, tab_exposure, tab_analysts, tab_sources = st.tabs(
    ["Overview", "Exposure", "Analyst Reports", "Sources"]
)

# ── OVERVIEW ──────────────────────────────────────────────────────────────────
with tab_overview:
    left, right = st.columns([3, 2])

    with left:
        st.markdown(
            f'<div class="verdict-box"><strong style="color:#1a5276;">Judge Verdict</strong>'
            f'<br><br>{_e(result.get("judge_verdict", "—"))}</div>',
            unsafe_allow_html=True,
        )
        cons = "".join(f"<li>{_e(c)}</li>" for c in final.get("consensus_points", []))
        dis  = "".join(f"<li>{_e(d)}</li>" for d in final.get("key_disagreements", []))
        st.markdown(f'<div class="card"><h4>Consensus</h4><ul>{cons or "<li>—</li>"}</ul><h4 style="margin-top:1rem;">Disagreements</h4><ul>{dis or "<li>—</li>"}</ul></div>', unsafe_allow_html=True)

    with right:
        risks = "".join(f"<li>{_e(r)}</li>" for r in final.get("top_3_risks", []))
        st.markdown(f'<div class="card"><h4>Top Risks</h4><ul>{risks or "<li>—</li>"}</ul></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        mit = "".join(f"<li>{_e(m)}</li>" for m in final.get("top_3_mitigants", []))
        st.markdown(f'<div class="card"><h4>Top Mitigants</h4><ul>{mit or "<li>—</li>"}</ul></div>', unsafe_allow_html=True)

# ── EXPOSURE ──────────────────────────────────────────────────────────────────
with tab_exposure:
    exposure_level = result.get("exposure_level")
    if not exposure_level:
        st.info("No exposure data for this run.")
    else:
        profile = result.get("exposure_profile") or {}
        raw_score_val = final.get("risk_score_raw") or result.get("raw_risk_score")
        adj_score_val = final.get("risk_score_adjusted") or result.get("risk_score") or score
        multiplier = result.get("exposure_multiplier", 1.0)

        exp_color = {
            "Critical": "#f85149", "High": "#f0883e",
            "Moderate": "#d29922", "Low": "#3fb950",
            "Minimal": "#8b949e",  "Unknown": "#8b949e",
        }.get(exposure_level, "#8b949e")

        deps = "".join(f"<li>{_e(d)}</li>" for d in profile.get("key_dependencies", []))
        mits = "".join(f"<li>{_e(m)}</li>" for m in profile.get("mitigation_on_file", []))
        score_line = (
            f"<br><span style='color:#64748b;font-size:0.82rem;'>"
            f"Macro risk score: <strong>{raw_score_val:.0f}</strong> × "
            f"exposure {multiplier:.2f} = "
            f"<strong style='color:{exp_color};'>{adj_score_val:.0f}</strong></span>"
            if raw_score_val is not None else ""
        )

        no_company_note = _e(profile.get("no_company_note", ""))
        summary_text = _e(result.get("exposure_summary") or profile.get("exposure_reasoning", "—"))
        exp_type = _e(profile.get("exposure_type", "unknown"))

        note_html = (
            "<p style=\"color:#64748b;font-size:0.85rem;font-style:italic;margin-top:0.5rem;\">"
            + no_company_note + "</p>"
        ) if no_company_note else ""

        st.markdown(f"""
        <div style="background:#ffffff;border:1px solid {exp_color}55;border-left:4px solid {exp_color};
                    border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:1.2rem;
                    box-shadow:0 1px 4px rgba(0,0,0,0.06);">
            <span style="color:#64748b;font-size:0.75rem;text-transform:uppercase;letter-spacing:.07em;font-weight:600;">
                Company Exposure
            </span>
            <div style="color:{exp_color};font-size:1.4rem;font-weight:700;line-height:1.2;margin-top:0.2rem;">
                {_e(exposure_level)}
                <span style="color:#64748b;font-size:0.85rem;font-weight:400;">&nbsp;({exp_type})</span>
            </div>
            {score_line}
            <p style="color:#374151;font-size:0.9rem;margin:0.8rem 0 0 0;line-height:1.6;">{summary_text}</p>
            {note_html}
        </div>
        """, unsafe_allow_html=True)

        key_deps = profile.get("key_dependencies") or []
        key_mits = profile.get("mitigation_on_file") or []
        if key_deps or key_mits:
            dep_col, mit_col = st.columns(2)
            with dep_col:
                if key_deps:
                    st.markdown("**Key Dependencies**")
                    for d in key_deps:
                        st.markdown(f"- {d}")
            with mit_col:
                if key_mits:
                    st.markdown("**Mitigations on File**")
                    for m in key_mits:
                        st.markdown(f"- {m}")

# ── ANALYST REPORTS ───────────────────────────────────────────────────────────
with tab_analysts:
    st.caption("Each analyst approaches the same risk from a different lens. The Judge synthesises their debate into the verdict above.")
    sub_bear, sub_bull, sub_geo = st.tabs(["Bear", "Bull", "Geopolitical"])
    with sub_bear:
        st.markdown(result.get("bear_analysis") or "_No output_")
    with sub_bull:
        st.markdown(result.get("bull_analysis") or "_No output_")
    with sub_geo:
        st.markdown(result.get("geopolitical_analysis") or "_No output_")

# ── SOURCES ───────────────────────────────────────────────────────────────────
with tab_sources:
    from collections import defaultdict
    docs = result.get("retrieved_docs") or []
    if not docs:
        st.info("No source documents recorded for this run.")
    else:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for d in docs:
            prefix = d.get("source", "Unknown").split("/")[0]
            grouped[prefix].append(d)

        cols = st.columns(len(grouped) or 1)
        for col, (src_type, src_docs) in zip(cols, grouped.items()):
            col.metric(src_type, f"{len(src_docs)} docs")

        st.markdown("<br>", unsafe_allow_html=True)
        for i, doc in enumerate(docs, 1):
            src = doc.get("source", "Unknown")
            url = doc.get("url", "")
            snippet = (doc.get("text") or "")[:300].replace("\n", " ")
            badge_html = source_badge(src)
            url_part = f"  —  [{url[:60]}]({url})" if url else ""
            header = f"**{i}. {src}**{url_part}"
            with st.expander(header, expanded=False):
                st.markdown(
                    f'<div class="src-row">{badge_html}</div>',
                    unsafe_allow_html=True,
                )
                st.caption(snippet + ("…" if len(doc.get("text", "")) > 300 else ""))
