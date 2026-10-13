import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

import streamlit as st
import pandas as pd
from tara.mitigation import recommend_mitigations
from tara.threat_analysis import generate_threats
from tara.asset_analysis import analyze_assets
from tara.attack_surface import analyze_attack_surfaces
from tara.risk_engine import assess_risks
from frontend.components.citations import render_citations
from frontend.components.review_controls import render_review_controls
from frontend.init_state import ensure_session_state, render_sidebar

settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
render_sidebar()

st.title("Defensive Mitigation Recommendations")
st.markdown("Recommend automotive cybersecurity controls (AUTOSAR SecOC, TLS 1.3, Secure Boot, HSM, Gateway Filtering) grounded in defensive engineering libraries.")

if st.button("Recommend Mitigations", type="primary"):
    try:
        with st.spinner("Matching threats to defensive controls and retrieving mitigation evidence..."):
            if 'threats' not in st.session_state:
                if 'assets' not in st.session_state:
                    st.session_state.assets = analyze_assets(retriever, llm_client)
                if 'attack_surfaces' not in st.session_state:
                    st.session_state.attack_surfaces = analyze_attack_surfaces(retriever, llm_client, st.session_state.assets)
                st.session_state.threats = generate_threats(retriever, llm_client, st.session_state.assets, st.session_state.attack_surfaces)
            if 'risks' not in st.session_state:
                st.session_state.risks = assess_risks(st.session_state.threats, retriever, llm_client)
                
            mitigations = recommend_mitigations(st.session_state.threats, st.session_state.risks, retriever, llm_client)
            st.session_state.mitigations = mitigations
            from backend.database.connection import log_audit_event
            log_audit_event(
                action="mitigation_recommendation",
                user="security_engineer",
                details=f"Generated {len(mitigations)} defensive controls. Mode: {llm_client.mode}"
            )
            if getattr(llm_client, "is_fallback_active", False) or getattr(llm_client, "is_demo", False):
                reason = getattr(llm_client, "last_fallback_reason", "")
                reason_txt = f" ({reason})" if reason else ""
                st.warning(f"⚠️ **DEMO MODE — PREDEFINED DATA ACTIVE**{reason_txt}: Showing deterministic demonstration mitigations.")
            else:
                st.success(f"Mitigation recommendations complete! Generated {len(mitigations)} defensive controls.")
    except Exception as e:
        st.error(f"Error recommending mitigations: {e}")

if 'mitigations' in st.session_state and st.session_state.mitigations:
    if getattr(llm_client, "is_fallback_active", False) or getattr(llm_client, "is_demo", False):
        st.info("ℹ️ **Provenance:** Results below are deterministic demonstration candidates, not extracted by live LLM.")
    st.subheader(f"Recommended Defensive Controls ({len(st.session_state.mitigations)})")
    
    data = []
    for m in st.session_state.mitigations:
        data.append({
            "Target Threat": m.threat,
            "Recommended Control": m.recommended_control,
            "Control Category": m.control_category
        })
    st.dataframe(pd.DataFrame(data), use_container_width=True)
    
    st.markdown("### Mitigation Details & Evidence")
    for i, m in enumerate(st.session_state.mitigations):
        with st.expander(f"Control [{i+1}]: {m.recommended_control} (for {m.threat})"):
            st.write(f"**Target Threat:** {m.threat}")
            st.write(f"**Control Category:** {m.control_category}")
            st.write(f"**Technical Description:** {m.description}")
            st.caption("ℹ️ *Candidate recommendation requiring cybersecurity engineering review — not an automatic compliance claim.*")
            if m.evidence:
                st.markdown("**Referenced Knowledge-Base Mitigation Guidance:**")
            render_citations(m.evidence)
            new_status = render_review_controls(f"mitigation_{i}", m.review_status)
            m.review_status = new_status
elif 'mitigations' not in st.session_state:
    st.info("Click **'Recommend Mitigations'** above to generate defensive controls for identified threats.")
