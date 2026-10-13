import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

import streamlit as st
from tara.threat_analysis import generate_threats
from tara.asset_analysis import analyze_assets
from tara.attack_surface import analyze_attack_surfaces
from frontend.components.citations import render_citations
from frontend.components.review_controls import render_review_controls
from frontend.init_state import ensure_session_state, render_sidebar

settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
render_sidebar()

st.title("STRIDE Threat Scenario Generation")
st.caption("ℹ️ **Analysis Scope:** Generates prioritized candidate threat scenarios for qualified cybersecurity engineering review. This is an engineering aid and not an exhaustive or fully certified threat assessment.")

if 'assets' not in st.session_state:
    st.info("💡 **Recommended workflow:** Execute **04 Asset Analysis** and **05 Attack Surface** first. If not yet executed, they will be synthesized automatically below.")

if st.button("Generate Threats", type="primary"):
    try:
        status_box = st.status("Analyzing STRIDE threat scenarios...", expanded=True)
        with status_box:
            if 'assets' not in st.session_state or not st.session_state.assets:
                st.write("Step 1/3: Analyzing architecture assets...")
                st.session_state.assets = analyze_assets(retriever, llm_client)
            else:
                st.write("Step 1/3: Using existing session assets...")

            if 'attack_surfaces' not in st.session_state or not st.session_state.attack_surfaces:
                st.write("Step 2/3: Identifying attack surfaces...")
                st.session_state.attack_surfaces = analyze_attack_surfaces(retriever, llm_client, st.session_state.assets)
            else:
                st.write("Step 2/3: Using existing session attack surfaces...")

            st.write("Step 3/3: Synthesizing STRIDE threat candidates and grounding citations...")
            from tara.threat_analysis import generate_threats_with_rejects
            threats, rejected = generate_threats_with_rejects(
                retriever, llm_client, st.session_state.assets, st.session_state.attack_surfaces, max_candidates=5
            )
            st.session_state.threats = threats
            st.session_state.rejected_threats = rejected

            from backend.database.connection import log_audit_event
            log_audit_event(
                action="threat_generation",
                user="security_engineer",
                details=f"Generated {len(threats)} valid candidates, {len(rejected)} rejected. Mode: {llm_client.mode}"
            )
            status_box.update(label=f"Threat analysis complete! ({len(threats)} candidate scenarios)", state="complete", expanded=False)
            if getattr(llm_client, "is_fallback_active", False) or getattr(llm_client, "is_demo", False):
                reason = getattr(llm_client, "last_fallback_reason", "")
                reason_txt = f" ({reason})" if reason else ""
                st.warning(f"⚠️ **DEMO MODE — PREDEFINED DATA ACTIVE**{reason_txt}: Showing deterministic demonstration threats.")
            else:
                st.success(f"Threat analysis complete! Synthesized {len(threats)} candidate scenarios via live LLM.")
    except Exception as e:
        st.error(f"Error generating threats: {e}")

if 'threats' in st.session_state and st.session_state.threats:
    if getattr(llm_client, "is_fallback_active", False) or getattr(llm_client, "is_demo", False):
        st.info("ℹ️ **Provenance:** Results below are deterministic demonstration candidates, not extracted by live LLM.")
    st.subheader(f"Generated Threats ({len(st.session_state.threats)})")
    assets_list = sorted(list(set([t.asset for t in st.session_state.threats])))
    filter_asset = st.selectbox("Filter by Asset", ["All"] + assets_list)
    
    for i, t in enumerate(st.session_state.threats):
        if filter_asset != "All" and t.asset != filter_asset:
            continue
            
        with st.expander(f"Threat [{i+1}]: {t.threat} (Target: {t.asset})", expanded=(i == 0)):
            st.write(f"**Asset:** {t.asset} | **Attack Surface:** {t.attack_surface}")
            st.write(f"**Description:** {t.threat_description}")
            st.write(f"**Potential Impact:** {t.potential_impact}")
            st.write(f"**Preconditions:** {t.preconditions}")
            st.write(f"**Confidence:** {t.confidence}")
            
            if not t.evidence or "Hypothesis" in t.confidence:
                st.warning("⚠️ **Unverified Hypothesis:** No supporting citations were found in the knowledge base. This scenario is labeled as a hypothesis and requires direct engineering evidence before verification.")
            else:
                st.markdown("**Supporting Knowledge-Base Evidence:**")
            
            render_citations(t.evidence)
            new_status = render_review_controls(f"threat_{i}", t.review_status)
            t.review_status = new_status

    if 'rejected_threats' in st.session_state and st.session_state.rejected_threats:
        with st.expander(f"⚠️ Excluded Candidates ({len(st.session_state.rejected_threats)}) — Structural Validation Failures"):
            st.caption("The following candidate items generated by the model were excluded from the analysis pipeline because they failed required field or technical definition validation:")
            for r in st.session_state.rejected_threats:
                st.markdown(f"- **{r.threat_id}:** '{r.threat}' on asset '{r.asset}' — *Reason:* {r.rejection_reason}")
elif 'threats' not in st.session_state:
    st.info("Click **'Generate Threats'** above to synthesize candidate threat scenarios.")
