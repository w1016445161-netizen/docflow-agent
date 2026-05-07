import hashlib

EMBEDDING_DIM = 256


def _text_to_ngrams(text: str, n: int = 3) -> list[str]:
    return [text[i : i + n] for i in range(len(text) - n + 1)]


def embed_texts(texts: list[str]) -> list[list[float]]:
    vectors = []
    for text in texts:
        vec = [0.0] * EMBEDDING_DIM
        ngrams = _text_to_ngrams(text)
        if not ngrams:
            vectors.append(vec)
            continue

        for ng in ngrams:
            h = int(hashlib.md5(ng.encode("utf-8", errors="ignore")).hexdigest(), 16)
            idx = h % EMBEDDING_DIM
            vec[idx] += 1.0

            h2 = int(
                hashlib.md5((ng + "\x00").encode("utf-8", errors="ignore")).hexdigest(),
                16,
            )
            idx2 = h2 % EMBEDDING_DIM
            vec[idx2] -= 0.5

        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        vectors.append(vec)
    return vectors
