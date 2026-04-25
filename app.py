import logging
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import streamlit as st

logging.basicConfig(level=logging.WARNING, format="%(name)s %(levelname)s: %(message)s")
# Show INFO from our pipeline modules without drowning in third-party noise
for _ns in ("agents", "tools"):
    logging.getLogger(_ns).setLevel(logging.INFO)

st.set_page_config(
    page_title="Supply Chain Risk Monitor",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    [data-testid="stAppViewContainer"] { background: #f0f4f8; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2444 0%, #1a3a5c 100%);
        border-right: none;
    }
    [data-testid="stSidebar"] * { color: #e2edf7 !important; }
    [data-testid="stSidebarNav"] a { color: #a8c4e0 !important; font-size: 0.9rem; }
    [data-testid="stSidebarNav"] a:hover { color: #ffffff !important; }
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] { background: rgba(255,255,255,0.08) !important; border-color: rgba(255,255,255,0.2) !important; }
    [data-testid="stSidebar"] button { background: rgba(255,255,255,0.12) !important; border-color: rgba(255,255,255,0.25) !important; color: #fff !important; }
    header[data-testid="stHeader"] { background: transparent; }

    .hero {
        background: linear-gradient(135deg, #0f2444 0%, #1a5276 100%);
        border-radius: 16px;
        padding: 3rem 2.5rem;
        margin: 1rem 0 2rem 0;
        text-align: center;
    }
    .hero h1 { color: #ffffff; font-size: 2.6rem; font-weight: 800; margin-bottom: 0.5rem; letter-spacing: -0.5px; }
    .hero p { color: #a8c4e0; font-size: 1.05rem; margin: 0; }

    .card-grid { display: flex; gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap; }
    .card {
        flex: 1; min-width: 180px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.4rem 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s, transform 0.2s;
    }
    .card:hover { box-shadow: 0 4px 12px rgba(15,36,68,0.12); transform: translateY(-2px); }
    .card h3 { color: #0f2444; font-size: 0.95rem; font-weight: 700; margin: 0 0 0.35rem 0; }
    .card p { color: #64748b; font-size: 0.82rem; margin: 0; line-height: 1.5; }

    .badge-row { display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; margin-top: 1.5rem; }
    .badge {
        background: #e8f0f9;
        border: 1px solid #c8daf0;
        border-radius: 20px;
        padding: 0.25rem 0.9rem;
        color: #1a3a5c;
        font-size: 0.78rem;
        font-weight: 500;
    }
</style>

<div class="hero">
    <h1>Supply Chain Risk Monitor</h1>
    <p>Multi-agent LangGraph pipeline · GPT-4o · Pinecone RAG · Real-time data</p>
</div>

<div class="card-grid">
    <div class="card">
        <h3>Search</h3>
        <p>Pick a scenario or build a custom query. 7-agent pipeline runs automatically.</p>
    </div>
    <div class="card">
        <h3>Exposure</h3>
        <p>Company-specific exposure assessment — how directly are YOU affected?</p>
    </div>
    <div class="card">
        <h3>Results</h3>
        <p>Risk score, analyst debate, judge verdict, and recommended actions.</p>
    </div>
    <div class="card">
        <h3>GuardRail</h3>
        <p>Trust scores, hallucination flags, and confidence bands per agent.</p>
    </div>
</div>

<div class="badge-row">
    <span class="badge">GPT-4o</span>
    <span class="badge">LangGraph</span>
    <span class="badge">Pinecone RAG</span>
    <span class="badge">SEC EDGAR</span>
    <span class="badge">NewsAPI</span>
    <span class="badge">BeautifulSoup</span>
    <span class="badge">RSS Feeds</span>
    <span class="badge">PostgreSQL</span>
    <span class="badge">GCP Cloud Run</span>
</div>
""", unsafe_allow_html=True)
