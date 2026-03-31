import os
import whisper
from sentence_transformers import SentenceTransformer


class ModelRegistry:
    """
    Singleton that owns all ML models for the process lifetime.
    Nothing outside this class should call whisper.load_model or
    SentenceTransformer() directly.
    """

    _instance: "ModelRegistry | None" = None

    def __init__(self):
        self._whisper = None
        self._embedder = None

    @classmethod
    def get(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_all(self):
        whisper_size = os.getenv("WHISPER_MODEL", "base")
        self._whisper = whisper.load_model(whisper_size)
        self._embedder = SentenceTransformer("sentence-transformers/LaBSE")

    def release(self):
        self._whisper = None
        self._embedder = None

    @property
    def whisper(self):
        if self._whisper is None:
            raise RuntimeError("Models not loaded. Call load_all() first.")
        return self._whisper

    @property
    def embedder(self):
        if self._embedder is None:
            raise RuntimeError("Models not loaded. Call load_all() first.")
        return self._embedder
