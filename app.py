import streamlit as st

st.set_page_config(
    page_title="Supply Chain Risk Monitor",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* Global */
    [data-testid="stAppViewContainer"] { background: #0f1117; }
    [data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }
    [data-testid="stSidebarNav"] a { color: #c9d1d9 !important; }

    /* Hide default header */
    header[data-testid="stHeader"] { background: transparent; }

    /* Hero */
    .hero { padding: 3rem 0 2rem 0; text-align: center; }
    .hero h1 {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #58a6ff 0%, #f78166 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .hero p { color: #8b949e; font-size: 1.1rem; margin-top: 0; }

    /* Feature cards */
    .card-grid { display: flex; gap: 1.2rem; margin: 2rem 0; flex-wrap: wrap; }
    .card {
        flex: 1;
        min-width: 200px;
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.4rem 1.2rem;
        transition: border-color 0.2s;
    }
    .card:hover { border-color: #58a6ff; }
    .card .icon { font-size: 1.8rem; margin-bottom: 0.6rem; }
    .card h3 { color: #e6edf3; font-size: 1rem; margin: 0 0 0.4rem 0; }
    .card p { color: #8b949e; font-size: 0.85rem; margin: 0; line-height: 1.5; }

    /* Badge row */
    .badge-row { display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; margin-top: 1.5rem; }
    .badge {
        background: #21262d;
        border: 1px solid #30363d;
        border-radius: 20px;
        padding: 0.25rem 0.8rem;
        color: #8b949e;
        font-size: 0.78rem;
    }
</style>

<div class="hero">
    <h1>⚠️ Supply Chain Risk Monitor</h1>
    <p>Multi-agent LangGraph pipeline · GPT-4o · Pinecone RAG · GCP</p>
</div>

<div class="card-grid">
    <div class="card">
        <div class="icon">🔍</div>
        <h3>Search</h3>
        <p>Describe a supply chain scenario and run the 6-agent analysis pipeline.</p>
    </div>
    <div class="card">
        <div class="icon">📊</div>
        <h3>Results</h3>
        <p>View risk scores, analyst debate, judge verdict, and recommended actions.</p>
    </div>
    <div class="card">
        <div class="icon">🛡️</div>
        <h3>GuardRail</h3>
        <p>Inspect trust scores, hallucination flags, and confidence bands per agent.</p>
    </div>
    <div class="card">
        <div class="icon">⚙️</div>
        <h3>Pipeline</h3>
        <p>Retriever → Bear · Bull · Geo analysts → Judge → Guardrail meta-agent.</p>
    </div>
</div>

<div class="badge-row">
    <span class="badge">GPT-4o</span>
    <span class="badge">LangGraph</span>
    <span class="badge">Pinecone RAG</span>
    <span class="badge">SEC EDGAR</span>
    <span class="badge">NewsAPI</span>
    <span class="badge">RSS Feeds</span>
    <span class="badge">PostgreSQL</span>
    <span class="badge">GCP Cloud Run</span>
</div>
""", unsafe_allow_html=True)
