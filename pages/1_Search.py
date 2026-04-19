import streamlit as st
from agents.graph import run_pipeline
from tools.postgres_db import save_run, init_db

st.set_page_config(page_title="Search · Supply Chain Risk", layout="wide")
st.title("🔍 Risk Query")


@st.cache_resource
def _init_db_once():
    init_db()


_init_db_once()

with st.form("query_form"):
    query = st.text_area(
        "Describe the supply chain scenario",
        placeholder="e.g. semiconductor supply from Taiwan for consumer electronics",
        height=100,
    )
    col1, col2 = st.columns(2)
    company = col1.text_input("Company / Ticker (optional)", placeholder="e.g. AAPL")
    region = col2.text_input("Region (optional)", placeholder="e.g. Taiwan, Southeast Asia")
    submitted = st.form_submit_button("Run Analysis ▶", use_container_width=True)

if submitted and query.strip():
    with st.spinner("Running 6-agent pipeline — this takes ~30 seconds…"):
        try:
            result = run_pipeline(query=query, company=company, region=region)
            run_id = save_run(result)
            st.session_state["last_result"] = result
            st.session_state["last_run_id"] = run_id
            st.success(f"Analysis complete (run #{run_id}). View full results on the **Results** page.")
        except Exception as e:
            st.error(f"Pipeline error: {e}")
elif submitted:
    st.warning("Please enter a query.")
