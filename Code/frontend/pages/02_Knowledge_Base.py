import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

import streamlit as st
from frontend.init_state import ensure_session_state, render_sidebar

settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
render_sidebar()

st.title("Knowledge Base & Vector Store Inspector")
st.markdown("Inspect persistent vector collections in ChromaDB, check document chunk counts, and execute semantic queries.")

st.subheader("Collection Stats")
try:
    stats = vector_store.get_collection_stats()
    st.json(stats)
except Exception as e:
    st.error(f"Error getting stats: {e}")

st.metric("Total Indexed Chunks", vector_store.get_document_count())

if st.button("Clear Knowledge Base"):
    try:
        vector_store.delete_collection()
        st.success("Knowledge base cleared.")
        for key in ['assets', 'attack_surfaces', 'threats', 'rejected_threats', 'risks', 'mitigations', 'requirements']:
            if key in st.session_state:
                del st.session_state[key]
    except Exception as e:
        st.error(f"Error clearing knowledge base: {e}")

st.markdown("---")
st.subheader("Semantic Test Query")
query = st.text_input("Enter a test query (e.g., 'CAN-FD gateway filtering', 'UDS seed-key'):", key="kb_query")
if query:
    try:
        citations = retriever.retrieve(query, 5, None)
        if citations:
            for i, c in enumerate(citations):
                with st.expander(f"Result {i+1}: {c.document_name} (Relevance: {c.relevance_score:.3f})"):
                    if c.section:
                        st.caption(f"**Section:** {c.section}")
                    if c.page_number:
                        st.caption(f"**Page:** {c.page_number}")
                    st.write(c.chunk_text)
        else:
            st.info("No matching chunks found in the index.")
    except Exception as e:
        st.error(f"Error executing query: {e}")
