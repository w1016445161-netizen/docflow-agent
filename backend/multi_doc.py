import json
from pathlib import Path


INDEX_DIR = Path("storage/index")


def load_doc_index(doc_id: str) -> dict:
    index_path = INDEX_DIR / f"{doc_id}.json"

    if not index_path.exists():
        raise FileNotFoundError(f"找不到文档索引：{doc_id}")

    return json.loads(index_path.read_text(encoding="utf-8"))


def build_multi_doc_context(doc_ids: list[str], max_chunks_per_doc: int = 3) -> list[dict]:
    """
    从多个文档中抽取前几个片段，构造对比上下文。
    """
    contexts = []

    for doc_id in doc_ids:
        index_data = load_doc_index(doc_id)

        filename = index_data["filename"]
        chunks = index_data["chunks"][:max_chunks_per_doc]

        for chunk in chunks:
            contexts.append({
                "doc_id": doc_id,
                "filename": filename,
                "chunk_id": chunk["chunk_id"],
                "text": f"【文档：{filename}】\n{chunk['text']}"
            })

    return contexts


def list_documents() -> list[dict]:
    """
    列出已经上传并建立索引的文档。
    """
    documents = []

    for index_path in INDEX_DIR.glob("*.json"):
        data = json.loads(index_path.read_text(encoding="utf-8"))

        documents.append({
            "doc_id": data["doc_id"],
            "filename": data["filename"],
            "total_chars": data["total_chars"],
            "total_chunks": data["total_chunks"]
        })

    return documents