import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TextChunker:
    def __init__(self, chunk_size=512, chunk_overlap=64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text, metadata) -> list[dict]:
        if not text:
            return []
            
        # Recursive splitting logic
        chunks = []
        # Fallback to simple chunking for now
        words = text.split()
        current_chunk = []
        current_length = 0
        chunk_idx = 0
        
        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1
            if current_length >= self.chunk_size:
                chunk_text = " ".join(current_chunk)
                if len(chunk_text) >= 50:
                    meta = metadata.copy()
                    meta['chunk_index'] = chunk_idx
                    chunks.append({
                        "text": chunk_text,
                        "metadata": meta
                    })
                    chunk_idx += 1
                # overlap
                overlap_words = current_chunk[-self.chunk_overlap:] if self.chunk_overlap < len(current_chunk) else []
                current_chunk = overlap_words
                current_length = sum(len(w)+1 for w in current_chunk)
                
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text) >= 50:
                meta = metadata.copy()
                meta['chunk_index'] = chunk_idx
                chunks.append({
                    "text": chunk_text,
                    "metadata": meta
                })

        # Fallback: if document has valid non-empty text but all pieces were < 50 chars, preserve as single chunk
        if not chunks and text.strip():
            meta = metadata.copy()
            meta['chunk_index'] = 0
            chunks.append({
                "text": text.strip(),
                "metadata": meta
            })
                
        return chunks
