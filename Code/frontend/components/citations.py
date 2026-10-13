import streamlit as st

def render_citations(citations):
    if not citations:
        st.info('No citations available.')
        return
    for i, c in enumerate(citations):
        with st.expander(f'📄 [{i+1}] {c.document_name}' + (f' — Page {c.page_number}' if c.page_number else '') + (f' — {c.section}' if c.section else '')):
            st.markdown(f'**Relevance:** {c.relevance_score:.2f}')
            st.text(c.chunk_text[:500])
