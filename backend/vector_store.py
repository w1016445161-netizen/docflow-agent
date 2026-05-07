import json
import logging
from pathlib import Path

from backend.core.logging import log_event

_logger = logging.getLogger(__name__)

VECTOR_INDEX_DIR = Path("storage/vector_index")
VECTOR_INDEX_DIR.mkdir(parents=True, exist_ok=True)


def save_vectors(doc_id: str, chunks: list[dict], embeddings: list[list[float]]) -> None:
    data = {
        "doc_id": doc_id,
        "chunks": [
            {
                "chunk_id": c["chunk_id"],
                "text": c["text"],
                "embedding": e,
            }
            for c, e in zip(chunks, embeddings)
        ],
    }
    path = VECTOR_INDEX_DIR / f"{doc_id}.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def load_vectors(doc_id: str) -> dict | None:
    path = VECTOR_INDEX_DIR / f"{doc_id}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search_vectors(
    doc_id: str, query_embedding: list[float], top_k: int = 4
) -> list[dict]:
    data = load_vectors(doc_id)
    if not data:
        return []
    chunks = data.get("chunks", [])
    scored = []
    for c in chunks:
        emb = c.get("embedding")
        if emb is None:
            continue
        score = _cosine_similarity(query_embedding, emb)
        scored.append(
            {"chunk_id": c["chunk_id"], "text": c["text"], "score": score}
        )
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
