import os
import logging
from sqlalchemy.orm import Session
from backend.models.database_models import Document, AuditLog
from pathlib import Path

logger = logging.getLogger(__name__)

class DocumentService:
    @staticmethod
    def process_document(db: Session, file_path: str, filename: str, project_id: int, source_type: str):
        from rag.ingestion import DocumentIngester
        from rag.chunking import TextChunker
        from rag.embeddings import EmbeddingModel
        from rag.vector_store import VectorStore
        
        # 1. Ingest
        ingester = DocumentIngester()
        docs = ingester.ingest_file(file_path, project_id, source_type)
        
        # 2. Chunk
        chunker = TextChunker()
        chunks = []
        for d in docs:
            chunks.extend(chunker.chunk_text(d["text"], d["metadata"]))
            
        # 3. Embed and store
        embed_model = EmbeddingModel()
        vector_store = VectorStore(embed_model)
        
        texts = [c["text"] for c in chunks]
        embeddings = embed_model.embed(texts)
        vector_store.add_documents(chunks, embeddings)
        
        # 4. Save to DB
        doc = Document(
            project_id=project_id,
            filename=filename,
            file_path=file_path,
            source_type=source_type
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Log action
        log = AuditLog(project_id=project_id, action="document_upload", details=f"Uploaded {filename}")
        db.add(log)
        db.commit()
        
        return doc
        
    @staticmethod
    def index_sample_data(db: Session, project_id: int):
        sample_dir = Path("c:/TARA/Input_Data")
        if not sample_dir.exists():
            return
            
        for file_path in sample_dir.glob("*.*"):
            if file_path.suffix.lower() in [".pdf", ".txt", ".md"]:
                DocumentService.process_document(
                    db, str(file_path), file_path.name, project_id, "sample"
                )
                
    @staticmethod
    def delete_document(db: Session, doc_id: int):
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            # Need to implement ChromaDB deletion logic based on doc metadata
            # For now, just remove from DB
            db.delete(doc)
            log = AuditLog(project_id=doc.project_id, action="document_delete", details=f"Deleted {doc.filename}")
            db.add(log)
            db.commit()
