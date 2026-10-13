import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import streamlit as st
from frontend.init_state import ensure_session_state, render_sidebar

st.set_page_config(page_title='Automotive TARA AI Assistant', layout='wide', page_icon='🔒')

# Ensure shared resources are cached and available
settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
render_sidebar()

st.title("Automotive Cybersecurity TARA Assistant")
st.markdown("AI-assisted Threat Analysis and Risk Assessment (TARA) platform informed by **ISO/SAE 21434** and **UNECE R155** concepts.")

st.subheader("System Status")
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.metric("Total Indexed Chunks", vector_store.get_document_count())
with col_s2:
    st.metric("LLM Provider Mode", llm_client.mode)
with col_s3:
    st.metric("Embedding Model", embedding_model.model_name.split('/')[-1])

st.markdown("---")

st.subheader("Quick Navigation")
st.markdown("Select a module below or use the sidebar navigation:")

col1, col2 = st.columns(2)
with col1:
    st.page_link("pages/01_Document_Upload.py", label="01. Document Upload & Knowledge Ingestion", icon="📁")
    st.page_link("pages/02_Knowledge_Base.py", label="02. Knowledge Base & Vector Inspector", icon="📚")
    st.page_link("pages/03_Architecture_Analysis.py", label="03. Vehicle Architecture Analysis", icon="🏗️")
    st.page_link("pages/04_Asset_Analysis.py", label="04. Asset Identification & CIA/A Properties", icon="🔍")
    st.page_link("pages/05_Attack_Surface.py", label="05. Attack Surface Analysis", icon="🎯")
    st.page_link("pages/06_Threat_Analysis.py", label="06. STRIDE Threat Scenario Generation", icon="⚠️")

with col2:
    st.page_link("pages/07_Risk_Assessment.py", label="07. Deterministic Risk Assessment", icon="📊")
    st.page_link("pages/08_Mitigations.py", label="08. Defensive Mitigation Mapping", icon="🛡️")
    st.page_link("pages/09_TARA_Report.py", label="09. Structured TARA Report Generation", icon="📑")
    st.page_link("pages/10_RAG_Assistant.py", label="10. Grounded Cybersecurity Chat Assistant", icon="💬")
    st.page_link("pages/11_Evaluation.py", label="11. Benchmark Evaluation Runner", icon="📈")
    st.page_link("pages/12_Audit_Review.py", label="12. SQLite Audit Trail & Review Analytics", icon="📋")

st.markdown("---")
st.info("💡 **Academic Prototype Advisory:** AI-generated findings, threat scenarios, risk ratings, mitigations, and requirements are advisory candidate suggestions requiring qualified human cybersecurity review.")
