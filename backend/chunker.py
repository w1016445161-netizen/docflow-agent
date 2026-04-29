def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[dict]:
    """
    把长文本切成多个小片段，方便后续检索。
    chunk_size：每个片段大约多少字符
    overlap：相邻片段重叠多少字符，避免上下文断裂
    """
    text = text.strip()

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError("overlap 必须小于 chunk_size")

    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk
            })
            chunk_id += 1

        start = end - overlap

    return chunks
