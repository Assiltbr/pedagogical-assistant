"""Multilingual embeddings (e5 needs the 'passage:' / 'query:' prefixes)."""
from functools import lru_cache
from sentence_transformers import SentenceTransformer
import config


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(config.EMBEDDING_MODEL)


def embed_passages(texts: list[str], batch_size: int = 16) -> list[list[float]]:
    model = get_model()
    return model.encode(["passage: " + t for t in texts], batch_size=batch_size,
                        normalize_embeddings=True, show_progress_bar=True).tolist()


def embed_query(text: str) -> list[float]:
    return get_model().encode("query: " + text, normalize_embeddings=True).tolist()