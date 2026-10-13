import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from backend.models.schemas import Citation
except ImportError:
    # Dummy class if schemas doesn't exist yet
    from dataclasses import dataclass
    @dataclass
    class Citation:
        document_name: str
        page_number: int
        section: str
        chunk_text: str
        relevance_score: float

from .vector_store import VectorStore
from .embeddings import EmbeddingModel

class Retriever:
    def __init__(self, vector_store: VectorStore, embedding_model: EmbeddingModel, top_k=5):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.top_k = top_k

    def retrieve(self, query: str, top_k=None, filter_metadata=None) -> list[Citation]:
        try:
            k = top_k or self.top_k
            where_filter = filter_metadata if (filter_metadata and isinstance(filter_metadata, dict) and len(filter_metadata) > 0) else None
            query_emb = self.embedding_model.embed_query(query)
            results = self.vector_store.query(query_emb, top_k=k, filter_metadata=where_filter)
            
            citations = []
            seen = set()
            for res in results:
                meta = res.get('metadata', {})
                distance = res.get('distance', 0.0)
                relevance = max(0.0, 1.0 - distance)
                doc_name = meta.get('document_name', 'Unknown')
                text = res.get('text', '')
                
                # Deduplicate identical chunks
                chunk_sig = f"{doc_name}_{text[:50]}"
                if chunk_sig in seen:
                    continue
                seen.add(chunk_sig)
                
                citations.append(Citation(
                    document_name=doc_name,
                    page_number=meta.get('page_number', 0),
                    section=meta.get('section', ''),
                    chunk_text=text,
                    relevance_score=relevance
                ))
                
            citations.sort(key=lambda x: x.relevance_score, reverse=True)
            return citations
        except Exception as e:
            return []
