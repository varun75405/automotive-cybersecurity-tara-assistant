import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

import streamlit as st
from tara.asset_analysis import analyze_assets
from frontend.components.citations import render_citations
from frontend.components.review_controls import render_review_controls
from frontend.init_state import ensure_session_state, render_sidebar

settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
render_sidebar()

st.title("Asset Identification & CIA/A Security Properties")
st.markdown("Extract automotive assets (ECUs, gateways, buses, sensors) and identify Confidentiality, Integrity, Availability, and Authenticity (CIA/A) security properties.")

if st.button("Run Asset Analysis", type="primary"):
    doc_count = vector_store.get_document_count()
    if doc_count == 0:
        st.error(
            "⚠️ **Knowledge Base is empty.** Please upload architecture documents on the "
            "[Document Upload](file:///C:/TARA/frontend/pages/01_Document_Upload.py) page before running Asset Analysis."
        )
    else:
        try:
            with st.status("Analyzing architecture documents and extracting assets...", expanded=True) as status:
                st.write("🔍 Retrieving architecture chunks from knowledge base...")
                assets = analyze_assets(retriever, llm_client)
                st.write(f"✅ Processed assets: {len(assets)} identified.")
                status.update(label="Asset Analysis Complete", state="complete", expanded=False)

            st.session_state.assets = assets
            from backend.database.connection import log_audit_event
            log_audit_event(
                action="asset_analysis",
                user="security_engineer",
                details=f"Extracted {len(assets)} assets. Mode: {llm_client.mode}"
            )
            if len(assets) == 0:
                st.warning("⚠️ Asset analysis finished, but 0 assets were identified from the retrieved documents.")
            elif getattr(llm_client, "is_fallback_active", False) or getattr(llm_client, "is_demo", False):
                reason = getattr(llm_client, "last_fallback_reason", "")
                reason_txt = f" ({reason})" if reason else ""
                st.warning(f"⚠️ **DEMO MODE — PREDEFINED DATA ACTIVE**{reason_txt}: Showing deterministic demonstration assets for engineering review.")
            else:
                st.success(f"Asset analysis complete! Discovered {len(assets)} candidate assets via live LLM.")
        except Exception as e:
            st.error(f"❌ **Asset analysis failed:** {e}")

if 'assets' in st.session_state and st.session_state.assets:
    if getattr(llm_client, "is_fallback_active", False) or getattr(llm_client, "is_demo", False):
        st.info("ℹ️ **Provenance:** Results below are deterministic demonstration candidates, not extracted by live LLM.")
    st.subheader(f"Discovered Assets ({len(st.session_state.assets)})")
    for i, asset in enumerate(st.session_state.assets):
        st.markdown(f"### {asset.name} ({asset.asset_type})")
        st.write(f"**Description:** {asset.description}")
        if asset.related_ecu:
            st.write(f"**Related ECU:** {asset.related_ecu}")
        if asset.related_interface:
            st.write(f"**Related Interface:** {asset.related_interface}")
        st.write(f"**Security Properties:** {asset.security_properties}")
        
        render_citations(asset.evidence)
        
        new_status = render_review_controls(f"asset_{i}", asset.review_status, item_type="asset")
        asset.review_status = new_status
        
        st.divider()
elif 'assets' not in st.session_state:
    st.info("Click **'Run Asset Analysis'** above to extract assets from indexed architecture documents.")
