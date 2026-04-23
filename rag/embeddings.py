"""
Local embeddings via sentence-transformers.
No API key required. Model is downloaded once and cached by HuggingFace hub.
"""

from functools import lru_cache
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _get_model()
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
    return [e.tolist() for e in embeddings]


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]