import logging
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import streamlit as st
from ui.theme import apply_theme
from ui.sidebar import render_sidebar

logging.basicConfig(level=logging.WARNING, format="%(name)s %(levelname)s: %(message)s")
for _ns in ("agents", "tools"):
    logging.getLogger(_ns).setLevel(logging.INFO)

st.set_page_config(
    page_title="Supply Chain Risk Monitor",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme("""
    .hero {
        background:
            linear-gradient(135deg, rgba(15,36,68,0.87) 0%, rgba(26,82,118,0.82) 100%),
            url('https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=1400&q=80') center/cover no-repeat;
        border-radius: 16px; padding: 3rem 2.5rem;
        margin: 1rem 0 2rem 0; text-align: center;
    }
    .hero h1 { color: #fff; font-size: 2.6rem; font-weight: 800; margin-bottom: 0.5rem; letter-spacing: -0.5px; }
    .hero p  { color: #a8c4e0; font-size: 1.05rem; margin: 0; }

    .card-grid { display: flex; gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap; }
    .home-card {
        flex: 1; min-width: 180px; background: #fff;
        border: 1px solid #e2e8f0; border-radius: 12px;
        padding: 1.4rem 1.2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s, transform 0.2s;
    }
    .home-card:hover { box-shadow: 0 4px 12px rgba(15,36,68,0.12); transform: translateY(-2px); }
    .home-card h3 { color: #0f2444; font-size: 0.95rem; font-weight: 700; margin: 0 0 0.35rem 0; }
    .home-card p  { color: #64748b; font-size: 0.82rem; margin: 0; line-height: 1.5; }

    .badge-row { display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; margin-top: 1.5rem; }
    .tech-badge {
        background: #e8f0f9; border: 1px solid #c8daf0;
        border-radius: 20px; padding: 0.25rem 0.9rem;
        color: #1a3a5c; font-size: 0.78rem; font-weight: 500;
    }
""")

render_sidebar()

st.markdown("""
<div class="hero">
    <h1>Supply Chain Risk Monitor</h1>
    <p>Multi-agent LangGraph pipeline &nbsp;·&nbsp; GPT-4o &nbsp;·&nbsp; Pinecone RAG &nbsp;·&nbsp; Real-time data</p>
</div>

<div class="card-grid">
    <div class="home-card">
        <h3>Search</h3>
        <p>Pick a scenario or build a custom query. The 7-agent pipeline runs automatically.</p>
    </div>
    <div class="home-card">
        <h3>Exposure</h3>
        <p>Company-specific exposure assessment — how directly are you affected?</p>
    </div>
    <div class="home-card">
        <h3>Results</h3>
        <p>Risk score, analyst debate, judge verdict, and recommended actions.</p>
    </div>
    <div class="home-card">
        <h3>GuardRail</h3>
        <p>Trust scores, hallucination flags, and confidence bands per agent.</p>
    </div>
</div>

<div class="badge-row">
    <span class="tech-badge">GPT-4o</span>
    <span class="tech-badge">LangGraph</span>
    <span class="tech-badge">Pinecone RAG</span>
    <span class="tech-badge">SEC EDGAR</span>
    <span class="tech-badge">NewsAPI</span>
    <span class="tech-badge">BeautifulSoup</span>
    <span class="tech-badge">RSS Feeds</span>
    <span class="tech-badge">PostgreSQL</span>
    <span class="tech-badge">GCP Cloud Run</span>
</div>
""", unsafe_allow_html=True)
