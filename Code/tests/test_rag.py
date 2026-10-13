import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings
from rag.ingestion import DocumentIngester
from rag.chunking import TextChunker
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore
from rag.retriever import Retriever
from rag.llm_client import LLMClient

def test_settings_load():
    settings = get_settings()
    assert settings.project_name == "Automotive TARA AI Assistant"
    assert settings.environment in ["development", "production", "testing"]
    assert hasattr(settings, "max_file_size_mb")
    assert settings.max_file_size_mb == 50

def test_document_ingestion(tmp_path):
    # Create sample document
    sample_file = tmp_path / "sample_ecu.md"
    sample_file.write_text("# [SYNTHETIC/SAMPLE DATA]\n\n## ECU Specifications\nThe Telematics Control Unit (TCU) manages external cellular connection.")
    
    ingester = DocumentIngester()
    docs = ingester.ingest_file(str(sample_file), project_id=1, source_type="test")
    assert len(docs) > 0
    assert docs[0]["metadata"]["document_name"] == "sample_ecu.md"

def test_text_chunker():
    chunker = TextChunker(chunk_size=200, chunk_overlap=20)
    text = "Section 1: Gateway ECU connected to CAN-FD bus. Section 2: IVI Infotainment system connected to Ethernet. Section 3: ADAS radar sensors."
    metadata = {"document_name": "test.md"}
    chunks = chunker.chunk_text(text, metadata)
    assert len(chunks) > 0
    assert "text" in chunks[0]
    assert "metadata" in chunks[0]

def test_vector_store_and_retriever(tmp_path):
    chroma_dir = str(tmp_path / "chroma_db")
    vector_store = VectorStore(persist_dir=chroma_dir, collection_name="test_collection")
    
    # Test adding documents
    chunks = [
        {"text": "The Gateway ECU routes CAN messages to Automotive Ethernet.", "metadata": {"document_name": "arch.md", "page_number": 1, "section": "Routing"}},
        {"text": "The Infotainment system handles Bluetooth and Wi-Fi.", "metadata": {"document_name": "ivi.md", "page_number": 2, "section": "Wireless"}}
    ]
    
    # Use dummy embeddings for deterministic fast testing
    embeddings = [[0.1] * 384, [0.9] * 384]
    count = vector_store.add_documents(chunks, embeddings)
    assert count == 2
    assert vector_store.get_document_count() == 2

def test_llm_client():
    settings = get_settings()
    llm = LLMClient(settings)
    assert llm.mode in ["REAL LLM", "DEMO FALLBACK"] or llm.mode.startswith("REAL LLM")
    response = llm.generate("List key ECUs in vehicle architecture", system_prompt="Answer concisely.")
    assert isinstance(response, str)
    assert len(response) > 0
