import streamlit as st

st.set_page_config(
    page_title="Supply Chain Risk Monitor",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Supply Chain Risk Monitor")
st.caption("6-agent LangGraph pipeline · GPT-4o · Pinecone RAG · GCP")

st.markdown(
    """
    Use the **Search** page to run a risk analysis query.
    View full results including analyst debate on the **Results** page.
    Monitor agent trust scores and guardrail flags on the **GuardRail** page.
    """
)
