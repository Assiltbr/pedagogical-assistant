"""Chroma wrapper: index chunks, search by similarity, filter by document."""
import chromadb
import config
from src.embeddings import embed_passages, embed_query


def get_collection():
    client = chromadb.PersistentClient(path=config.CHROMA_DIR)
    return client.get_or_create_collection("courses", metadata={"hnsw:space": "cosine"})


def add_chunks(chunks: list[dict]) -> int:
    """Index chunks that aren't already stored. Returns the number added."""
    col = get_collection()
    existing = set(col.get(ids=[c["id"] for c in chunks])["ids"])
    new = [c for c in chunks if c["id"] not in existing]
    if not new:
        return 0
    col.add(ids=[c["id"] for c in new],
            documents=[c["text"] for c in new],
            embeddings=embed_passages([c["text"] for c in new]),
            metadatas=[c["meta"] for c in new])
    return len(new)


def search(query: str, k: int = config.TOP_K, doc: str | None = None) -> list[dict]:
    col = get_collection()
    res = col.query(query_embeddings=[embed_query(query)], n_results=k,
                    where={"doc": doc} if doc else None)
    return [{"id": res["ids"][0][i],
             "text": res["documents"][0][i],
             "meta": res["metadatas"][0][i],
             "score": 1 - res["distances"][0][i]}   # cosine distance -> similarity
            for i in range(len(res["ids"][0]))]


def delete_doc(doc: str) -> None:
    get_collection().delete(where={"doc": doc})