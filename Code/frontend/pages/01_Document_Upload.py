import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

import streamlit as st
import pandas as pd
from rag.ingestion import DocumentIngester
from rag.chunking import TextChunker
from frontend.init_state import ensure_session_state, render_sidebar
from backend.database.connection import get_session_factory
from backend.models.database_models import AuditLog

# Ensure session state is initialized (eliminates 'Please start from the main app page' error)
settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
render_sidebar()

st.title("Document Upload & Knowledge Ingestion")
st.markdown("Upload automotive architecture specifications, ECU inventories, communication matrices, or threat/mitigation documents in **PDF, TXT, or MD** format.")

# Section 1: File Uploader
st.subheader("1. Select Documents to Upload")
uploaded_files = st.file_uploader(
    "Choose PDF, TXT, or MD files",
    type=["pdf", "txt", "md"],
    accept_multiple_files=True,
    help="Supported formats: .pdf (text-based), .txt, .md. Max size: 50MB per file."
)

if uploaded_files:
    st.info(f"Selected {len(uploaded_files)} file(s) for processing.")

# Button callback
if st.button("Process Uploaded Files", type="primary", use_container_width=False):
    if not uploaded_files:
        st.warning("⚠️ Please select at least one file to upload before clicking Process.")
    else:
        ingester = DocumentIngester(max_size_mb=getattr(settings, 'max_file_size_mb', 50))
        chunker = TextChunker(settings.chunk_size, settings.chunk_overlap)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        processing_summary = []
        total_chunks_added = 0
        
        for i, file in enumerate(uploaded_files):
            file_name = file.name
            file_ext = Path(file_name).suffix.lower()
            status_text.text(f"Processing ({i+1}/{len(uploaded_files)}): {file_name}...")
            
            # Read bytes safely from Streamlit UploadedFile
            file_bytes = file.getvalue()
            
            # 1. Check for empty file
            if not file_bytes or len(file_bytes) == 0:
                processing_summary.append({
                    "Filename": file_name,
                    "Type": file_ext,
                    "Extracted Chars": 0,
                    "Chunks Created": 0,
                    "Status": "Failed: Empty file (0 bytes)"
                })
                st.warning(f"⚠️ **{file_name}** is empty (0 bytes). Skipped.")
                progress_bar.progress((i + 1) / len(uploaded_files))
                continue
                
            try:
                # 2. Extract text sections via in-memory ingestion
                docs = ingester.ingest_bytes(
                    file_bytes=file_bytes,
                    filename=file_name,
                    project_id=1,
                    source_type="user_upload"
                )
                
                if not docs:
                    processing_summary.append({
                        "Filename": file_name,
                        "Type": file_ext,
                        "Extracted Chars": 0,
                        "Chunks Created": 0,
                        "Status": "Warning: No readable text extracted"
                    })
                    st.warning(f"⚠️ **{file_name}**: No readable text could be extracted. Scanned image-only PDFs without OCR or empty files cannot be parsed.")
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    continue
                
                # 3. Chunk extracted text
                file_chunks = []
                total_chars = 0
                for doc in docs:
                    text_content = doc.get("text", "")
                    total_chars += len(text_content)
                    chunks = chunker.chunk_text(text_content, doc.get("metadata", {}))
                    file_chunks.extend(chunks)
                    
                if not file_chunks:
                    processing_summary.append({
                        "Filename": file_name,
                        "Type": file_ext,
                        "Extracted Chars": total_chars,
                        "Chunks Created": 0,
                        "Status": "Warning: Text extracted but no chunks created"
                    })
                    st.warning(f"⚠️ **{file_name}**: Extracted {total_chars} characters but text chunking produced 0 chunks.")
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    continue
                
                # 4. Generate dense embeddings
                chunk_texts = [c["text"] for c in file_chunks]
                embeddings = embedding_model.embed(chunk_texts)
                
                # 5. Persist to ChromaDB vector store
                added_count = vector_store.add_documents(file_chunks, embeddings)
                total_chunks_added += added_count
                
                # 6. Record audit log entry in SQLite
                try:
                    SessionFactory = get_session_factory(settings.sqlite_db_path)
                    with SessionFactory() as session:
                        audit_entry = AuditLog(
                            action="document_upload",
                            user="engineer",
                            document_name=file_name,
                            details=f"Extracted {total_chars} chars, created {len(file_chunks)} chunks, indexed {added_count} chunks in ChromaDB."
                        )
                        session.add(audit_entry)
                        session.commit()
                except Exception as db_err:
                    # Non-fatal database logging error
                    pass
                
                processing_summary.append({
                    "Filename": file_name,
                    "Type": file_ext,
                    "Extracted Chars": total_chars,
                    "Chunks Created": len(file_chunks),
                    "Status": "Success (Indexed)"
                })
                
            except Exception as e:
                processing_summary.append({
                    "Filename": file_name,
                    "Type": file_ext,
                    "Extracted Chars": 0,
                    "Chunks Created": 0,
                    "Status": f"Error: {str(e)}"
                })
                st.error(f"❌ Error processing **{file_name}**: {e}")
                
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        status_text.empty()
        progress_bar.empty()
        
        # Display Processing Summary Report
        st.subheader("Processing Results")
        summary_df = pd.DataFrame(processing_summary)
        st.dataframe(summary_df, use_container_width=True)
        
        if total_chunks_added > 0:
            st.success(f"✅ Successfully processed and indexed **{total_chunks_added} chunks** into ChromaDB! Total indexed chunks in knowledge base: **{vector_store.get_document_count()}**")
            # Invalidate cached analysis results when knowledge base changes
            for key in ['assets', 'attack_surfaces', 'threats', 'rejected_threats', 'risks', 'mitigations', 'requirements']:
                if key in st.session_state:
                    del st.session_state[key]
        else:
            st.warning("⚠️ Processing completed, but no new chunks were added to the index.")

st.markdown("---")

# Section 2: Sample Dataset Loader
st.subheader("2. Load Built-In Synthetic Sample Data")
st.markdown("Load the 6 educational automotive architecture and threat knowledge files provided in `Input_Data/`.")

if st.button("Load Sample Data"):
    try:
        sample_dir = Path("c:/TARA/Input_Data")
        if not sample_dir.exists():
            sample_dir = Path(__file__).parent.parent.parent / "Input_Data"
            
        ingester = DocumentIngester()
        chunker = TextChunker(settings.chunk_size, settings.chunk_overlap)
        
        with st.spinner("Ingesting synthetic automotive knowledge base..."):
            extracted_sections = ingester.ingest_directory(str(sample_dir), project_id=1, source_type="sample_data")
            
            all_chunks = []
            for sec in extracted_sections:
                chunks = chunker.chunk_text(sec["text"], sec["metadata"])
                all_chunks.extend(chunks)
                
            texts = [c["text"] for c in all_chunks]
            embeddings = embedding_model.embed(texts)
            added_count = vector_store.add_documents(all_chunks, embeddings)
            
        st.success(f"✅ Sample knowledge base loaded: **{len(extracted_sections)} sections** chunked into **{len(all_chunks)} vector chunks** and indexed! Total collection count: **{vector_store.get_document_count()}**.")
        # Invalidate cached analysis results when knowledge base changes
        for key in ['assets', 'attack_surfaces', 'threats', 'rejected_threats', 'risks', 'mitigations', 'requirements']:
            if key in st.session_state:
                del st.session_state[key]
    except Exception as e:
        st.error(f"❌ Error loading sample data: {e}")

st.markdown("---")

# Section 3: Verification & Retrieval Check
st.subheader("3. Verify Retrieval from Knowledge Base")
st.markdown("Test whether newly uploaded or existing documents are searchable:")

verify_query = st.text_input("Enter a query to verify retrieval (e.g. 'CAN bus gateway', 'OTA update', or a term from your uploaded file):", key="verify_doc_query")
if verify_query:
    try:
        results = retriever.retrieve(verify_query, top_k=3)
        if results:
            st.write(f"Found **{len(results)} relevant chunks** in the index:")
            for idx, c in enumerate(results, 1):
                with st.expander(f"[{idx}] {c.document_name} (Relevance: {c.relevance_score:.3f})"):
                    if c.section:
                        st.caption(f"**Section:** {c.section}")
                    if c.page_number:
                        st.caption(f"**Page:** {c.page_number}")
                    st.text(c.chunk_text[:500] + ("..." if len(c.chunk_text) > 500 else ""))
        else:
            st.info("No matching chunks retrieved for this query.")
    except Exception as e:
        st.error(f"Error during retrieval: {e}")

st.markdown("---")
st.subheader("4. Next Steps & Workflow Navigation")
col_n1, col_n2, col_n3 = st.columns(3)
with col_n1:
    st.page_link("streamlit_app.py", label="Home Dashboard", icon="🏠")
with col_n2:
    st.page_link("pages/02_Knowledge_Base.py", label="02. Knowledge Base", icon="📚")
with col_n3:
    st.page_link("pages/04_Asset_Analysis.py", label="04. Asset Analysis", icon="🔍")
