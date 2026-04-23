import hashlib
import chromadb
from chromadb.config import Settings
from rag.embeddings import embed_texts, embed_query
from config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION, TOP_K_RESULTS


def _get_collection():
    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def _make_id(chunk: dict, position: int) -> str:
    # Include source content hash + absolute position to guarantee uniqueness
    # even when file_path, name, and chunk_index are identical across chunks
    content_hash = hashlib.md5(chunk.get("source", "").encode()).hexdigest()[:8]
    key = f"{chunk.get('file_path', '')}::{chunk.get('name', '')}::{chunk.get('chunk_index', 0)}::{content_hash}::{position}"
    return hashlib.md5(key.encode()).hexdigest()


def _deduplicate(chunks: list[dict]) -> list[tuple]:
    seen_ids = set()
    unique = []
    for i, chunk in enumerate(chunks):
        cid = _make_id(chunk, i)
        if cid not in seen_ids:
            seen_ids.add(cid)
            unique.append((cid, chunk))
    return unique


def index_chunks(chunks: list[dict]) -> int:
    if not chunks:
        return 0

    collection = _get_collection()
    batch_size = 100

    deduped = _deduplicate(chunks)
    indexed = 0

    for i in range(0, len(deduped), batch_size):
        batch = deduped[i: i + batch_size]
        ids = [item[0] for item in batch]
        raw_chunks = [item[1] for item in batch]
        texts = [c["source"] for c in raw_chunks]
        embeddings = embed_texts(texts)
        metadatas = [
            {
                "name": c.get("name", ""),
                "type": c.get("type", ""),
                "file_path": c.get("file_path", ""),
                "docstring": c.get("docstring", "")[:500],
                "chunk_index": c.get("chunk_index", 0),
            }
            for c in raw_chunks
        ]
        collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        indexed += len(batch)

    return indexed


def query_similar(query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
    collection = _get_collection()
    embedding = embed_query(query)
    results = collection.query(query_embeddings=[embedding], n_results=top_k)

    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append({
            "source": doc,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return chunks


def clear_collection() -> None:
    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False),
    )
    client.delete_collection(CHROMA_COLLECTION)