"""Shared sidebar rendered on every page."""
from __future__ import annotations
import os
import html as _html
import streamlit as st


def _e(text: str) -> str:
    return _html.escape(str(text or ""))


def render_sidebar() -> None:
    """Inject the shared sidebar sections into st.sidebar."""
    with st.sidebar:
        # ── Brand header ──────────────────────────────────────────────────────
        st.markdown("""
        <div style="padding:1rem 0 0.5rem 0; border-bottom:1px solid rgba(255,255,255,0.12); margin-bottom:1rem;">
            <div style="font-size:1.25rem; font-weight:800; color:#ffffff; letter-spacing:-0.3px;">
                Supply Chain Risk
            </div>
            <div style="font-size:0.72rem; color:#a8c4e0; text-transform:uppercase;
                        letter-spacing:0.1em; margin-top:0.2rem;">
                Multi-Agent Risk Monitor
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Last run summary ──────────────────────────────────────────────────
        result = st.session_state.get("last_result")
        if result:
            score = result.get("risk_score") or 0
            label = (result.get("final_output") or {}).get("risk_label", "Unknown")
            query = result.get("query", "")
            company = result.get("company", "")
            region = result.get("region", "")

            score_color = (
                "#3fb950" if score < 21 else
                "#d29922" if score < 41 else
                "#f0883e" if score < 61 else
                "#f85149"
            )

            meta_parts = [p for p in [company, region] if p]
            meta_line = " · ".join(meta_parts)

            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.12);
                        border-radius:10px; padding:0.9rem 1rem; margin-bottom:1rem;">
                <div style="font-size:0.68rem; text-transform:uppercase; letter-spacing:0.09em;
                            color:#a8c4e0; font-weight:600; margin-bottom:0.5rem;">Last Run</div>
                <div style="display:flex; align-items:baseline; gap:0.5rem;">
                    <span style="font-size:2rem; font-weight:800; color:{score_color}; line-height:1;">{score:.0f}</span>
                    <span style="font-size:0.85rem; color:{score_color}; font-weight:600;">{_e(label)}</span>
                </div>
                <div style="font-size:0.78rem; color:#cbd5e1; margin-top:0.35rem;
                            white-space:nowrap; overflow:hidden; text-overflow:ellipsis;"
                     title="{_e(query)}">{_e(query[:48])}{'…' if len(query) > 48 else ''}</div>
                {f'<div style="font-size:0.72rem; color:#94a3b8; margin-top:0.2rem;">{_e(meta_line)}</div>' if meta_line else ''}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08);
                        border-radius:10px; padding:0.8rem 1rem; margin-bottom:1rem;
                        color:#64748b; font-size:0.8rem; font-style:italic;">
                No run yet — use Search to start.
            </div>
            """, unsafe_allow_html=True)

        # ── Risk legend ───────────────────────────────────────────────────────
        st.markdown("""
        <div style="margin-bottom:1rem;">
            <div style="font-size:0.68rem; text-transform:uppercase; letter-spacing:0.09em;
                        color:#a8c4e0; font-weight:600; margin-bottom:0.55rem;">Risk Legend</div>
            <div style="display:flex; flex-direction:column; gap:0.3rem;">
                <div style="display:flex; align-items:center; gap:0.55rem;">
                    <span style="width:10px;height:10px;border-radius:50%;background:#3fb950;flex-shrink:0;"></span>
                    <span style="font-size:0.8rem; color:#e2edf7;">Low</span>
                    <span style="font-size:0.75rem; color:#64748b; margin-left:auto;">0 – 20</span>
                </div>
                <div style="display:flex; align-items:center; gap:0.55rem;">
                    <span style="width:10px;height:10px;border-radius:50%;background:#d29922;flex-shrink:0;"></span>
                    <span style="font-size:0.8rem; color:#e2edf7;">Moderate</span>
                    <span style="font-size:0.75rem; color:#64748b; margin-left:auto;">21 – 40</span>
                </div>
                <div style="display:flex; align-items:center; gap:0.55rem;">
                    <span style="width:10px;height:10px;border-radius:50%;background:#f0883e;flex-shrink:0;"></span>
                    <span style="font-size:0.8rem; color:#e2edf7;">High</span>
                    <span style="font-size:0.75rem; color:#64748b; margin-left:auto;">41 – 60</span>
                </div>
                <div style="display:flex; align-items:center; gap:0.55rem;">
                    <span style="width:10px;height:10px;border-radius:50%;background:#f85149;flex-shrink:0;"></span>
                    <span style="font-size:0.8rem; color:#e2edf7;">Critical</span>
                    <span style="font-size:0.75rem; color:#64748b; margin-left:auto;">61 – 100</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Data sources status ───────────────────────────────────────────────
        sources = [
            ("NewsAPI",   bool(os.getenv("NEWS_API_KEY"))),
            ("Pinecone",  bool(os.getenv("PINECONE_API_KEY"))),
            ("SEC EDGAR", True),   # no key needed
            ("RSS Feeds", True),   # always available
            ("PostgreSQL", bool(os.getenv("CLOUD_SQL_CONNECTION_NAME") or os.getenv("DATABASE_URL"))),
        ]

        rows = ""
        for name, ok in sources:
            dot_color = "#3fb950" if ok else "#f85149"
            status_label = "connected" if ok else "not configured"
            rows += (
                f'<div style="display:flex;align-items:center;gap:0.55rem;margin-bottom:0.28rem;">'
                f'<span style="width:7px;height:7px;border-radius:50%;background:{dot_color};flex-shrink:0;"></span>'
                f'<span style="font-size:0.8rem;color:#e2edf7;">{name}</span>'
                f'<span style="font-size:0.7rem;color:#64748b;margin-left:auto;">{status_label}</span>'
                f'</div>'
            )

        st.markdown(f"""
        <div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:0.9rem;">
            <div style="font-size:0.68rem; text-transform:uppercase; letter-spacing:0.09em;
                        color:#a8c4e0; font-weight:600; margin-bottom:0.55rem;">Data Sources</div>
            {rows}
        </div>
        """, unsafe_allow_html=True)
