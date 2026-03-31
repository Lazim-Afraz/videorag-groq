import numpy as np
import faiss

from domain.transcript import TranscriptSegment, SearchHit
from services.model_registry import ModelRegistry


class EmbeddingIndex:
    """
    Wraps a FAISS flat L2 index together with the original segments.
    One instance lives per processed video (stored in SessionStore).
    """

    def __init__(self, segments: list[TranscriptSegment]):
        embedder = ModelRegistry.get().embedder
        texts = [s.text for s in segments]
        vectors = embedder.encode(texts, batch_size=32, show_progress_bar=False)
        vectors = vectors.astype(np.float32)

        self._index = faiss.IndexFlatL2(vectors.shape[1])
        self._index.add(vectors)
        self._segments = segments

    def search(self, query: str, k: int = 5) -> list[SearchHit]:
        embedder = ModelRegistry.get().embedder
        q_vec = embedder.encode([query])[0].astype(np.float32)
        distances, indices = self._index.search(np.array([q_vec]), k=k)

        return [
            SearchHit(segment=self._segments[idx], score=float(dist))
            for idx, dist in zip(indices[0], distances[0])
            if idx < len(self._segments)
        ]
