import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

import streamlit as st
from frontend.components.citations import render_citations
from rag.prompts import get_qa_prompt
from frontend.init_state import ensure_session_state, render_sidebar

settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
render_sidebar()

st.title("Grounded Cybersecurity Chat Assistant")
st.markdown("Ask natural-language questions regarding the vehicle architecture, protocols, known threats, or mitigation controls. All responses are grounded in retrieved documentation.")

if llm_client.is_demo:
    st.info("ℹ️ **Active LLM Provider:** `DEMO FALLBACK MODE` (Offline Deterministic Synthesis). Configurable in `.env` to live OpenAI or Ollama endpoints.")
else:
    st.success(f"🟢 **Active LLM Provider:** `{llm_client.mode}`")

st.markdown("""
> [!NOTE]
> **Evidence Grounding Guide:**
> - **Retrieved Facts:** Technical details directly supported by expandable knowledge base citations below.
> - **Inferred / Advisory Hypotheses:** AI synthesized candidate scenarios or mitigations requiring engineering review.
""")

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "citations" in msg and msg["citations"]:
            render_citations(msg["citations"])
        if "disclaimer" in msg:
            st.caption(msg["disclaimer"])

query = st.chat_input("Ask a question about vehicle cybersecurity (e.g. 'How does Central Gateway filter IVI traffic?')...")
if query:
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
        
    with st.chat_message("assistant"):
        with st.spinner("Retrieving relevant technical documentation and synthesizing answer..."):
            try:
                citations = retriever.retrieve(query, 5, None)
                context_chunks = [c.chunk_text for c in citations]
                prompt = get_qa_prompt(query, context_chunks)
                response_text = llm_client.generate(prompt, "You are an automotive cybersecurity assistant.")
                
                st.markdown(response_text)
                if citations:
                    render_citations(citations)
                if not llm_client.is_demo and not response_text.startswith("[LIVE LLM CALL FAILED"):
                    disclaimer_text = f"🟢 **Live LLM Response** ({llm_client.mode}) | *Grounded in retrieved vehicle documentation. Verify with domain specifications.*"
                else:
                    disclaimer_text = f"🟠 **Mode:** {llm_client.mode} | *AI generated advisory output — verify with domain specifications.*"
                st.caption(disclaimer_text)
                
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_text,
                    "citations": citations,
                    "disclaimer": disclaimer_text
                })

                from backend.database.connection import log_audit_event
                sources_str = ", ".join([c.document_name for c in citations]) if citations else "None"
                log_audit_event(
                    action="rag_query",
                    user="security_engineer",
                    query=query,
                    retrieved_sources=sources_str,
                    ai_response=response_text[:500],
                    details=f"Retrieved {len(citations)} citations. Mode: {llm_client.mode}"
                )
            except Exception as e:
                st.error(f"Error generating response: {e}")
