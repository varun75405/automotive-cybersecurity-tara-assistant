import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

import streamlit as st
import graphviz
from tara.trust_boundaries import identify_trust_boundaries
from frontend.init_state import ensure_session_state, render_sidebar

settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
render_sidebar()

st.title("Vehicle Architecture & Trust Boundaries")
st.markdown("Analyze vehicle E/E architecture, electronic control unit (ECU) topologies, and cross-domain security boundaries.")

if st.button("Run Architecture Analysis", type="primary"):
    try:
        with st.spinner("Retrieving architecture context and extracting boundaries..."):
            info = retriever.retrieve('vehicle architecture ECUs communication', 5, None)
            st.subheader("Retrieved Architecture Context")
            for c in info:
                with st.expander(f"{c.document_name} — {c.section or 'General'}"):
                    st.write(c.chunk_text)
                    
            st.subheader("E/E Architecture Network Topology")
            try:
                dot = graphviz.Digraph()
                dot.attr(rankdir='LR')
                dot.node('CGW', 'Central Gateway (CGW)', shape='box', style='filled', fillcolor='#E2E8F0')
                dot.node('TCU', 'Telematics (TCU)', shape='ellipse')
                dot.node('IVI', 'Infotainment (IVI)', shape='ellipse')
                dot.node('ADAS', 'ADAS ECU', shape='ellipse')
                dot.node('PT', 'Powertrain ECU', shape='ellipse')
                dot.node('BCM', 'Body Control (BCM)', shape='ellipse')
                
                dot.edge('TCU', 'CGW', label='Ethernet')
                dot.edge('IVI', 'CGW', label='Ethernet')
                dot.edge('ADAS', 'CGW', label='CAN-FD')
                dot.edge('PT', 'CGW', label='High-Speed CAN')
                dot.edge('BCM', 'CGW', label='Low-Speed CAN / LIN')
                
                st.graphviz_chart(dot)
            except Exception as g_err:
                st.info("E/E Topology: [Telematics / IVI] --Ethernet--> [Central Gateway] --CAN-FD--> [ADAS / Powertrain / BCM]")

            st.subheader("Discovered Trust Boundaries")
            boundaries = identify_trust_boundaries(retriever, llm_client)
            for b in boundaries:
                with st.expander(f"Boundary: {b.name}"):
                    st.write(f"**Rationale:** {b.rationale}")
                    st.write(f"**Connected Components:** {b.connected_components}")
                    if hasattr(b, 'confidence') and b.confidence:
                        st.caption(f"Confidence: {b.confidence}")
            
            st.session_state.trust_boundaries = boundaries
            from backend.database.connection import log_audit_event
            log_audit_event(
                action="architecture_analysis",
                user="security_engineer",
                details=f"Retrieved {len(info)} architecture chunks. Identified {len(boundaries)} trust boundaries. Mode: {llm_client.mode}"
            )
            if getattr(llm_client, "is_fallback_active", False) or getattr(llm_client, "is_demo", False):
                reason = getattr(llm_client, "last_fallback_reason", "")
                reason_txt = f" ({reason})" if reason else ""
                st.warning(f"⚠️ **DEMO MODE — PREDEFINED DATA ACTIVE**{reason_txt}: Showing deterministic demonstration trust boundaries.")
            else:
                st.success("Architecture analysis complete.")
            
    except Exception as e:
        st.error(f"Error analyzing architecture: {e}")
