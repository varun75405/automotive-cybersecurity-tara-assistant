import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import streamlit as st
from config import get_settings
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore
from rag.retriever import Retriever
from rag.llm_client import LLMClient
from backend.database.connection import init_db

@st.cache_resource
def get_shared_resources():
    """Load and cache singleton resources across the Streamlit session."""
    settings = get_settings()
    settings.ensure_directories()
    init_db()
    embedding_model = EmbeddingModel(settings.embedding_model)
    vector_store = VectorStore(settings.chroma_persist_dir)
    retriever = Retriever(vector_store, embedding_model, settings.retrieval_top_k)
    llm_client = LLMClient(settings)
    return settings, embedding_model, vector_store, retriever, llm_client

def ensure_session_state():
    """
    Ensure all core resources and session variables are initialized.
    Eliminates the 'Please start from the main app page' error by auto-initializing
    resources on any page load, refresh, or direct hyperlink navigation.
    """
    if ('settings' not in st.session_state or 
        'vector_store' not in st.session_state or 
        'retriever' not in st.session_state or 
        'embedding_model' not in st.session_state or 
        'llm_client' not in st.session_state):
        settings, embedding_model, vector_store, retriever, llm_client = get_shared_resources()
        st.session_state.settings = settings
        st.session_state.embedding_model = embedding_model
        st.session_state.vector_store = vector_store
        st.session_state.retriever = retriever
        st.session_state.llm_client = llm_client

    return (
        st.session_state.settings,
        st.session_state.embedding_model,
        st.session_state.vector_store,
        st.session_state.retriever,
        st.session_state.llm_client
    )

def render_sidebar():
    """Render consistent sidebar with system status across all pages."""
    ensure_session_state()
    llm_client = st.session_state.llm_client
    is_live = llm_client.mode.startswith("REAL LLM") and not getattr(llm_client, "is_fallback_active", False)
    mode_color = "#28a745" if is_live else "#fd7e14"
    st.sidebar.markdown("### System Status")
    st.sidebar.markdown(f"**LLM Mode:** <span style='color:{mode_color}; font-weight:bold;'>{llm_client.mode}</span>", unsafe_allow_html=True)
    if not is_live:
        reason = getattr(llm_client, "last_fallback_reason", "")
        reason_txt = f" ({reason})" if reason else ""
        st.sidebar.warning(f"⚠️ **DEMO MODE — PREDEFINED DATA**{reason_txt}")
    if 'vector_store' in st.session_state and st.session_state.vector_store:
        st.sidebar.markdown(f"**Indexed Chunks:** {st.session_state.vector_store.get_document_count()}")
    st.sidebar.markdown("---")
