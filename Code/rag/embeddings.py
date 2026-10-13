import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

class EmbeddingModel:
    def __init__(self, model_name='BAAI/bge-small-en-v1.5'):
        self.model_name = model_name
        self._model = None
        self._use_fallback = False

    @property
    def model(self):
        if self._model is None and not self._use_fallback:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                try:
                    self._model = SentenceTransformer(self.model_name, local_files_only=True)
                except Exception:
                    self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.warning(f"SentenceTransformers unavailable ({e}). Using deterministic hash-embedding fallback.")
                self._use_fallback = True
        return self._model

    def _fallback_embed_text(self, text: str, dim: int = 384) -> list[float]:
        """Generate a normalized 384-dim pseudo-embedding based on word hashes."""
        import hashlib
        vec = [0.0] * dim
        words = text.lower().split()
        if not words:
            return vec
        for word in words:
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % dim
            val = (h % 100) / 100.0
            vec[idx] += val
        norm = sum(x*x for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.model is not None:
            try:
                embeddings = self.model.encode(texts)
                return embeddings.tolist()
            except Exception as e:
                logger.warning(f"SentenceTransformer encode failed ({e}), using fallback.")
        return [self._fallback_embed_text(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        if self.model is not None:
            try:
                return self.model.encode(text).tolist()
            except Exception as e:
                logger.warning(f"SentenceTransformer encode query failed ({e}), using fallback.")
        return self._fallback_embed_text(text)
