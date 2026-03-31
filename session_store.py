import uuid
from typing import Optional

from services.embedding_index import EmbeddingIndex


class SessionStore:
    """
    Holds one EmbeddingIndex per upload session.
    In a multi-worker setup you'd back this with Redis;
    for a single-process deployment this is perfectly fine.
    """

    _store: dict[str, EmbeddingIndex] = {}

    @classmethod
    def create(cls, index: EmbeddingIndex) -> str:
        session_id = str(uuid.uuid4())
        cls._store[session_id] = index
        return session_id

    @classmethod
    def get(cls, session_id: str) -> Optional[EmbeddingIndex]:
        return cls._store.get(session_id)

    @classmethod
    def delete(cls, session_id: str):
        cls._store.pop(session_id, None)
