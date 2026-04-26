"""Shared design system — one place for all CSS tokens, base styles, and components.

Import and call apply_theme() at the top of every page, passing page-specific CSS
as the optional extra_css argument.
"""
from __future__ import annotations
import streamlit as st

# ── Colour tokens ─────────────────────────────────────────────────────────────
NAVY_900 = "#0f2444"
NAVY_700 = "#1a3a5c"
NAVY_500 = "#1a5276"
SLATE_100 = "#f0f4f8"
SLATE_200 = "#e2e8f0"
SLATE_400 = "#94a3b8"
SLATE_600 = "#64748b"
WHITE    = "#ffffff"

# ── Shared CSS ────────────────────────────────────────────────────────────────
_BASE = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* App shell */
[data-testid="stAppViewContainer"] { background: #f0f4f8; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f2444 0%, #1a3a5c 100%);
    border-right: none;
}
[data-testid="stSidebar"] *         { color: #e2edf7 !important; }
[data-testid="stSidebarNav"] a      { color: #a8c4e0 !important; font-size: 0.9rem; }
[data-testid="stSidebarNav"] a:hover{ color: #fff !important; }
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(255,255,255,0.2) !important;
}
[data-testid="stSidebar"] button {
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(255,255,255,0.25) !important;
    color: #fff !important;
}
header[data-testid="stHeader"] { background: transparent; }

/* Page header (dark gradient banner with industry background) */
.page-header {
    background:
        linear-gradient(135deg, rgba(15,36,68,0.90) 0%, rgba(26,82,118,0.86) 100%),
        url('https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=1400&q=80') center/cover no-repeat;
    border-radius: 12px; padding: 1.8rem 2rem; margin-bottom: 1.5rem;
}
.page-header h1 { color: #fff; font-size: 1.8rem; font-weight: 800; margin: 0 0 0.2rem 0; }
.page-header p  { color: #a8c4e0; margin: 0; font-size: 0.88rem; }

/* White content card */
.card {
    background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 1.2rem; height: 100%;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.card h4 {
    color: #1a3a5c; font-size: 0.78rem; text-transform: uppercase;
    letter-spacing: 0.06em; margin: 0 0 0.8rem 0; font-weight: 700;
}
.card ul { margin: 0; padding-left: 1.2rem; color: #374151; font-size: 0.88rem; line-height: 1.9; }

/* Verdict / notes box (border-left accent) */
.verdict-box {
    background: #ffffff; border: 1px solid #e2e8f0;
    border-left: 4px solid #1a5276; border-radius: 8px;
    padding: 1.2rem 1.4rem; color: #374151;
    font-size: 0.93rem; line-height: 1.75; margin-bottom: 1.2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

/* Section micro-label */
.section-label {
    color: #1a3a5c; font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 0.08em; margin-bottom: 0.6rem; font-weight: 700;
}

/* Source type badges */
.src-badge {
    display: inline-block; padding: 0.15rem 0.55rem;
    border-radius: 10px; font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.02em; vertical-align: middle;
}
.src-edgar  { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
.src-news   { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
.src-rss    { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
.src-html   { background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe; }
.src-vector { background: #fdf4ff; color: #9333ea; border: 1px solid #e9d5ff; }
.src-other  { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }

/* Confidence badges */
.conf-badge {
    display: inline-block; padding: 0.25rem 0.8rem;
    border-radius: 12px; font-size: 0.75rem; font-weight: 600;
}
.conf-high   { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
.conf-medium { background: #fef9c3; color: #854d0e; border: 1px solid #fcd34d; }
.conf-low    { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }

/* Action badges */
.action-badge {
    display: inline-block; padding: 0.3rem 1rem;
    border-radius: 20px; font-size: 0.82rem; font-weight: 600; margin-top: 0.5rem;
}
.action-watch     { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
.action-monitor   { background: #fef9c3; color: #854d0e; border: 1px solid #fcd34d; }
.action-escalate  { background: #ffedd5; color: #c2410c; border: 1px solid #fdba74; }
.action-immediate { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }

/* Tabs */
[data-testid="stTabs"] button { color: #64748b !important; font-weight: 500; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #0f2444 !important; border-bottom-color: #1a5276 !important; font-weight: 700;
}

/* Expanders */
details { background: #fff; border: 1px solid #e2e8f0 !important; border-radius: 8px !important; }
summary { color: #0f2444 !important; font-weight: 500; }
"""


def apply_theme(extra_css: str = "") -> None:
    """Inject the shared design system, plus any page-specific CSS."""
    st.markdown(f"<style>{_BASE}{extra_css}</style>", unsafe_allow_html=True)


# ── Reusable component helpers ────────────────────────────────────────────────

def source_badge(source: str) -> str:
    """Return an HTML source-type badge for a doc source string."""
    s = source.upper()
    if "EDGAR"   in s: cls, label = "src-edgar",  "EDGAR"
    elif "NEWSAPI" in s: cls, label = "src-news",   "News"
    elif "RSS"    in s: cls, label = "src-rss",    "RSS"
    elif "HTML"   in s: cls, label = "src-html",   "Web"
    elif "PINECONE" in s: cls, label = "src-vector", "Vector"
    else:              cls, label = "src-other",  source.split("/")[0]
    return f'<span class="src-badge {cls}">{label}</span>'


def confidence_badge(level: str) -> str:
    """Return an HTML confidence badge (High / Medium / Low)."""
    cls = {"High": "conf-high", "Medium": "conf-medium", "Low": "conf-low"}.get(level, "conf-low")
    return f'<span class="conf-badge {cls}">{level} Confidence</span>'
