import pytest
import tempfile
import os
from pathlib import Path
import streamlit as st

from config import get_settings
from rag.ingestion import DocumentIngester
from rag.chunking import TextChunker
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore
from rag.retriever import Retriever
from frontend.init_state import ensure_session_state, get_shared_resources

def test_ensure_session_state_initialization():
    """Verify that ensure_session_state auto-initializes all resources without crashing."""
    # Clear session state if present
    st.session_state.clear()
    
    settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
    assert settings is not None
    assert embedding_model is not None
    assert vector_store is not None
    assert retriever is not None
    assert llm_client is not None
    assert 'settings' in st.session_state
    assert 'vector_store' in st.session_state

def test_navigation_pages_exist_and_use_session_guard():
    """Verify that all 12 multi-page app files exist and do not block with unhandled stops."""
    frontend_dir = Path(__file__).parent.parent / "frontend"
    pages_dir = frontend_dir / "pages"
    
    expected_pages = [
        "01_Document_Upload.py",
        "02_Knowledge_Base.py",
        "03_Architecture_Analysis.py",
        "04_Asset_Analysis.py",
        "05_Attack_Surface.py",
        "06_Threat_Analysis.py",
        "07_Risk_Assessment.py",
        "08_Mitigations.py",
        "09_TARA_Report.py",
        "10_RAG_Assistant.py",
        "11_Evaluation.py",
        "12_Audit_Review.py"
    ]
    
    for page_name in expected_pages:
        page_path = pages_dir / page_name
        assert page_path.exists(), f"Page {page_name} does not exist!"
        content = page_path.read_text(encoding="utf-8")
        # Ensure the legacy blocking error is removed and ensure_session_state is used
        assert 'st.error("Please start from the main app page.")' not in content, f"Page {page_name} still contains blocking check!"
        assert "ensure_session_state" in content, f"Page {page_name} does not call ensure_session_state!"

def test_successful_document_processing_pdf():
    """Verify that PDF bytes are extracted with original filename and chunked cleanly."""
    ingester = DocumentIngester()
    chunker = TextChunker(chunk_size=512, chunk_overlap=64)
    
    # Read technical report PDF as sample
    pdf_path = Path(__file__).parent.parent / "Documentation" / "technical_report.pdf"
    assert pdf_path.exists()
    pdf_bytes = pdf_path.read_bytes()
    
    docs = ingester.ingest_bytes(pdf_bytes, filename="my_test_spec.pdf", project_id=1)
    assert len(docs) > 0
    assert docs[0]["metadata"]["document_name"] == "my_test_spec.pdf"
    assert docs[0]["metadata"]["document_type"] == "pdf"
    
    chunks = []
    for doc in docs:
        chunks.extend(chunker.chunk_text(doc["text"], doc["metadata"]))
    assert len(chunks) > 0
    assert chunks[0]["metadata"]["document_name"] == "my_test_spec.pdf"

def test_successful_document_processing_txt_and_md():
    """Verify that TXT and MD bytes are ingested with section metadata."""
    ingester = DocumentIngester()
    
    # TXT
    txt_bytes = b"Automotive ECU Gateway specification.\nBuses include CAN-FD and Automotive Ethernet."
    txt_docs = ingester.ingest_bytes(txt_bytes, filename="gateway_spec.txt")
    assert len(txt_docs) == 1
    assert "CAN-FD" in txt_docs[0]["text"]
    assert txt_docs[0]["metadata"]["document_name"] == "gateway_spec.txt"
    
    # MD
    md_bytes = b"# Section 1: ADAS ECU\nADAS processes camera and radar data.\n\n# Section 2: Powertrain\nControls throttle."
    md_docs = ingester.ingest_bytes(md_bytes, filename="architecture.md")
    assert len(md_docs) == 2
    assert md_docs[0]["metadata"]["section"] == "Section 1: ADAS ECU"
    assert md_docs[1]["metadata"]["section"] == "Section 2: Powertrain"

def test_empty_or_unreadable_document_handling():
    """Verify that empty files (0 bytes) and unreadable/unsupported files return empty lists safely."""
    ingester = DocumentIngester()
    
    # Empty file
    assert ingester.ingest_bytes(b"", "empty.pdf") == []
    assert ingester.ingest_bytes(b"", "empty.txt") == []
    
    # Whitespace only
    assert ingester.ingest_bytes(b"   \n\t  ", "blank.txt") == []
    assert ingester.ingest_bytes(b"   \n\t  ", "blank.md") == []
    
    # Unsupported file type
    assert ingester.ingest_bytes(b"MZBINARYDATA", "malware.exe") == []
    assert ingester.ingest_bytes(b"BINARYDATA", "firmware.bin") == []

def test_pdf_file_handle_released_on_windows():
    """Verify that file-based PDF ingestion releases file locks immediately on Windows."""
    ingester = DocumentIngester()
    pdf_path = Path(__file__).parent.parent / "Documentation" / "technical_report.pdf"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tf:
        tf.write(pdf_path.read_bytes())
        temp_name = tf.name
        
    try:
        docs = ingester.ingest_file(temp_name, original_filename="temp_test.pdf")
        assert len(docs) > 0
        # Immediately remove file - should not raise PermissionError: [WinError 32]
        os.remove(temp_name)
        assert not os.path.exists(temp_name)
    except PermissionError:
        pytest.fail("Windows file lock was not released by PyMuPDF!")
    finally:
        if os.path.exists(temp_name):
            try:
                os.remove(temp_name)
            except Exception:
                pass

def test_short_text_chunking_fallback():
    """Verify that short text (< 50 chars) is preserved rather than dropped."""
    chunker = TextChunker(chunk_size=512, chunk_overlap=64)
    short_text = "ECU Gateway FW 1.0"
    meta = {"document_name": "short.txt"}
    
    chunks = chunker.chunk_text(short_text, meta)
    assert len(chunks) == 1
    assert chunks[0]["text"] == short_text
    assert chunks[0]["metadata"]["chunk_index"] == 0

def test_retrieval_of_newly_indexed_content():
    """End-to-end verification: Ingest unique content -> Chunk -> Embed -> Index -> Retrieve."""
    settings = get_settings()
    embedding_model = EmbeddingModel(settings.embedding_model)
    vector_store = VectorStore(settings.chroma_persist_dir)
    retriever = Retriever(vector_store, embedding_model, top_k=3)
    
    ingester = DocumentIngester()
    chunker = TextChunker(settings.chunk_size, settings.chunk_overlap)
    
    unique_keyword = "UNIQUE_VEHICLE_CAN_FIREWALL_SECRET_XYZ987"
    content = f"# Automotive Firewall Rules\nThe {unique_keyword} blocks unauthorized DoIP packets from IVI domain."
    filename = "custom_firewall_rules.md"
    
    docs = ingester.ingest_bytes(content.encode("utf-8"), filename=filename)
    assert len(docs) > 0
    
    chunks = []
    for doc in docs:
        chunks.extend(chunker.chunk_text(doc["text"], doc["metadata"]))
    assert len(chunks) > 0
    
    texts = [c["text"] for c in chunks]
    embeddings = embedding_model.embed(texts)
    added = vector_store.add_documents(chunks, embeddings)
    assert added > 0
    
    # Retrieve using the unique keyword
    citations = retriever.retrieve(unique_keyword, top_k=3)
    assert len(citations) > 0
    # Top citation should match our newly indexed document and keyword
    matching_citations = [c for c in citations if unique_keyword in c.chunk_text]
    assert len(matching_citations) > 0
    assert matching_citations[0].document_name == filename

def test_pdf_upload_processing_and_cgw_verification():
    """Verify PDF upload, extraction, chunking, ChromaDB indexing, and retrieval with UPLOAD-VERIFY-KEY: CGW-ORANGE-7429."""
    import fitz
    
    settings = get_settings()
    assert hasattr(settings, "max_file_size_mb"), "settings must have max_file_size_mb attribute"
    assert settings.max_file_size_mb == 50
    
    # 1. Create in-memory test PDF
    pdf_doc = fitz.open()
    page = pdf_doc.new_page()
    test_key = "UPLOAD-VERIFY-KEY: CGW-ORANGE-7429"
    content_text = f"Central Gateway Interface Specification\n\n{test_key}\n\nFirewall rules and routing policies for CAN and Automotive Ethernet."
    page.insert_text((50, 72), content_text)
    pdf_bytes = pdf_doc.tobytes()
    pdf_doc.close()
    
    # 2. Ingest with settings.max_file_size_mb
    ingester = DocumentIngester(max_size_mb=settings.max_file_size_mb)
    filename = "cgw_orange_verification.pdf"
    docs = ingester.ingest_bytes(pdf_bytes, filename=filename, project_id=1, source_type="user_upload")
    assert len(docs) > 0, "PDF ingestion must extract text"
    assert test_key in docs[0]["text"]
    assert docs[0]["metadata"]["document_name"] == filename
    
    # 3. Chunk text
    chunker = TextChunker(settings.chunk_size, settings.chunk_overlap)
    chunks = chunker.chunk_text(docs[0]["text"], docs[0]["metadata"])
    assert len(chunks) > 0, "Chunking must produce at least one chunk"
    
    # 4. Embed and index in ChromaDB
    embedding_model = EmbeddingModel(settings.embedding_model)
    vector_store = VectorStore(settings.chroma_persist_dir)
    embeddings = embedding_model.embed([c["text"] for c in chunks])
    added_count = vector_store.add_documents(chunks, embeddings)
    assert added_count > 0, "Must add documents to ChromaDB"
    
    # 5. Retrieve using exact test key
    retriever = Retriever(vector_store, embedding_model, top_k=5)
    citations = retriever.retrieve("CGW-ORANGE-7429", top_k=5)
    assert len(citations) > 0, "Must retrieve citations for CGW-ORANGE-7429"
    
    matched = [c for c in citations if "CGW-ORANGE-7429" in c.chunk_text]
    assert len(matched) > 0, "Retrieved chunk must contain test key CGW-ORANGE-7429"
    assert matched[0].document_name == filename, f"Document name must match {filename}"
