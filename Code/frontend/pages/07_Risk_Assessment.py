import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

import streamlit as st
import pandas as pd
from tara.risk_engine import assess_risks
from tara.threat_analysis import generate_threats
from tara.asset_analysis import analyze_assets
from tara.attack_surface import analyze_attack_surfaces
from frontend.components.charts import create_risk_heatmap
from frontend.components.review_controls import render_review_controls
from frontend.init_state import ensure_session_state, render_sidebar

settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
render_sidebar()

st.title("Deterministic Risk Assessment")
st.markdown(r"Calculate risk scores using deterministic arithmetic ($\text{Risk Score} = \text{Impact Score} \times \text{Feasibility Score}$) to prevent numeric hallucinations.")
st.caption("⚠️ Risk thresholds are project-defined for this demonstration (Score ≥9 → Critical, ≥6 → High, ≥3 → Medium, <3 → Low). These are **not** official ISO/SAE 21434 impact classifications.")

if st.button("Assess Risks", type="primary"):
    try:
        with st.spinner("Assessing qualitative impact and computing deterministic risk scores..."):
            if 'threats' not in st.session_state:
                if 'assets' not in st.session_state:
                    st.session_state.assets = analyze_assets(retriever, llm_client)
                if 'attack_surfaces' not in st.session_state:
                    st.session_state.attack_surfaces = analyze_attack_surfaces(retriever, llm_client, st.session_state.assets)
                st.session_state.threats = generate_threats(retriever, llm_client, st.session_state.assets, st.session_state.attack_surfaces)
                
            risks = assess_risks(st.session_state.threats, retriever, llm_client)
            st.session_state.risks = risks
            from backend.database.connection import log_audit_event
            log_audit_event(
                action="risk_assessment",
                user="security_engineer",
                details=f"Evaluated {len(risks)} risk items. Mode: {llm_client.mode}"
            )
            if getattr(llm_client, "is_fallback_active", False) or getattr(llm_client, "is_demo", False):
                reason = getattr(llm_client, "last_fallback_reason", "")
                reason_txt = f" ({reason})" if reason else ""
                st.warning(f"⚠️ **DEMO MODE — PREDEFINED DATA ACTIVE**{reason_txt}: Deterministic scoring applied to demonstration qualitative inputs.")
            else:
                st.success(f"Risk assessment complete! Evaluated {len(risks)} risk items.")
    except Exception as e:
        st.error(f"Error assessing risks: {e}")

if 'risks' in st.session_state and st.session_state.risks:
    if getattr(llm_client, "is_fallback_active", False) or getattr(llm_client, "is_demo", False):
        st.info("ℹ️ **Provenance:** Qualitative ratings were derived from offline demonstration data. Risk scores were computed via deterministic arithmetic.")
    st.subheader("Risk Matrix Heatmap")
    try:
        heatmap = create_risk_heatmap(st.session_state.risks)
        st.plotly_chart(heatmap, use_container_width=True)
    except Exception as e:
        st.info("Risk matrix heatmap rendering unavailable.")
        
    st.subheader("Evaluated Risk Rankings")
    data = []
    for r in st.session_state.risks:
        data.append({
            "Threat": r.threat,
            "Target Asset": r.asset,
            "Impact Score": r.impact_score,
            "Feasibility": r.feasibility_score,
            "Risk Score": r.risk_score,
            "Risk Level": r.risk_level
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values(by="Risk Score", ascending=False)
    st.dataframe(df, use_container_width=True)
    
    st.markdown("### Risk Scoring Rationale & Review")
    for i, r in enumerate(st.session_state.risks):
        with st.expander(f"Risk [{i+1}]: {r.threat} — Level: {r.risk_level} (Score: {r.risk_score})"):
            st.write(f"**Target Asset:** {r.asset}")
            st.write(f"**Impact Dimension Score:** {r.impact_score} (Max of Safety, Financial, Privacy, Operational)")
            st.write(f"**Attack Feasibility Score:** {r.feasibility_score}")
            st.write(f"**Scoring Formula Rationale:** {r.scoring_rationale}")
            new_status = render_review_controls(f"risk_{i}", r.review_status)
            r.review_status = new_status
elif 'risks' not in st.session_state:
    st.info("Click **'Assess Risks'** above to compute deterministic risk scores for candidate threats.")
