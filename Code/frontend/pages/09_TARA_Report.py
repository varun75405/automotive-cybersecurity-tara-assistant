import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

import streamlit as st
from datetime import datetime
from tara.report_generator import generate_tara_report
from frontend.init_state import ensure_session_state, render_sidebar

settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
render_sidebar()

st.title("Structured TARA Report Generation")
st.markdown("Compile all discovered assets, attack surfaces, STRIDE threats, deterministic risk scores, and recommended mitigations into a structured engineering report.")

has_upstream_data = any([
    st.session_state.get('assets'),
    st.session_state.get('threats'),
    st.session_state.get('risks'),
    st.session_state.get('mitigations')
])

if not has_upstream_data:
    st.info("ℹ️ No analysis findings currently in session. You can click 'Generate TARA Report' to see the empty session status report, or navigate to upstream pages (Asset, Attack Surface, Threat, Risk, Mitigation) first.")

if st.button("Generate TARA Report", type="primary"):
    report_content = generate_tara_report(st.session_state, execution_mode=llm_client.mode)
    st.session_state.report_content = report_content
    from backend.database.connection import log_audit_event
    log_audit_event(
        action="report_generation",
        user="security_engineer",
        details=f"Generated report (Length: {len(report_content)} chars). Mode: {llm_client.mode}"
    )
    if has_upstream_data:
        st.success("TARA report generated successfully from current session findings!")
    else:
        st.warning("⚠️ Generated report reflects an empty session. Upstream analysis has not yet been executed.")

if 'report_content' in st.session_state and st.session_state.report_content:
    if getattr(llm_client, "is_fallback_active", False) or getattr(llm_client, "is_demo", False):
        st.warning("⚠️ **DEMO MODE — PREDEFINED DATA ACTIVE**: This report incorporates demonstration findings generated in offline fallback mode, not live LLM responses.")
    st.subheader("Report Preview")
    st.markdown(st.session_state.report_content)
    
    st.download_button(
        label="📥 Download Report as Markdown (.md)",
        data=st.session_state.report_content,
        file_name=f"tara_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown"
    )
