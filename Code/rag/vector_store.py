import sys
import hashlib
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, persist_dir, collection_name='tara_documents'):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
        except Exception as e:
            logger.warning(f"ChromaDB persistent client unavailable, using in-memory store fallback: {e}")
            self.client = None
            self.collection = None
            self._memory_store = []

    def add_documents(self, chunks: list[dict], embeddings: list[list[float]]) -> int:
        if not chunks:
            return 0
            
        ids = []
        texts = []
        metadatas = []
        
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            meta = chunk.get('metadata', {})
            doc_name = str(meta.get('document_name', 'unknown'))
            chunk_idx = str(meta.get('chunk_index', i))
            txt = chunk.get('text', '')
            txt_hash = hashlib.md5(txt.encode('utf-8')).hexdigest()[:8]
            
            chunk_id = hashlib.sha256(f"{doc_name}_{chunk_idx}_{i}_{txt_hash}".encode('utf-8')).hexdigest()
            ids.append(chunk_id)
            texts.append(txt)
            
            clean_meta = {}
            for k, v in meta.items():
                if v is not None:
                    clean_meta[k] = str(v) if not isinstance(v, (int, float, bool, str)) else v
            metadatas.append(clean_meta)
            
        if self.collection:
            try:
                self.collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas
                )
                return len(ids)
            except Exception as e:
                logger.error(f"Failed to upsert documents to ChromaDB: {e}")
                return 0
        else:
            if not hasattr(self, '_memory_store'):
                self._memory_store = []
            for cid, txt, meta, emb in zip(ids, texts, metadatas, embeddings):
                self._memory_store.append({
                    'id': cid,
                    'text': txt,
                    'metadata': meta,
                    'embedding': emb
                })
            return len(ids)

    def query(self, query_embedding: list[float], top_k=5, filter_metadata=None) -> list[dict]:
        if self.collection:
            try:
                # ChromaDB raises error if where={} is passed; it requires where=None when empty
                where_filter = filter_metadata if (filter_metadata and isinstance(filter_metadata, dict) and len(filter_metadata) > 0) else None
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_filter
                )
                
                output = []
                if results and results.get('documents') and results['documents'][0]:
                    for i in range(len(results['documents'][0])):
                        output.append({
                            'text': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'distance': results['distances'][0][i] if results.get('distances') else 0.0
                        })
                return output
            except Exception as e:
                logger.error(f"Failed to query ChromaDB: {e}")
                return []
        else:
            if not hasattr(self, '_memory_store') or not self._memory_store:
                return []
            
            # Simple in-memory distance calculation (L2 distance or 1 - dot product)
            scored = []
            for item in self._memory_store:
                if filter_metadata:
                    match = all(item['metadata'].get(k) == v for k, v in filter_metadata.items())
                    if not match:
                        continue
                emb = item['embedding']
                dist = sum((a - b)**2 for a, b in zip(query_embedding, emb))**0.5 if emb else 0.0
                scored.append({
                    'text': item['text'],
                    'metadata': item['metadata'],
                    'distance': float(dist)
                })
            scored.sort(key=lambda x: x['distance'])
            return scored[:top_k]

    def delete_collection(self) -> None:
        if self.client:
            try:
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.get_or_create_collection(name=self.collection_name)
            except Exception as e:
                logger.error(f"Failed to delete collection: {e}")
        else:
            self._memory_store = []

    def get_document_count(self) -> int:
        if self.collection:
            try:
                return self.collection.count()
            except Exception:
                pass
        return len(getattr(self, '_memory_store', []))

    def get_collection_stats(self) -> dict:
        return {
            "count": self.get_document_count(),
            "name": self.collection_name
        }
