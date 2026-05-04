import re


def tokenize(text: str) -> set[str]:
    """
    简单检索用的分词函数。
    英文和数字按单词切分，中文按相邻两个字组成 bigram。
    """
    text = text.lower()

    english_tokens = re.findall(r"[a-zA-Z0-9_]+", text)

    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    chinese_bigrams = [
        chinese_chars[i] + chinese_chars[i + 1] for i in range(len(chinese_chars) - 1)
    ]

    return set(english_tokens + chinese_bigrams)


def retrieve_chunks(question: str, chunks: list[dict], top_k: int = 4) -> list[dict]:
    """
    根据用户问题，从文档片段中找出最相关的 top_k 个片段。
    第一版使用简单关键词重合度检索。
    """
    if not chunks:
        return []

    question_tokens = tokenize(question)
    scored_chunks = []

    for chunk in chunks:
        chunk_tokens = tokenize(chunk["text"])
        score = len(question_tokens & chunk_tokens)

        scored_chunks.append({**chunk, "score": score})

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)

    top_chunks = scored_chunks[:top_k]

    # 如果完全没有关键词命中，就默认返回文档开头几个片段，适合“总结全文”类问题
    if all(item["score"] == 0 for item in top_chunks):
        return [{**chunk, "score": 0} for chunk in chunks[:top_k]]

    return top_chunks
