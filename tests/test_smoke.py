"""DocFlow-Agent 后端 smoke tests。

覆盖核心流程：健康检查、文档上传与状态查询、问答记录写库、非法文件类型处理。
每个测试独立，不依赖执行顺序。
"""

from backend.database import SessionLocal
from backend.models import Document, QARecord


class TestHealth:
    def test_health_check(self, client):
        """GET /health 应该返回 200。"""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestUpload:
    def test_upload_txt_creates_document_record(self, client):
        """上传 TXT 文件后，数据库中存在对应记录。"""
        content = "测试文档内容：这是一个用于测试的文档。"
        resp = client.post("/upload", files={"file": ("test.txt", content, "text/plain")})
        assert resp.status_code == 200
        data = resp.json()

        # 上传成功响应中应包含 doc_id
        assert "doc_id" in data, f"响应缺少 doc_id: {data}"
        assert "error" not in data, f"上传返回错误: {data}"
        doc_id = data["doc_id"]

        # 通过 API 确认文档存在
        list_resp = client.get("/documents")
        assert list_resp.status_code == 200
        doc_ids = [d["doc_id"] for d in list_resp.json()["documents"]]
        assert doc_id in doc_ids

        # 直接查询数据库确认
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            assert doc is not None, f"数据库未找到 doc_id={doc_id}"
            assert doc.filename == "test.txt"
            assert doc.file_type == "txt"
        finally:
            db.close()

    def test_document_status_after_upload(self, client):
        """上传 TXT 文件后，查询状态应为 parsed，parse_method 为 text。"""
        content = "状态检查测试文档内容。"
        resp = client.post("/upload", files={"file": ("test.txt", content, "text/plain")})
        data = resp.json()
        doc_id = data["doc_id"]

        status_resp = client.get(f"/documents/{doc_id}/status")
        assert status_resp.status_code == 200
        status = status_resp.json()

        assert status["status"] == "parsed"
        assert status["parse_method"] == "text"
        assert status["char_count"] > 0


class TestAsk:
    def test_ask_writes_qa_record(self, client):
        """先上传文档，再提问，验证问答结果和 QA 记录写入数据库。"""
        # 1. 上传文档
        content = "这是用于测试问答的文档内容。包含一些关键词信息。"
        resp = client.post("/upload", files={"file": ("test.txt", content, "text/plain")})
        data = resp.json()
        doc_id = data["doc_id"]

        # 2. 提问
        ask_resp = client.post("/ask", json={"doc_id": doc_id, "question": "测试问题"})
        assert ask_resp.status_code == 200
        ask_data = ask_resp.json()

        # 验证返回中包含 question 和 answer
        assert "question" in ask_data
        assert "answer" in ask_data
        assert ask_data["question"] == "测试问题"
        assert "mock 回答" in ask_data["answer"]

        # 3. 数据库验证 QA 记录
        db = SessionLocal()
        try:
            qa = db.query(QARecord).filter(QARecord.document_id == doc_id).first()
            assert qa is not None, f"数据库未找到 QA 记录, doc_id={doc_id}"
            assert qa.question == "测试问题"
            assert "mock 回答" in qa.answer
        finally:
            db.close()


class TestErrorHandling:
    def test_invalid_file_type_returns_error(self, client):
        """上传不支持的文件类型返回结构化错误消息，而非未捕获的 traceback。"""
        content = b"some random executable bytes"
        resp = client.post(
            "/upload",
            files={"file": ("test.exe", content, "application/octet-stream")},
        )
        # 即使业务错误，路由层仍返回 200（当前设计如此）
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data, f"响应应包含 error 字段: {data}"
        assert "不支持" in data["error"], f"错误消息应明确说明不支持: {data}"
        # 确保不是未捕获的 traceback
        assert "Traceback" not in str(data)


class TestRAG:
    def test_upload_creates_vector_index(self, client):
        """上传 TXT 后，向量索引文件存在且包含 chunks 和 embeddings。"""
        content = "RAG 测试文档内容。" * 50
        resp = client.post(
            "/upload", files={"file": ("rag_test.txt", content, "text/plain")}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "doc_id" in data
        doc_id = data["doc_id"]

        from backend.vector_store import load_vectors

        vec_data = load_vectors(doc_id)
        assert vec_data is not None, f"向量索引不存在: doc_id={doc_id}"
        assert vec_data["doc_id"] == doc_id
        assert "chunks" in vec_data
        assert len(vec_data["chunks"]) > 0
        for c in vec_data["chunks"]:
            assert "chunk_id" in c
            assert "text" in c
            assert "embedding" in c
            assert len(c["embedding"]) == 256

    def test_ask_uses_rag_retrieval(self, client):
        """上传 TXT 后提问，related_chunks 非空且检索方法为 embedding。"""
        content = "这是一份关于机器学习的技术报告。" * 40
        resp = client.post(
            "/upload", files={"file": ("ml_report.txt", content, "text/plain")}
        )
        data = resp.json()
        doc_id = data["doc_id"]

        ask_resp = client.post(
            "/ask", json={"doc_id": doc_id, "question": "机器学习是什么"}
        )
        assert ask_resp.status_code == 200
        ask_data = ask_resp.json()

        assert "related_chunks" in ask_data
        assert len(ask_data["related_chunks"]) > 0
        for chunk in ask_data["related_chunks"]:
            assert "retrieval_method" in chunk
            assert chunk["retrieval_method"] in ("embedding", "fallback_keyword")

    def test_rag_fallback_when_vector_missing(self, client):
        """上传 TXT 后删除向量索引，/ask 仍返回 answer 且使用 fallback。"""
        content = "这是一份关于深度学习的文档。" * 40
        resp = client.post(
            "/upload", files={"file": ("dl_doc.txt", content, "text/plain")}
        )
        data = resp.json()
        doc_id = data["doc_id"]

        from backend.vector_store import VECTOR_INDEX_DIR

        vec_path = VECTOR_INDEX_DIR / f"{doc_id}.json"
        try:
            vec_path.unlink()
        except FileNotFoundError:
            pass

        ask_resp = client.post(
            "/ask", json={"doc_id": doc_id, "question": "深度学习是什么"}
        )
        assert ask_resp.status_code == 200
        ask_data = ask_resp.json()

        assert "answer" in ask_data
        assert "mock 回答" in ask_data["answer"]
        assert len(ask_data["related_chunks"]) > 0
        for chunk in ask_data["related_chunks"]:
            assert chunk.get("retrieval_method") == "fallback_keyword"
